# LazyFiles
LazyFiles is an Android application client that retrieves files from a computer running a Python server, using sockets.

## Purpose
Usually there are some interesting reads (pdf's) on the internet (e.g HackerNews) but reading on a phone is more 
preferable in some cases (so everywhere not at a desktop). But file transfer through a third-party site (google drive) is too reliant,
and using a usb cable is tiresome (because charging is much faster through an outlet rather than through a computer so leaving the phone plugged to 
the wall is preferable).

There are better, well-test softwares that can do LazyFiles' job, so use those. 

![Client](https://raw.githubusercontent.com/hueyjj/LazyFiles/master/Images/Client.PNG)
![Server](https://raw.githubusercontent.com/hueyjj/LazyFiles/master/Images/Server.PNG)

# Requirements
    - Android device
    - Python (on computer)
    - Both devices on the same local network

# Install
### From source
```sh
git clone https://github.com/hueyjj/LazyFiles.git
```
Open Android studio > Open LazyFiles\SocketClient

Build > Build APK

Install APK on Android device
    (i.e) Put it on Google drive and install it from the Android device, or some other way.

# How it works
A python server opens up a socket server. Then it reads from a file called Directory-List.txt. The server
will build a list of strings pointing to each files in each directory. 
   
In Directory-List.txt
```
C:\Users\Hueyjj\Algorithms
C:\Code\fun
```

In C:\Users\Hueyjj\Algorithms
```
Algorithm1.pdf
Algorithm2.pdf
```

In C:\Code\fun
```
How-to-cook_101.pdf
How-to-swim_101.pdf
```

The client will then ask for a file number and the server will reply back with the file to download.

# Usage
Add a directory to Directory-List.txt
```
C:\Some\Example\Directory
```

Start the server...
```sh
cd LazyFiles
./SocketServer.py
```
or
```sh
python SocketServer.py
```

#### Get server IP...

Get server (computer) local ip address. For windows, open cmd.exe (commmand prompt) and enter ipconfig. 
(Lazyfiles uses IPv4 so use IPv4 Address from ipconfig)

Example local IPv4 address: 10.0.0.30

#### Running LazyFiles (Android) client...

- Open LazyFiles

- Enter IPv4 address

- Connect
- 
- List Files (If it works, a list of files should be outputted on the Android device.)
- 
- Enter a file number (starts from 0)
- 
- Download
- 
- File saved should be at 

/storage/SD-CARD-SERIAL-NUMBER/USER.socketclient/files/Movies

or 

/storage/emulated/0/Download

- Use a file explorer on Android to reach the file or however way.

##### Important
If the file is saved in an application's local space, when the application is uninstalled, **all** 
files will be deleted along with it. A workaround is to relocate the entire /path/to/directory/ to 
a non-local space, for example /storage/SD-CARD-SERIAL-NUMBER.
