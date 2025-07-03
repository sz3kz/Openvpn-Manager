#!/usr/bin/env python3
'''
OpenVPN management daemon for ease of handling of simple openvpn connections.
'''

import os
import sys
import shutil
import subprocess
import logging
import stat

from termcolor import colored

ROOT_PIPE_DIR="/var/run"
INPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-server.pipe"
OUTPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-client.pipe"

ROOT_MNGR_DIR="/root/.openvpn-management"
VPN_DIR=f"{ROOT_MNGR_DIR}/vpns"
VPN_LINK=f"{ROOT_MNGR_DIR}/current"
LOG_FILE=f"{ROOT_MNGR_DIR}/log.txt"



def failure(message):
    '''
    Returns red color text.

    Args:
        message (str): message to be colored

    Returns:
        (str): colored message
    '''
    return colored(f'{message}','red')

def success(message):
    '''
    Returns green color text.

    Args:
        message (str): message to be colored

    Returns:
        (str): colored message
    '''
    return colored(f'{message}', 'green')

def inform(message):
    '''
    Returns yellow color text.

    Args:
        message (str): message to be colored

    Returns:
        (str): colored message
    '''
    return colored(f'{message}', 'yellow')

def respond(message):
    '''
    Writes message to the pipe the client is reading from.

    Args:
        message (str): message to write to pipe

    Returns:
        None
    '''
    with open(f"{OUTPUT_PIPE}", 'w') as output_pipe:
        output_pipe.write(f"{message}")
    logger.info(inform(f"    > \'{message}\'"))

def receive():
    '''
    Reads message from the pipe the client is writing to.

    Args:
        message (str): message to write to pipe

    Returns:
        None
    '''
    with open(f"{INPUT_PIPE}", 'r') as input_pipe:
        response = input_pipe.read().strip()
    logger.info(inform(f"    < \'{response}\'"))
    return response

def setup_pipes():
    '''
    Ensures the pipes are correctly set up. Checks if pipes exist and if they do, 
    deletes them (to be deterministic). Then creates the pipes with appropriate
    permissions.

    Args:
        None

    Returns:
        None
    '''
    for pipe in [INPUT_PIPE, OUTPUT_PIPE]:
        if os.path.exists(f"{pipe}"):
            logger.info(inform(f"Pipe already exists: \'{pipe}\'."))
            os.remove(f"{pipe}")
            logger.info(inform(f"Pipe deleted: \'{pipe}\'."))
        os.mkfifo(f"{pipe}")
        logger.info(inform(f"Pipe created: \'{pipe}\'."))
    os.chmod(INPUT_PIPE, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IWOTH)
    logger.info(inform(f"Pipe permissions modified: \'{INPUT_PIPE}\'"))
    os.chmod(OUTPUT_PIPE, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
    logger.info(inform(f"Pipe permissions modified: \'{OUTPUT_PIPE}\'"))
    logger.info(success("Pipes set up."))

def check_root_privileges():
    '''
    Checks if daemon is ran with appropriate (root!) privileges. Exits if not root.

    Args:
        None

    Returns:
        None
    '''
    if os.geteuid() != 0:
        logger.error(failure(f"Insufficient privileges: \'{os.geteuid()}\'."))
        logger.error(failure(f"{sys.argv[0]} must be ran with root privileges."))
        sys.exit(1)
    logger.info(success(f"Sufficient privileges: \'{os.geteuid()}\'."))


def terminate():
    '''
    Handles the 'TERMINATE' command. Kills active openvpn process. Deletes
    the pipes.

    Args:
        None

    Returns:
        None

    Responses:
        'TERMINATED': terminated successfully
    '''
    logger.info(inform("#### Client requested termination of daemon."))
    if connection_active:
        process.kill()
        logger.info(inform("Killed still active openvpn connection."))
    for pipe in [INPUT_PIPE, OUTPUT_PIPE]:
        os.remove(f"{pipe}")
        logger.info(inform(f"Removed pipe: \'{pipe}\'."))
    logger.info(inform("Daemon terminated."))
    sys.exit(0)

def status():
    '''
    Handles the 'STATUS' command. Determines whether the openvpn process is active.

    Args:
        None

    Returns:
        None

    Responses:
        'CONNECTED' : process is running
        'DISCONNECTED' : process is not running / was killed 
    '''
    logger.info(inform("#### Client queried status of connection."))
    if connection_active:
        logger.info(inform("Connection is active."))
        respond("CONNECTED")
    else:
        logger.info(inform("Connection is not active."))
        respond("DISCONNECTED")
    logger.info(success("Status query answered."))

def available():
    '''
    Handles the 'AVAILABLE' command. Sends the count of files inside the VPN_DIR 
    directory. Transmits every file name one-by-one, waiting for 'CONTINUE' responses.

    Args:
        None

    Returns:
        None

    Responses:
        [count of files]
        [name of file]
    '''
    logger.info(inform("#### Client requested a listing of available vpn files."))
    files = os.listdir(f"{VPN_DIR}")
    logger.info(inform(f"Files available: {len(files)}."))
    respond(f"{len(files)}")
    logger.info(inform("Listing files:"))
    for file in files:
        logger.info(inform(f" - \'{file}\'"))
        response = receive()
        if not response == "CONTINUE":
            return
        respond(f"{file}")
    logger.info(success("Listing done."))

def upload():
    '''
    Handles the 'UPLOAD' command. Queries user for path of file and it's preferred
    basename via 'PATH?' and 'NEWNAME?'. Copies path to VPN_DIR with new basename.

    Args:
        None

    Returns:
        None

    Responses:
        'PATH?': query for path of vpn file
        'NEWNAME?': query for preferred basename of vpn file
        'SUCCESS': upload was successful

    Errors:
        'ERROR:INVALIDFILE': given path does not exist
        'ERROR:NOTAFILE': given path does not point to a file
        'ERROR:FILEEXISTS: given preferred basename already exists in VPN_DIR
    '''
    logger.info(inform("#### Client requested a vpn file upload."))
    respond("PATH?")
    src_path = receive()
    if not os.path.exists(src_path):
        logger.error(failure(f"Non-existant source file denoted: \'{src_path}\'."))
        respond("ERROR:INVALIDFILE")
        return
    if not os.path.isfile(src_path):
        logger.error(failure(f"Non-file path denoted: \'{src_path}\'"))
        respond("ERROR:NOTAFILE")
        return
    logger.info(inform(f"Source file : \'{src_path}\'"))
    respond("NEWNAME?")
    dst_path_user = receive()
    dst_name = os.path.basename(dst_path_user)
    dst_path = f"{VPN_DIR}/{dst_name}"
    if os.path.exists(f"{dst_path}"):
        logger.info(failure(f"Already existant vpn file denoted: \'{dst_path}\'."))
        respond("ERROR:FILEEXISTS")
        return
    logger.info(inform(f"Target file : \'{dst_path}\'."))
    shutil.copy(f"{src_path}",f"{dst_path}")
    logger.info(success("Copied source file to target file."))
    respond("SUCCESS")

def delete():
    '''
    Handles the DELETE command. Deletes vpn file name in VPN_DIR denoted by the user.

    Args:
        None

    Returns:
        None

    Responses:
        'NAME?': queries for name of file in VPN_DIR
        'SUCCESS': deletion was successful

    Errors:
        'ERROR:FILEDOESNOTEXIST': denoted file does not exist.
    '''
    logger.info(inform("#### Client requested a vpn file deletion."))
    respond("NAME?")
    target_path_user = receive()
    target_name = os.path.basename(target_path_user)
    target_path = f"{VPN_DIR}/{target_name}"
    if not os.path.exists(f"{target_path}"):
        logger.error(failure("Non-existant vpn file denoted: \'{target_path}\'."))
        respond("ERROR:FILEDOESNOTEXIST")
        return
    logger.info(inform("File to be deleted: \'{target_path}\'."))
    os.remove(f"{target_path}")
    logger.info(success("File deleted."))
    respond("SUCCESS")



def current():
    '''
    Handles the 'CURRENT' command. Sends the name of VPN_DIR file currently selected
    for connecting, which can be accessed through a deterministic symbolic link to it.

    Args:
        None

    Returns:
        None

    Responses:
        [currently selected file name]

    Errors:
        'ERROR:NOFILESELECTED': symbolic link either does not exist or is broken.
    '''
    logger.info(inform("#### Client queried for currently selected vpn file."))
    if not os.path.exists(f"{VPN_LINK}"):       # this also takes care of broken links
        logger.error(failure(f"Symbolic link does not exist: \'{VPN_LINK}\'."))
        respond("ERROR:NOFILESELECTED")
        return
    current_path = os.readlink(f"{VPN_LINK}")
    current_file = os.path.basename(f"{current_path}")
    logger.info(inform(f"Currently selected file: \'{current_file}\'."))
    respond(f"{current_file}")

def select():
    '''
    Handles the 'SELECT' command. Changes / creates the symbolic link pointing to the vpn file
    to be used when connecting.
    
    Args:
        None

    Returns:
        None

    Responses:
        'NAME?': name of vpn file for the symbolic link to point to.
        'SUCCESS': symbolic link creation / relinking was successful

    Errors:
        'ERROR:FILEDOESNOTEXIST': file of denoted name does not exist in VPN_DIR
    '''
    logger.info(inform("#### Client requested to change the currently selected vpn file."))
    respond("NAME?")
    path_user = receive()
    name = os.path.basename(f"{path_user}")
    path = f"{VPN_DIR}/{name}"
    if not os.path.exists(f"{path}"):
        logger.error(failure("Nonexist Selected file: \'{VPN_DIR}/{name}\' does not exist."))
        respond("ERROR:FILEDOESNOTEXIST")
        return
    logger.info(inform(f"Valid path given: \'{path}\'."))
    os.symlink(f"{VPN_DIR}/{name}", f"{ROOT_MNGR_DIR}/temporarylink")
    os.rename(f"{ROOT_MNGR_DIR}/temporarylink", f"{VPN_LINK}")
    logger.info(success(f"Symbolic link changed: \'{VPN_LINK}\' -> \'{os.readlink(VPN_LINK)}\'."))
    respond("SUCCESS")

def connect():
    '''
    Handles the 'CONNECT' command. Executes the openvpn process with the vpn file pointed to by 
    the symbolic link.

    Args:
        None

    Returns:
        None

    Responses:
        'SUCCESS': establishment of connection was successful.

    Errors:
        'ERROR:CONNECTED': the connection was already established.
    '''
    global process
    global connection_active
    logger.info(inform("#### Client requested to activate vpn."))
    if connection_active:
        logger.error(failure("Openvpn daemon is already active."))
        respond("ERROR:CONNECTED")
        return
    logger.info(inform("Activating vpn daemon."))
    process = subprocess.Popen(["openvpn", f"{VPN_LINK}"])
    connection_active = True
    logger.info(success("Daemon activated."))
    respond("SUCCESS")

def disconnect():
    '''
    Handles the DISCONNECT command. Kills the opevpn process.

    Args:
        None

    Returns:
        None

    Responses:
        'SUCCESS': the connection was severed successfully.

    Errors:
        'ERROR:DISCONNECTED': connection was not established before.
    '''
    global process
    global connection_active
    logger.info(inform("#### Client requested to deactivate vpn."))
    if not connection_active:
        logger.error(failure("Openvpn daemon is not active."))
        respond("ERROR:DISCONNECTED")
        return
    logger.info(inform("Deactivating vpn daemon."))
    process.kill()
    connection_active = False
    logger.info(success("Daemon deactivated."))
    respond("SUCCESS")

def main():
    '''
    The brain of the script.
    '''
    global logger
    global connection_active
    global process

    logger = logging.getLogger(__name__)
    logging.basicConfig(filename=f'{LOG_FILE}', encoding='utf-8', level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    check_root_privileges()

    setup_pipes()

    connection_active = False
    process = None
    while True:
        logger.info(inform("Command loop started."))
        command = receive()
        logger.info(inform(f"Command received: \'{command}\'."))
        match command:
            case "TERMINATE":
                terminate()
            case "STATUS":
                status()
            case "AVAILABLE":
                available()
            #case "UPLOAD":
            #    upload()
            #    pass
            #case "DELETE":
            #    delete()
            case "CURRENT":
                current()
            case "SELECT":
                select()
            case "CONNECT":
                connect()
            case "DISCONNECT":
                disconnect()
            case _:
                logger.error(failure(f"Command \'{command}\' not supported."))
                respond("ERROR:INVALIDCOMMAND")

if __name__ == '__main__':
    main()
