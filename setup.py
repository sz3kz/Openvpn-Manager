#!/usr/bin/env python3
import os
import sys

ROOT_DIRECTORY="/root/.openvpn-management"

if os.geteuid() != 0:
    print(f"Insufficient privileges.")
    print(f"{sys.argv[0]} must be ran with root privileges!")
    sys.exit(1)
print("Sufficent privileges.")

if os.path.exists(f"{ROOT_DIRECTORY}"):
    print(f"\"{ROOT_DIRECTORY}\" already exists.")
else:
    os.makedirs(f"{ROOT_DIRECTORY}")
    print(f"\"{ROOT_DIRECTORY}\" created.")


if os.path.exists(f"{ROOT_DIRECTORY}/vpns"):
    print(f"\"{ROOT_DIRECTORY}/vpns\" already exists.")
else:
    os.makedirs(f"{ROOT_DIRECTORY}/vpns")
    print(f"\"{ROOT_DIRECTORY}/vpns\" created.")
