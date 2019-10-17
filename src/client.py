import socket
import os
import threading
import time
import ntpath

import utility

TYPE_DATA = 0x0
TYPE_ACK = 0x1
TYPE_FIN = 0x2
TYPE_FIN_ACK = 0x3

# Sending file per thread
def sendFile(arr_file, UDP_IP, UDP_PORT, dataId):

    # Splitting files into packets
    dataArray = utility.fileSplitting(arr_file)
    manyPacket = len(dataArray)
    print(manyPacket)

    # Initial package sending... Give name
    fileName = ntpath.basename(arr_file)
    print("Trying to send packet")

    #try:
    # Binding socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    i = 0
    while i < 20:
        try:
            address = (UDP_IP, 5021 + i + dataId)
            print("Trying to bind to", address)
            sock.bind(address)
            break
        except:
            i += 5
    
    if i >= 20:
        print("Socket is full. Unable to send file:", (dataId + 1))
    
    print("Socket is set")
    
    i = 0
    while i < 5:
        try:
            # Sending file name
            packet = createPacket(TYPE_DATA,dataId,0,bytearray(fileName,"utf-8"))
            message = sendPacket(TYPE_DATA, packet, sock, (UDP_IP, UDP_PORT))
            target_port = utility.getData(message)
            target_port = int(target_port[0]) * 256 + int(target_port[1])
            break
        except:
            print("Socket timeout")
            print("Cannot get response from the server regarding target port")
            time.sleep(2)
            i += 1

    if i < 5:
        print("Received target port:", target_port)
    else:
        print("Receiver doesn't give port for communication")
        return 0
    

    # Initial call to print 0% progress
    utility.printProgressBar(0, manyPacket, prefix = 'Progress:', suffix = 'Complete', length = 50)

    i = 0
    while (i < len(dataArray) - 1):
        try:
            packet = createPacket(TYPE_DATA, dataId, i, dataArray[i])
            sendPacket(TYPE_DATA, packet, sock, (UDP_IP, target_port))
            # Update Progress Bar
            time.sleep(0.1)
            utility.printProgressBar(i + 1, manyPacket, prefix = 'Progress:', suffix = 'Complete', length = 50)
            i += 1
        except:
            print("Socket timeout")
            print("Error package sending at id =", dataId, "and sequence =", i, " -- Sending package again")
            time.sleep(1)

    end = False
    while not end:   
        try:
            packet = createPacket(TYPE_FIN, dataId, (len(dataArray) - 1), dataArray[len(dataArray) - 1])
            sendPacket(TYPE_FIN, packet, sock, (UDP_IP, target_port))
            # Update Progress Bar
            time.sleep(0.1)
            utility.printProgressBar(i + 1, manyPacket, prefix = 'Progress:', suffix = 'Complete', length = 50)
            end = True
        except:
            print("Socket timeout")
            print("Error package sending at id =", dataId, "and sequence =", (len(dataArray) - 1), " -- Sending package again")
            time.sleep(1)

    sock.close()

    


# Sending packet per thread
def sendPacket(dataType, packet, sock, addr):
    # Sending file procedure
    sent_packet = bytes(packet)
    sock.sendto(bytes(packet), addr)
    message = 0xFF
    message, sender_addr = sock.recvfrom(utility.MAX_PACKET_SIZE)
    
    if message != 0xFF:
        if utility.getPacketType(message) == dataType + 1:
            return message
        else:
            print("Packet id: not acknowledged")
            time.sleep(2)
    else:
        print("Packet id:not received")
        time.sleep(2)


def createPacket(dataType, dataId, dataSequence, data):
    # Packet creation
    packet = utility.createPacketWithoutCheckSum(dataType, dataId, dataSequence, data)

    isOdd = False
    if (utility.isPacketOdd(packet)):
        isOdd = True
    
    checksum = utility.countCheckSum(packet)

    if (isOdd):
        packet = packet[:-1]
    
    utility.createPacketWithChecksum(packet, checksum)

    return packet



# Configuring IP address and port
hostname = socket.gethostname()
UDP_IP = input("Insert target IP address:")
UDP_PORT = int(input("Insert target port:"))

print("UDP target IP:", UDP_IP)
print("UDP target port: ", UDP_PORT)

# Creating array of files that want to be transfered
files_num = int(input("Insert the number of files: "))
while files_num <= 0 or files_num > 5:
    print("Invalid amount of files")
    files_num = int(input("Insert the number of files: "))

arr_files = []
for i in range(files_num):
    selected_file = input("Insert file target relative to this file : ")
    arr_files.append(selected_file)

print()

# Connecting to socket
for i in range(len(arr_files)):
    socketThread = threading.Thread(target = sendFile, args = (arr_files[i], UDP_IP, UDP_PORT, i))
    socketThread.start()
    time.sleep(1)