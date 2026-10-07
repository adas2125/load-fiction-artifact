from scp import SCPClient
import getopt
import os
import paramiko
import sys
import time
from enum import Enum

# TODO: Update this to turn this into an automated experiment

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:],"u:c:s:f:p",["username=","client=","server=", "other-clients-file=", "port="])
    except getopt.GetoptError:
        print('cilantro_experiment.py -c <client-hostname> -s <server-hostname> -f <other-clients-file> -u <username> -p <port>')
        sys.exit(2)

    master_hostname = None
    for opt, arg in opts:
        if opt == '-c':
            master_hostname = arg
        else:
            print('cilantro_experiment.py -c <client-hostname> -s <server-hostname> -f <other-clients-file> -u <username> -p <port>')
            sys.exit(2)

    