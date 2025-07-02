#!/usr/bin/env python3
import os
import sys

ROOT_PIPE_DIR="/var/run"
INPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-server.pipe"
OUTPUT_PIPE=f"{ROOT_PIPE_DIR}/ovpn-mngr-client.pipe"

ROOT_MNGR_DIR="/root/.openvpn-management"
VPN_DIR=f"{ROOT_MNGR_DIR}/vpns"

def respond(message):
    with open(f"{OUTPUT_PIPE}", 'w') as output_pipe:
        output_pipe.write(f"{message}")

def terminate():
    respond("TERMINATED")
    for pipe in [INPUT_PIPE, OUTPUT_PIPE]:
        os.remove(f"{pipe}")
        print(f"Pipe {pipe} removed.")
    print("Terminated")
    sys.exit(0)

def status():
    if connection_active:
        print("Connection is active")
        respond(f"CONNECTED")
    else:
        print("Connection is not active")
        respond(f"DISCONNECTED")

def available():
    files = os.listdir(f"{VPN_DIR}")
    print(f"{len(files)} files available.")
    respond(f"{len(files)}")
    for file in files:
        print(f"{file}")
        with open(f"{INPUT_PIPE}", 'r') as input_pipe:
            response = input_pipe.read().strip()
        if not response == "CONTINUE":
            return None
        respond(f"{file}")
    print("Listing done.")


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
    print("Command loop started.")
    with open(f"{INPUT_PIPE}", 'r') as input_pipe:
        command = input_pipe.read().strip()
        print(f"Command: \'{command}\'")
    match command:
        case "TERMINATE":
            terminate()
        case "STATUS":
            status()
        case "AVAILABLE":
            available()
        case _:
            print(f"ERROR: command \'{command}\' not supported.")
