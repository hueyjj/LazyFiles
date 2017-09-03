#!/usr/bin/env python

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
MAX_FILEREAD        = 1048576            # Amount (bytes) to send 

file_list = None

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
        print("Unable to determine payload size", flush=True)
        return None
    
    #print("current size", current_size, "payload size", payload_size, flush=True)
    while current_size < payload_size:
        try:
            data = conn.recv(MAX_PAYLOAD)
        except socket.timeout as e:
            print("Max timeout reached for payload size", payload_size, "...unable to continue to receive more data")
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
            print("\r", addr, current_sent, '/', file_size, "bytes sent", flush=True, end='')
        print("\r", addr, current_sent, '/', file_size, "bytes sent", flush=True)

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
                print(addr, "Requested file name", file_no, ":", file_list[file_no]["name"], flush=True)
                send_file_name(file_no, conn)
            except ValueError as e:
                send_msg("UNKNOWN_REQUEST -- " + client_msg, conn)
        elif "REQUEST_FILE_DOWNLOAD" in client_msg:
            _, _, file_no = client_msg.partition("REQUEST_FILE_DOWNLOAD")
            try:
                file_no = int(file_no)
                print(addr, "Requested file download", file_no, ":", file_list[file_no]["name"], flush=True)
                send_file(file_no, conn, addr)
            except ValueError as e:
                send_msg("UNKNOWN_REQUEST -- " + client_msg, conn)
        
        elif "REQUEST_FILE_COUNT" == client_msg:
            send_msg(str(len(file_list)), conn)

def start_server():
    global file_list
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        print("Opening server socket...", end='', flush=True)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #server_socket.settimeout(30)
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        print("ok", flush=True)
        
        while True:
            conn, addr = server_socket.accept()
            if not conn: 
                continue 
            conn.settimeout(60)     # 1 minute timeout
            
            print()
            print(addr, "Client connection established", flush=True)
            send_msg(CONNECTION_RECEIVED, conn)
            
            while conn:
                # Refresh file list
                file_list = read_directory_list(DIRECTORY_LIST)

                input_data = recv_size(conn)
                if input_data:
                    client_msg = input_data.decode()
                else:
                    print(addr, "Connection lost: cannot read client reply", flush=True)
                    conn = None
                    continue
                
                print(addr, "msg:", client_msg, flush=True)
                try:
                    handle_client_msg(client_msg, conn, addr)
                except (socket.timeout, ConnectionResetError) as e:
                    print(addr, "Connection lost: timeout or reset", flush=True)
                    conn = None
                    continue
                except Exception as e:
                    print(addr, "Connection lost: unknown error", flush=True)
                    print(e, flush=True)
                    conn = None
                    continue
                
                if "CONNECTION_END" == client_msg: 
                    print(addr, "Connection ending...", end='', flush=True)
                    conn.close()
                    conn = None
                    print("ok", flush=True)
    
        print("Closing server socket...", end="", flush=True)
        server_socket.close()
        print("ok", flush=True)

if __name__ == "__main__":
    start_server()

