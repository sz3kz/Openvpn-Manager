#!/usr/bin/env python3

import sys
import os

from termcolor import colored

ROOT_PIPE_DIR="/var/run"
OUTPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-server.pipe"
INPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-client.pipe"


def failure(message):
    return colored(f'{message}','red')


def success(message):
    return colored(f'{message}','green')


def inform(message):
    return colored(f'{message}','yellow')


def send(message):
    with open(f"{OUTPUT_PIPE}", 'w') as output_pipe:
        output_pipe.write(f"{message}")


def receive():
    with open(f"{INPUT_PIPE}", 'r') as input_pipe:
        response = input_pipe.read().strip()
    return response


def check_root_privileges():
    if os.geteuid() != 0:
        print(failure("Insufficient (non-root!) privileges detected."))
        sys.exit(1)


def check_pipes():
    for pipe in [INPUT_PIPE, OUTPUT_PIPE]:
        if not os.path.exists(f"{pipe}"):
            print(failure(f"Missing pipe: \'{pipe}\'."))
            sys.exit(1)


def terminate():
    if len(sys.argv) != 2:
        print(failure("Invalid command format."))
        sys.exit(1)
    send('TERMINATE')
    response = receive()
    if response == "TERMINATED":
        print(success("Daemon terminated."))
        return
    print(failure("Server error."))


def status():
    if len(sys.argv) != 2:
        print(failure("Invalid command format."))
        sys.exit(1)
    send('STATUS')
    response = receive()
    if response == "CONNECTED":
        print(inform("Connection: On."))
    elif response == "DISCONNECTED":
        print(inform("Connection: Off."))
    else:
        print(failure("Server error."))

def available():
    if len(sys.argv) != 2:
        print(failure("Invalid command format."))
        sys.exit(1)
    send('AVAILABLE')
    file_amount = int(receive())
    print(inform(f"Listing files({file_amount}):"))
    for _ in range (0, file_amount):
        send("CONTINUE")
        file = receive()
        print(inform(f" - {file}"))
    print(success("Listing done."))

def upload():
    if len(sys.argv) != 4:
        print(failure("Invalid command format."))
        sys.exit(1)
    path = sys.argv[2]
    newname = sys.argv[3]
    send('UPLOAD')
    response = receive()
    if not response == 'PATH?':
        print(failure("Command failed."))
        sys.exit(1)
    send(f"{path}")
    response = receive()
    if not response == 'NEWNAME?':
        print(failure("Command failed."))
        sys.exit(1)
    send(f"{newname}")
    response = receive()
    if response != 'SUCCESS':
        print(failure("Command failed."))
        sys.exit(1)
    print(success("File uploaded."))

def delete():
    if len(sys.argv) != 3:
        print(failure("Invalid command format."))
        sys.exit(1)
    file = sys.argv[2]
    send('DELETE')
    response = receive()
    if not response == 'NAME?':
        print(failure("Command failed."))
        sys.exit(1)
    send(f'{file}')
    response = receive()
    if not response == 'SUCCESS':
        print(failure("Command failed."))
        sys.exit(1)
    print(success("File deleted."))


def current():
    if len(sys.argv) != 2:
        print(failure("Invalid command format."))
        sys.exit(1)
    send('CURRENT')
    file = receive()
    if file == "ERROR:NOFILESELECTED":
        print(inform("No file has been selected."))
        return
    print(inform(f"Current selected file: \'{file}\'"))


def select():
    if len(sys.argv) != 3:
        print(failure("Invalid command format."))
        sys.exit(1)
    file = sys.argv[2]
    send('SELECT')
    response = receive()
    if not response == 'NAME?':
        print(failure("Server error."))
        sys.exit(1)
    send(f"{file}")
    response = receive()
    if response == 'ERROR:FILEDOESNOTEXIST':
        print(failure("Denoted file does not exist."))
        sys.exit(1)
    if response == 'SUCCESS':
        print(success("File selected."))
        sys.exit(0)
    print(success("Server error."))



def connect():
    if not len(sys.argv) == 2:
        print(failure("Invalid command format."))
        sys.exit(1)
    send('CONNECT')
    response = receive()
    if response == 'ERROR:CONNECTED':
        print(failure("Connection already active."))
        sys.exit(1)
    if response == 'SUCCESS':
        print(success("Connection established."))
        sys.exit(0)
    print(failure("Server error."))


def disconnect():
    if not len(sys.argv) == 2:
        print(failure("Invalid command format."))
        sys.exit(1)
    send('DISCONNECT')
    response = receive()
    if response == 'ERROR:DISCONNECTED':
        print(failure("Connection not active."))
        sys.exit(1)
    if response == 'SUCCESS':
        print(success("Connection severed."))
        sys.exit(1)
    print(failure("Server error."))



def main():
    # check_root_privileges()
    check_pipes()
    if len(sys.argv) == 1:
        print(failure("No command found!"))
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
            print(failure(f"Unrecognized command: \'{command}\'"))


if __name__ == '__main__':
    main()
