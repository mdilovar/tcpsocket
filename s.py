#!/usr/bin/env python

import socket, time, random, string, re, textwrap
from random import randint


TCP_IP = '127.0.0.1'
TCP_PORT = 11000
PACKET_SIZE = 20
PACKET_HEADER_SIZE = 5
WINDOW_SIZE = 8


N  = 8 # window size
Rn = 0 # request number
Sn = 0 # sequence number
Sb = 0 # sequence base
Sm = 0 # sequence max
Ln = 0 # last sequence number requested

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(10)

# packet pattern
pck_rgx = '<sn(\d)>([\d\w/]{%s})' % (PACKET_SIZE)

# message header pattern
msg_hdr_rgx = '\/mlen(\d{2})\/'

conn, addr = s.accept()
print 'Connection address:', addr

conn.settimeout(.1)

data = ''
message = ''
msglen = 0
messages = []
packets_per_current_msg = 0

def errFree(data):
    # randomly declares a packet as having an error
    noErr = random.choice([True, True, True, True, True, False])
    if noErr:
        #print 'packet has no error: %s' % data
        pass
    else:
        print 'Packet is corrupted: %s' % data

    return noErr

def processPacket(packet):
    global messages, message, packets_per_current_msg, msglen
    print 'Accepted packet: ', packet
    payload = re.match(pck_rgx, data).group(2)
    message += payload
    packets_per_current_msg += 1
    print 'debug: packets_per_current_msg ', packets_per_current_msg

    if re.match(msg_hdr_rgx, message):
        # if a message header is found, read message length
        msglen = int(re.match(msg_hdr_rgx, message).group(1))
        # then remove the header to start buffering the body
        mheader = re.match(msg_hdr_rgx, message).group(0)
        message = message.replace( mheader, '')
        #packets_per_current_msg -= 1

    if msglen > 0 and len(message) >= msglen:
        # if the buffer reaches message size give in the header,
        # reset buffer and save the message
        #message = message.replace('/eof/', '')
        tobeappended = message[:msglen]
        messages.append(tobeappended)
        print 'Receved message of length %s in %s packets. Content (excluding headers): %s' % (msglen, packets_per_current_msg, tobeappended)
        message = message[msglen:]
        packets_per_current_msg = 0

    # print 'debug: message so far: ', message


def ignorePacket(packet):
    #print 'ignored packet: ', packet
    pass



while True:
    # Do the following forever:

    #print 'debug: buffer: ', data
    #time.sleep(0.2)

    if re.match(pck_rgx, data):
        # when a whle packet has arrived, examine it
        if int(re.match(pck_rgx, data).group(1)) != Rn % N:
            # if the packet has the sequence number
            #  refuse the packet - ignore it
            # print 'debug: sn not expected. Expected sn: ', Rn % N
            ignorePacket(data)
        else:
            if not errFree(data):
                # if the packet has error ignore it
                ignorePacket(data)
                #Send a Request for Rn
                print 'Asking the sender for packet with SN: ', Rn % N
                req = '<rn%s>' % (Rn % N)
                conn.send(req)
            else:
                # If the packet received Sn == Rn and the packet is error free
                #Accept the packet and send it to a higher layer
                processPacket(data)
                Rn = Rn + 1
                if Rn - Ln == N:
                    #Send a Request for Rn
                    print 'Asking the sender for packet with SN: ', Rn % N
                    req = '<rn%s>' % (Rn % N)
                    conn.send(req)
                    Ln = Rn

        # reset the data buffer after examining the whole packets
        data = ''

    try:
        data += conn.recv(1)
        # time.sleep(0.4)
        # print 'received so far: ', data
    except Exception, e:
        # print 'debug: norec %s ' % e
        pass
