#!/usr/bin/env python3

import sys
import os

ROOT_PIPE_DIR="/var/run"
OUTPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-server.pipe"
INPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-client.pipe"



def send(message):
    with open(f"{OUTPUT_PIPE}", 'w') as output_pipe:
        output_pipe.write(f"{message}")


def receive():
    with open(f"{INPUT_PIPE}", 'r') as input_pipe:
        response = input_pipe.read().strip()
    return response


def check_root_privileges():
    if os.geteuid() != 0:
        print("Run client with root privileges.")
        sys.exit(1)


def check_pipes():
    for pipe in [INPUT_PIPE, OUTPUT_PIPE]:
        if not os.path.exists(f"{pipe}"):
            print(f"Error: Missing pipe: \'{pipe}\'.")
            sys.exit(1)


def terminate():
    if len(sys.argv) != 2:
        print("Invalid command format.")
        sys.exit(1)
    print("Valid command format.")
    send('TERMINATE')
    print("Terminate sent")
    response = receive()
    if response == "TERMINATED":
        print("Command succeeded!")
        return
    print("ERROR: Command failed.")


def status():
    if len(sys.argv) != 2:
        print("Invalid command format.")
        sys.exit(1)
    print("Valid command format.")
    send('STATUS')
    print("STATUS sent")
    response = receive()
    if response == "CONNECTED":
        print("Connection live.")
    elif response == "DISCONNECTED":
        print("No connection.")
    else:
        print("ERROR: Command failed.")

def available():
    if len(sys.argv) != 2:
        print("Invalid command format.")
        sys.exit(1)
    print("Valid command format.")
    send('AVAILABLE')
    file_amount = int(receive())
    print(f"Listing files({file_amount}):")
    for _ in range (0, file_amount):
        send("CONTINUE")
        file = receive()
        print(f" - {file}")
    print("Command succeeded.")

def upload():
    if len(sys.argv) != 4:
        print("Invalid command format.")
        sys.exit(1)
    path = sys.argv[2]
    newname = sys.argv[3]
    print("Valid command format.")
    send('UPLOAD')
    response = receive()
    if not response == 'PATH?':
        print("Command failed.")
        sys.exit(1)
    send(f"{path}")
    response = receive()
    if not response == 'NEWNAME?':
        print("Command failed.")
        sys.exit(1)
    send(f"{newname}")
    response = receive()
    if response != 'SUCCESS':
        print("Command failed.")
        sys.exit(1)
    print("Command succeeded.")

def delete():
    if len(sys.argv) != 3:
        print("Invalid command format.")
        sys.exit(1)
    file = sys.argv[2]
    send('DELETE')
    response = receive()
    if not response == 'NAME?':
        print("Command failed.")
        sys.exit(1)
    send(f'{file}')
    response = receive()
    if not response == 'SUCCESS':
        print("Command failed.")
        sys.exit(1)
    print("Command succeeded.")


def current():
    if len(sys.argv) != 2:
        print("Invalid command format.")
        sys.exit(1)
    send('CURRENT')
    file = receive()
    if file == "ERROR:NOFILESELECTED":
        print("No file has been selected.")
    print(f"Current selected file: {file}")


def select():
    if len(sys.argv) != 3:
        print("Invalid command format.")
        sys.exit(1)
    file = sys.argv[2]
    send('SELECT')
    response = receive()
    if not response == 'NAME?':
        print("Command failed.")
        sys.exit(1)
    send(f"{file}")
    response = receive()
    if not response == 'SUCCESS':
        print("Command failed.")
        sys.exit(1)
    print("Command succeeded.")


def connect():
    if not len(sys.argv) == 2:
        print("Invalid command format.")
        sys.exit(1)
    send('CONNECT')
    response = receive()
    if not response == 'SUCCESS':
        print("Command failed.")
        sys.exit(1)
    print("Command succeeded.")


def disconnect():
    if not len(sys.argv) == 2:
        print("Invalid command format.")
        sys.exit(1)
    send('DISCONNECT')
    response = receive()
    if not response == 'SUCCESS':
        print("Command failed.")
        sys.exit(1)
    print("Command succeeded.")




def main():
    # check_root_privileges()
    check_pipes()
    if len(sys.argv) == 1:
        print("No command found!")
        sys.exit(1)
    command = sys.argv[1]
    match command:
        case 'terminate':
            terminate()
        case 'status':
            status()
        case 'available':
            available()
        #case 'upload':
        #    upload()
        #case 'delete':
        #    delete()
        case 'current':
            current()
        case 'select':
            select()
        case 'connect':
            connect()
        case 'disconnect':
            disconnect()
        case _:
            print(f"Error: unrecognized command: \'{command}\'")


if __name__ == '__main__':
    main()
