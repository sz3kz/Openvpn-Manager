#!/usr/bin/env python3

import sys

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
    print("Command failed.")


def main():
    if len(sys.argv) == 1:
        print("No command found!")
        sys.exit(1)
    command = sys.argv[1]
    match command:
        case 'terminate':
            terminate()
        case 'status':
            pass
        case 'available':
            pass
        case 'upload':
            pass
        case 'delete':
            pass
        case 'current':
            pass
        case 'select':
            pass
        case 'connect':
            pass
        case 'disconnect':
            pass
        case _:
            print(f"Error: unrecognized command: \'{command}\'")


if __name__ == '__main__':
    main()
