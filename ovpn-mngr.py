#!/usr/bin/env python3

import sys

def main():
    if len(sys.argv) == 1:
        print("No command found!")
        sys.exit(1)
    command = sys.argv[1]
    match command:
        case 'terminate':
            pass
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
