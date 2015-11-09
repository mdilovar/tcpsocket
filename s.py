#!/usr/bin/env python

import socket, time, random, string, re, textwrap
from random import randint

TCP_IP = '127.0.0.1'
TCP_PORT = 11000
PACKET_SIZE = 20

N  = 8 # window size
Cn = 0 # current window needle
Ln = 0 # last sequence number requested

data = '' # current packet buffer
message = '' # current message buffer
packets_per_current_msg = 0
# received messages are saved to this file
rec_msg_log_file = open("rec_msg_log_file.txt", "wb")

# packet pattern
pck_rgx = '<sn(\d)>([\d\w/]{%s})' % (PACKET_SIZE)

# message pattern
msg_rgx = '/start/([\d\w]+)/end/'

# garbled message header pattern
garb_msg_rgx = '(/start/([\d\w]+)/start/)|(/end/([\d\w]+)/end/)'
# message beginning error
msg_strt_err_rgx = '(^(?!/start/)(.+)$)'

# create a socket and start listening to port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(10)

# wait for client to connect
conn, addr = s.accept()
print 'Connection address:', addr

# set timeout for conn to avoid blocking
conn.settimeout(.1)


def isErrorFree(data):
    # randomly declares a packet as having an error
    noErr = random.choice([False, False, False, True, True, True])
    if noErr:
        # print 'packet has no error: %s' % data
        pass
    else:
        print 'Packet is corrupted: %s' % data

    return noErr

def processPacket(packet):
    global message, packets_per_current_msg, msglen
    print 'Accepted packet: ', packet
    payload = re.match(pck_rgx, data).group(2)
    message += payload
    packets_per_current_msg += 1
    # print 'debug: packets_per_current_msg ', packets_per_current_msg

    if re.match(msg_rgx, message):
        body = re.match(msg_rgx, message).group(1)
        msglen = len(body)
        rec_msg_log_file.write(message+'\n')
        print 'Receved message of length %s in %s packets. Content (excluding headers): %s' % (msglen, packets_per_current_msg, body)
        message = ''
        packets_per_current_msg = 0
    elif re.match(garb_msg_rgx, message) or re.match(msg_strt_err_rgx, message):
        raise Exception ('ERROR: garbled MESSAGE was received: ', message)

    # print 'debug: message so far: ', message

while True:
    # Repeat forever:

    # print 'debug: buffer: ', data
    #time.sleep(0.2)

    if re.match(pck_rgx, data):
        # when a whole packet has arrived, examine it
        if int(re.match(pck_rgx, data).group(1)) != Cn % N:
            # if the packet has the wrong sequence number
            #  refuse the packet - ignore it
            got = int(re.match(pck_rgx, data).group(1))
            expected = Cn % N
            # print 'debug: sn %s not expected. Expected sn: %s' % (got, expected)
        else:
            if not isErrorFree(data):
                # Send a NACK
                NackN = int(re.match(pck_rgx, data).group(1))
                print 'Sending NACK for packet with SN: ', NackN
                nack = '<n%s>' % NackN
                conn.send(nack)
            else:
                # If the packet has the right SN and is error free
                # Accept the packet and process it
                processPacket(data)
                if Cn - Ln == N - 1:
                    #Send an ACK every Nth packet successfully received
                    AckN = int(re.match(pck_rgx, data).group(1))
                    print 'Sending ACK for packet with SN: ', AckN
                    ack = '<a%s>' % AckN
                    conn.send(ack)
                    Ln = Cn
                Cn += 1

        # reset the data buffer after examining the whole packet
        data = ''

    try:
        data += conn.recv(1)
    except Exception, e:
        # to avoid blocking, conn will throw exception after a timeout
        pass
