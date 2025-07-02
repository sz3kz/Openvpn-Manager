#!/usr/bin/env python3
import os
import sys

ROOT_PIPE_DIR="/var/run"
INPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-server.pipe"
OUTPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-client.pipe"

def terminate():
    for pipe in [INPUT_PIPE, OUTPUT_PIPE]:
        os.remove(f"{pipe}")
        print(f"Pipe {pipe} removed.")
    print("Terminated")
    sys.exit(0)


if os.geteuid() != 0:
    print(f"Insufficient privileges.")
    print(f"{sys.argv[0]} must be ran with root privileges!")
    sys.exit(1)
print("Sufficent privileges.")

for pipe in [INPUT_PIPE, OUTPUT_PIPE]:
    if os.path.exists(f"{pipe}"):
        print(f"\'{pipe}\' already exists.")
        os.remove(f"{pipe}")
        print(f"\'{pipe}\' deleted.")
    os.mkfifo(f"{pipe}")
    print(f"\'{pipe}\' created.")

while True:
    with open(f"{INPUT_PIPE}", 'r') as input_pipe:
        command = input_pipe.read().strip()
        print(f"Command: \'{command}\'")
    match command:
        case "TERMINATE":
            terminate()
        case _:
            print(f"ERROR: command \'{command}\' not supported.")
