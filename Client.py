#!/usr/bin/python3

import sys
import logging
import socket
import os
import time

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
