#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import logging

ROOT_PIPE_DIR="/var/run"
INPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-server.pipe"
OUTPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-client.pipe"

ROOT_MNGR_DIR="/root/.openvpn-management"
VPN_DIR=f"{ROOT_MNGR_DIR}/vpns"
VPN_LINK=f"{ROOT_MNGR_DIR}/current"
LOG_FILE=f"{ROOT_MNGR_DIR}/log.txt"



def respond(message):
    with open(f"{OUTPUT_PIPE}", 'w') as output_pipe:
        output_pipe.write(f"{message}")
    logger.info(f"    > \'{message}\'")

def receive():
    with open(f"{INPUT_PIPE}", 'r') as input_pipe:
        response = input_pipe.read().strip()
    logger.info(f"    < \'{response}\'")
    return response

def setup_pipes():
    for pipe in [INPUT_PIPE, OUTPUT_PIPE]:
        if os.path.exists(f"{pipe}"):
            logger.info(f"Pipe already exists: \'{pipe}\'.")
            os.remove(f"{pipe}")
            logger.info(f"Pipe deleted: \'{pipe}\'.")
        os.mkfifo(f"{pipe}")
        logger.info(f"Pipe created: \'{pipe}\'.")

def check_root_privileges():
    if os.geteuid() != 0:
        logger.error(f"Insufficient privileges: \'{os.geteuid()}\'.")
        logger.error(f"{sys.argv[0]} must be ran with root privileges!")
        sys.exit(1)
    logger.info(f"Sufficient privileges: \'{os.geteuid()}\'.")


def terminate():
    logger.info("#### Client requested termination of daemon.")
    if connection_active:
        process.kill()
        logger.info(f"Killed still active openvpn connection.")
    for pipe in [INPUT_PIPE, OUTPUT_PIPE]:
        os.remove(f"{pipe}")
        logger.info(f"Removed pipe: \'{pipe}\'.")
    logger.info("Daemon terminated.")
    respond("TERMINATED")
    sys.exit(0)

def status():
    logger.info("#### Client queried status of connection.")
    if connection_active:
        logger.info("Connection is active.")
        respond("CONNECTED")
    else:
        logger.info("Connection is not active.")
        respond("DISCONNECTED")

def available():
    logger.info("#### Client requested a listing of available vpn files.")
    files = os.listdir(f"{VPN_DIR}")
    logger.info(f"Files available: {len(files)}.")
    respond(f"{len(files)}")
    logger.info("Listing files:")
    for file in files:
        logger.info(f" - \'{file}\'")
        response = receive()
        if not response == "CONTINUE":
            return
        respond(f"{file}")
    logger.info("Listing done.")

def upload():
    logger.info("#### Client requested a vpn file upload.")
    respond("PATH?")
    src_path = receive()
    if not os.path.exists(src_path):
        logger.error(f"Non-existant source file denoted: \'{src_path}\'.")
        respond("ERROR:INVALIDFILE")
        return
    if not os.path.isfile(src_path):
        logger.error(f"Non-file path denoted: \'{src_path}\'")
        respond("ERROR:NOTAFILE")
        return
    logger.info(f"Source file : \'{src_path}\'")
    respond("NEWNAME?")
    dst_path_user = receive()
    dst_name = os.path.basename(dst_path_user)
    dst_path = f"{VPN_DIR}/{dst_name}"
    if os.path.exists(f"{dst_path}"):
        logger.info(f"Already existant vpn file denoted: \'{dst_path}\'.")
        respond("ERROR:FILEEXISTS")
        return
    logger.info(f"Target file : \'{dst_path}\'.")
    shutil.copy(f"{src_path}",f"{dst_path}")
    logger.info("Copied source file to target file.")
    respond("SUCCESS")

def delete():
    logger.info("#### Client requested a vpn file deletion.")
    respond("NAME?")
    target_path_user = receive()
    target_name = os.path.basename(target_path_user)
    target_path = f"{VPN_DIR}/{target_name}"
    if not os.path.exists(f"{target_path}"):
        logger.error("Non-existant vpn file denoted: \'{target_path}\'.")
        respond("ERROR:FILEDOESNOTEXIST")
        return
    logger.info("File to be deleted: \'{target_path}\'.")
    os.remove(f"{target_path}")
    logger.info("File deleted.")
    respond("SUCCESS")



def current():
    logger.info("#### Client queried for currently selected vpn file.")
    if not os.path.exists(f"{VPN_LINK}"):       # this also takes care of broken links
        logger.error(f"Symbolic link does not exist: \'{VPN_LINK}\'.")
        respond("ERROR:NOFILESELECTED")
        return
    current_path = os.readlink(f"{VPN_LINK}")
    current_file = os.path.basename(f"{current_path}")
    logger.info(f"Currently selected file: \'{current_file}\'.")
    respond(f"{current_file}")

def select():
    logger.info("#### Client requested to change the currently selected vpn file.")
    respond("NAME?")
    path_user = receive()
    name = os.path.basename(f"{path_user}")
    path = f"{VPN_DIR}/{name}"
    if not os.path.exists(f"{path}"):
        logger.error("Nonexist Selected file: \'{VPN_DIR}/{name}\' does not exist.")
        respond("ERROR:FILEDOESNOTEXIST")
        return
    logger.info(f"Valid path given: \'{path}\'.")
    os.symlink(f"{VPN_DIR}/{name}", f"{ROOT_MNGR_DIR}/temporarylink")
    os.rename(f"{ROOT_MNGR_DIR}/temporarylink", f"{VPN_LINK}")
    logger.info(f"Symbolic link changed: \'{VPN_LINK}\' -> \'{os.readlink(VPN_LINK)}\'.")
    respond("SUCCESS")

def connect():
    global process
    global connection_active
    logger.info("#### Client requested to activate vpn.")
    if connection_active:
        logger.error("Openvpn daemon is already active.")
        respond("ERROR:CONNECTED")
        return
    logger.info("Activating vpn daemon.")
    process = subprocess.Popen(["openvpn", f"{VPN_LINK}"])
    connection_active = True
    logger.info("Daemon activated.")
    respond("SUCCESS")

def disconnect():
    global process
    global connection_active
    logger.info("#### Client requested to deactivate vpn.")
    if not connection_active:
        logger.error("Openvpn daemon is not active.")
        respond("ERROR:DISCONNECTED")
        return
    logger.info("Deactivating vpn daemon.")
    process.kill()
    connection_active = False
    logger.info("Daemon deactivated.")
    respond("SUCCESS")

def main():
    global logger 
    global connection_active
    global process
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename=f'{LOG_FILE}', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s')

    check_root_privileges()

    setup_pipes()

    connection_active = False
    process = None
    while True:
        logger.info("Command loop started.")
        command = receive()
        logger.info(f"Command received: \'{command}\'.")
        match command:
            case "TERMINATE":
                terminate()
            case "STATUS":
                status()
            case "AVAILABLE":
                available()
            case "UPLOAD":
                upload()
            case "DELETE":
                delete()
            case "CURRENT":
                current()
            case "SELECT":
                select()
            case "CONNECT":
                connect()
            case "DISCONNECT":
                disconnect()
            case _:
                logger.error(f"Command \'{command}\' not supported.")
                respond("ERROR:INVALIDCOMMAND")

if __name__ == '__main__':
    main()
