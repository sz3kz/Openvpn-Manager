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
    with open(f"{OUTPUT_PIPE}", 'w') as output_pipe:
        output_pipe.write("TERMINATED")
    sys.exit(0)

def status():
    if connection_active:
        print("Connection is active")
        status_output="CONNECTED"
    else:
        print("Connection is not active")
        status_output="DISCONNECTED"

    with open(f"{OUTPUT_PIPE}",'w') as output_pipe:
        output_pipe.write(f"{status_output}")


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

connection_active = False
while True:
    with open(f"{INPUT_PIPE}", 'r') as input_pipe:
        command = input_pipe.read().strip()
        print(f"Command: \'{command}\'")
    match command:
        case "TERMINATE":
            terminate()
        case "STATUS":
            status()
        case _:
            print(f"ERROR: command \'{command}\' not supported.")
