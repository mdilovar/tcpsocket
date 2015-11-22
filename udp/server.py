# UDPPingerServer.py

# We will need the following module to generate randomized lost packets 

import random, time

from socket import *

# Create a UDP socket

# Notice the use of SOCK_DGRAM for UDP packets

TIMEOUT = 0.9
lastPacketRecvTime = 0

serverSocket = socket(AF_INET, SOCK_DGRAM) # Assign IP address and port number to socket

serverSocket.bind(('', 11000))
serverSocket.settimeout(TIMEOUT)


while True:

    # Generate random number in the range of 0 to 10

    rand = random.randint(0, 10)

    # Receive the client packet along with the address it is coming from
    try:
        message, address = serverSocket.recvfrom(1024)
    except Exception,e:
        pass
        print 'The client application has stopped. Stopping the server.'
        break
    # Capitalize the message from the client

    message = message.upper()
    print rand

    # If rand is less is than 4, we consider the packet lost and do not respond

    if rand < 4:
        print 'packet lost. Time since last packet was received: %s seconds' % (time.time() - lastPacketRecvTime)
        continue
    lastPacketRecvTime = time.time()

    # Otherwise, the server responds

    serverSocket.sendto(message, address)
    print 'sent'
