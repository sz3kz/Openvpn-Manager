#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

ROOT_PIPE_DIR="/var/run"
INPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-server.pipe"
OUTPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-client.pipe"

ROOT_MNGR_DIR="/root/.openvpn-management"
VPN_DIR=f"{ROOT_MNGR_DIR}/vpns"
VPN_LINK=f"{ROOT_MNGR_DIR}/current"


def respond(message):
    with open(f"{OUTPUT_PIPE}", 'w') as output_pipe:
        output_pipe.write(f"{message}")
    print(f"    > \'{message}\'")

def receive():
    with open(f"{INPUT_PIPE}", 'r') as input_pipe:
        response = input_pipe.read().strip()
    print(f"    < \'{response}\'")
    return response

def setup_pipes():
    for pipe in [INPUT_PIPE, OUTPUT_PIPE]:
        if os.path.exists(f"{pipe}"):
            print(f"Pipe already exists: \'{pipe}\'.")
            os.remove(f"{pipe}")
            print(f"Pipe deleted: \'{pipe}\'.")
        os.mkfifo(f"{pipe}")
        print(f"Pipe created: \'{pipe}\'.")

def check_root_privileges():
    if os.geteuid() != 0:
        print(f"Insufficient privileges: \'{os.geteuid()}\'.")
        print(f"{sys.argv[0]} must be ran with root privileges!")
        sys.exit(1)
    print(f"Sufficient privileges: \'{os.geteuid()}\'.")


def terminate():
    print("#### Client requested termination of daemon.")
    if connection_active:
        process.kill()
        print(f"Killed still active openvpn connection.")
    for pipe in [INPUT_PIPE, OUTPUT_PIPE]:
        os.remove(f"{pipe}")
        print(f"Removed pipe: \'{pipe}\'.")
    print("Daemon terminated.")
    respond("TERMINATED")
    sys.exit(0)

def status():
    print("#### Client queried status of connection.")
    if connection_active:
        print("Connection is active.")
        respond(f"CONNECTED")
    else:
        print("Connection is not active.")
        respond(f"DISCONNECTED")

def available():
    print("#### Client requested a listing of available vpn files.")
    files = os.listdir(f"{VPN_DIR}")
    print(f"Files available: {len(files)}.")
    respond(f"{len(files)}")
    print(f"Listing files:")
    for file in files:
        print(f" - \'{file}\'")
        response = receive()
        if not response == "CONTINUE":
            return
        respond(f"{file}")
    print("Listing done.")

def upload():
    print("#### Client requested a vpn file upload.")
    respond("PATH?")
    src_path = receive()
    if not os.path.exists(src_path):
        print(f"Non-existant source file denoted: \'{src_path}\'.")
        respond("ERROR:INVALIDFILE")
        return
    if not os.path.isfile(src_path):
        print(f"Non-file path denoted: \'{src_path}\'")
        respond("ERROR:NOTAFILE")
        return
    print(f"Source file : \'{src_path}\'")
    respond("NEWNAME?")
    dst_path_user = receive()
    dst_name = os.path.basename(dst_path_user)
    dst_path = f"{VPN_DIR}/{dst_name}"
    if os.path.exists(f"{dst_path}"):
        print(f"Already existant vpn file denoted: \'{dst_path}\'.")
        respond("ERROR:FILEEXISTS")
        return
    print(f"Target file : \'{dst_path}\'.")
    shutil.copy(f"{src_path}",f"{dst_path}")
    print("Copied source file to target file.")
    respond("SUCCESS")

def delete():
    print("#### Client requested a vpn file deletion.")
    respond("NAME?")
    target_path_user = receive()
    target_name = os.path.basename(target_path_user)
    target_path = f"{VPN_DIR}/{target_name}"
    if not os.path.exists(f"{target_path}"):
        print("Non-existant vpn file denoted: \'{target_path}\'.")
        respond("ERROR:FILEDOESNOTEXIST")
        return
    print("File to be deleted: \'{target_path}\'.")
    os.remove(f"{target_path}")
    print("File deleted.")
    respond("SUCCESS")



def current():
    print("#### Client queried for currently selected vpn file.")
    if not os.path.exists(f"{VPN_LINK}"):       # this also takes care of broken links
        print(f"Symbolic link does not exist: \'{VPN_LINK}\'.")
        respond("ERROR:NOFILESELECTED")
        return
    current_path = os.readlink(f"{VPN_LINK}")
    current_file = os.path.basename(f"{current_path}")
    print(f"Currently selected file: \'{current_file}\'.")
    respond(f"{current_file}")

def select():
    print("#### Client requested to change the currently selected vpn file.")
    respond("NAME?")
    path_user = receive()
    name = os.path.basename(f"{path_user}")
    path = f"{VPN_DIR}/{name}"
    if not os.path.exists(f"{path}"):
        print("Nonexist Selected file: \'{VPN_DIR}/{name}\' does not exist.")
        respond("ERROR:FILEDOESNOTEXIST")
    print(f"Valid path given: \'{path}\'.")
    os.symlink(f"{VPN_DIR}/{name}", f"{ROOT_MNGR_DIR}/temporarylink")
    os.rename(f"{ROOT_MNGR_DIR}/temporarylink", f"{VPN_LINK}")
    print(f"Symbolic link changed: \'{VPN_LINK}\' -> \'{os.readlink(VPN_LINK)}\'.")
    respond("SUCCESS")

def connect():
    global process
    global connection_active
    print("#### Client requested to activate vpn.")
    if connection_active:
        print("Openvpn daemon is already active.")
        respond("ERROR:CONNECTED")
        return
    print("Activating vpn daemon.")
    process = subprocess.Popen(["openvpn", f"{VPN_LINK}"])
    connection_active = True
    print("Daemon activated.")
    respond("SUCCESS")

def disconnect():
    global process
    global connection_active
    print("#### Client requested to deactivate vpn.")
    if not connection_active:
        print("Openvpn daemon is not active.")
        respond("ERROR:DISCONNECTED")
        return
    print("Deactivating vpn daemon.")
    process.kill()
    connection_active = False
    print("Daemon deactivated.")
    respond("SUCCESS")


check_root_privileges()

setup_pipes()

connection_active = False
process = None
while True:
    print("Command loop started.")
    command = receive()
    print(f"Command received: \'{command}\'.")
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
            print(f"Command \'{command}\' not supported.")
            respond("ERROR:INVALIDCOMMAND")
