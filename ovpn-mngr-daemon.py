#!/usr/bin/env python3
import os
import sys

if os.geteuid() != 0:
    print(f"Insufficient privileges.")
    print(f"{sys.argv[0]} must be ran with root privileges!")
    sys.exit(1)
print("Sufficent privileges.")
