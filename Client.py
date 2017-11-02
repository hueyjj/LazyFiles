#!/usr/bin/python3

import sys
import logging
import socket
import os
import time
import getopt

#   (Valid client messages)
#       # = valid file number integer 0 ... n
#
#   REQUEST_FILE_COUNT              Send/Receive number of files
#   REQUEST_FILE_LIST               Send/Receive all available files to download
#   REQUEST_FILE_NAME #             Send/Receive name of file #
#   REQUEST_FILE_DOWNLOAD_ALL       Send/Receive all files listed
#   REQUEST_FILE_DOWNLOAD #         Send/Recieve file #

#   CONNECTION_RECEIVED             Received client connection
#   CONNECTION_END                  Client ended connection

REQUEST_FILE_COUNT          = "REQUEST_FILE_COUNT"
REQUEST_FILE_LIST           = "REQUEST_FILE_LIST"
REQUEST_FILE_NAME           = "REQUEST_FILE_NAME"
REQUEST_FILE_DOWNLOAD       = "REQUEST_FILE_DOWNLOAD"
                                                       
CONNECTION_RECEIVED         = "CONNECTION_RECEIVED"
CONNECTION_END              = "CONNECTION_END"

request_flag = False
request_arg = None

# Client debug information
logging.basicConfig(filename="client.log", filemode="w", level=logging.DEBUG)
if sys.stdout:
    std_handler = logging.StreamHandler(sys.stdout)
    logging.getLogger().addHandler(std_handler)

def usage():
    print("Client.py [-h] [-r argument]")

def scan_opts():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 
            "hr:", ["help", "request="])
    except getopt.GetoptError as err:
        logging.error(err)
        print("Try 'Client.py --help' for more information")
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(2)
        elif o in ("-r", "--request"):
            request_flag = True;
            request_arg = a

def handle_request():
    pass
        
def main():
    scan_opts()

if __name__ == "__main__":
    main()
    std_handler.close()
