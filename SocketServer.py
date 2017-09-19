#!/usr/bin/env python

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

DIRECTORY_LIST = r".\Directory-List.txt"

HOST                = ''                 # Local host
PORT                = 1234               # Random port
MAX_PAYLOAD         = 2048               # Amount (bytes) to receive ~2kb
MAX_BYTES           = 2**31              # ~2.147483648 GB 
MAX_FILEREAD        = 2**25              # Amount (bytes) to send 

file_list = None

# Record LazyFile information
logging.basicConfig(filename="LazyFiles.log", filemode="w", level=logging.DEBUG)
if sys.stdout:
    std_handler = logging.StreamHandler(sys.stdout)
    logging.getLogger().addHandler(std_handler)

def append(bytes_, buffer_):
    for b in bytes_:
        buffer_.append(b)

#int size
def size_to_bytes(size):
    return size.to_bytes(4, byteorder="big", signed=False) 

def data_to_bytes(data):
    if type(data) is str:
        b_data = bytearray(data, "utf-8")
    elif type(data) is bytes:
        b_data = bytearray(data)
    else:
        return None
    
    return b_data

def data_to_send(b_size, b_data):
    buffer_ = bytearray()
    append(b_size, buffer_)
    append(b_data, buffer_)
    
    return buffer_

def recv_size(conn):
    try:
        data = conn.recv(MAX_PAYLOAD)
    except (socket.timeout, ConnectionResetError) as e:
        return None

    #Get size of payload
    buffer_ = bytearray()
    if len(data) >= 4: 
        payload_size = int.from_bytes(data[:4], byteorder="big", signed=False)
        for byte in data[4:]:
            buffer_.append(byte)
        current_size = len(buffer_) 
    else:
        #Exit if there's no payload
        logging.error("%s Unable to determine payload size", conn)
        return None
    
    while current_size < payload_size:
        try:
            data = conn.recv(MAX_PAYLOAD)
        except socket.timeout as e:
            logging.warning("Max timeout reached for payload size %d: unable to continue to receive more data", payload_size)
            return None
            
        append(data, buffer_)
        current_size = len(buffer_)

    return buffer_

def read_directory_list(dir_list):
    list_ = []       
    for dir_ in open(dir_list, "r"):
        dir_ = dir_.strip()
        files = os.listdir(path=dir_)
        
        for file_ in files:
            full_path = "".join([dir_, "\\", file_]) 
            
            # Remove directories and other cases
            _, ext = os.path.splitext(full_path)
            invalid_ext = [".zip", ".html"]
            if os.path.isdir(full_path) is False and ext not in invalid_ext:
                file_stats = os.stat(full_path)
                file_size = file_stats.st_size
                if (os.path.isdir(full_path)): 
                    file_type = "..." #Directory
                
                list_.append({
                    "name": file_,
                    "type": ext,
                    "size": file_size,
                    "path": dir_,
                })
    return list_

def send_file_list(conn):
    files = list(file_list)
    for i in range(len(files)): 
        files[i]["size"] = "{:,}".format(files[i]["size"]) #Add commas
    
    files = list(enumerate(files))
    
    #Alignment
    max_just0 = len(str(max([index for index, _ in files])))
    max_just1 = max([len(f["size"]) for index, f in files])
    max_just2 = max([len(f["type"]) for index, f in files])
    max_just3 = max([len(f["name"]) for index, f in files])
    
    data = "".join([
        "{:>{x0}} {:>{x1}} {:>{x2}} {:<{x3}} {}".format(
            index, file_["size"], file_["type"], file_["name"], '\n', 
            x0=max_just0, x1=max_just1, x2=max_just2, x3=max_just3,
        ) for index, file_ in files
    ])
    send_msg(data, conn)

def send_file_name(file_no, conn):
    send_msg(file_list[file_no]["name"], conn)

def send_file(file_no, conn, addr):
    f = file_list[file_no]
    file_path = "".join([f["path"], '\\', f["name"]])
    with open(file_path, "rb") as file_:
        file_size = f["size"]
        data_size = size_to_bytes(int(file_size))
        data = file_.read(MAX_FILEREAD)
        data = data_to_send(data_size, data)
        conn.sendall(data)
        current_sent = len(data) - 4    # Subtract size of data at beginning
        while True:
            data = file_.read(MAX_FILEREAD)
            if not data: 
                break
            data = data_to_bytes(data)
            conn.sendall(data)
            current_sent += len(data)
            #print("\r %s %d / %d bytes sent" % (addr, current_sent, file_size), flush=True, end='')
        logging.info("%s %d / %d bytes sent", addr, current_sent, file_size)

def send_msg(msg, conn):
    data = data_to_bytes(msg)
    data_size = size_to_bytes(len(data))
    data = data_to_send(data_size, data)
    conn.sendall(data)

def handle_client_msg(client_msg, conn, addr):
    if "REQUEST_FILE" in client_msg:
        if "REQUEST_FILE_LIST" == client_msg:
            send_file_list(conn)
        elif "REQUEST_FILE_NAME" in client_msg:
            _, _, file_no = client_msg.partition("REQUEST_FILE_NAME")
            try:
                file_no = int(file_no)
                logging.info("%s Requested file name %d: %s", addr, file_no, file_list[file_no]["name"])
                send_file_name(file_no, conn)
            except ValueError as e:
                send_msg("UNKNOWN_REQUEST -- " + client_msg, conn)
        elif "REQUEST_FILE_DOWNLOAD" in client_msg:
            _, _, file_no = client_msg.partition("REQUEST_FILE_DOWNLOAD")
            try:
                file_no = int(file_no)
                logging.info("%s Requested file download %d: %s", addr, file_no, file_list[file_no]["name"])
                send_file(file_no, conn, addr)
            except ValueError as e:
                send_msg("UNKNOWN_REQUEST -- " + client_msg, conn)
        
        elif "REQUEST_FILE_COUNT" == client_msg:
            send_msg(str(len(file_list)), conn)

def start_server():
    global file_list
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        logging.info("Trying to open server socket at %s %d", HOST if HOST else "localhost", PORT)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #server_socket.settimeout(30)
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        logging.info("Server socket opened at %s %d", HOST if HOST else "localhost", PORT)
        
        while True:
            conn, addr = server_socket.accept()
            if not conn: 
                continue 
            conn.settimeout(60)     # 1 minute timeout
            
            logging.info("%s Client connection established", addr)
            send_msg(CONNECTION_RECEIVED, conn)
            
            while conn:
                # Refresh file list
                file_list = read_directory_list(DIRECTORY_LIST)

                input_data = recv_size(conn)
                if input_data:
                    client_msg = input_data.decode()
                else:
                    logging.debug("%s Connection lost: cannot read client reply", addr)
                    conn = None
                    continue
                
                logging.info("%s msg: %s", addr, client_msg)
                try:
                    handle_client_msg(client_msg, conn, addr)
                except (socket.timeout, ConnectionResetError) as e:
                    logging.error("%s Connection lost: timeout or reset", addr)
                    conn = None
                    continue
                except Exception as e:
                    logging.error("%s Connection lost: unknown error", addr)
                    logging.exception("%s", e)
                    conn = None
                    continue
                
                if "CONNECTION_END" == client_msg: 
                    logging.error("%s Connection ending...", addr)
                    conn.close()
                    conn = None
                    logging.error("%s Connection ended", addr)
    
        logging.info("Closing server socket")
        server_socket.close()
        logging.info("Server socket closed")
    
    std_handler.close()

if __name__ == "__main__":
    start_server()
    logging.shutdown()

