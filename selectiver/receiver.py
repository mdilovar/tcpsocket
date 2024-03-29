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

# keeps track of current window state
current_window = {0:0, 1:0, 2:0, 3:0,
                  4:0, 5:0, 6:0, 7:0}
# packets are buffered and processed only after the whole window arrives
PACKETS_BUFFER = {0:0, 1:0, 2:0, 3:0,
                  4:0, 5:0, 6:0, 7:0};


def isErrorFree(Sn):
    # randomly declares a packet as having an error
    noErr = random.choice([False, True, True, True, True, True])
    if noErr:
        # print 'packet has no error: %s' % data
        pass
    else:
        print 'Packet with SN %s is corrupted.' % Sn

    return noErr

def processWindow(packets_buffer):
    global message, packets_per_current_msg
    for i in range(0,N):
        data = packets_buffer[i]
        payload = re.match(pck_rgx, data).group(2)
        message += payload
        packets_per_current_msg += 1
        # print 'debug: packets_per_current_msg ', packets_per_current_msg

        if re.match(msg_rgx, message):
            # body = re.match(msg_rgx, message).group(1)
            msglen = len(message)
            rec_msg_log_file.write(message+'\n')
            print 'Received message of length %s in %s packet(s).' % (msglen, packets_per_current_msg)
            # print 'Content: %s' % message
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
        Sn = int(re.match(pck_rgx, data).group(1))
        print 'Packet with SN %s arrived - %s' % (Sn, data)
        if not isErrorFree(Sn):
            # Send a NACK
            NackN = Sn
            print 'Sending NACK for packet with SN: ', NackN
            nack = '<n%s>' % NackN
            current_window[NackN] = -1
            conn.send(nack)
        else:
            # If the packet has the right SN and is error free
            # Accept the packet and buffer it
            print 'Accepted packet: ', data
            AckN = Sn
            PACKETS_BUFFER[AckN] = data
            current_window[AckN] = 1

        for key, value in current_window.iteritems():
            if value !=1: break
            if key == len(current_window)-1:
                #Send an ACK when the whole window is successfully received
                print 'Sending ACK for packet with SN: ', N - 1
                ack = '<a%s>' % (N - 1)
                conn.send(ack)
                processWindow(PACKETS_BUFFER)
                # reset buffer and window
                current_window = {0:0, 1:0, 2:0, 3:0,
                                  4:0, 5:0, 6:0, 7:0}
                PACKETS_BUFFER = {0:0, 1:0, 2:0, 3:0,
                                  4:0, 5:0, 6:0, 7:0}

        # reset the data buffer after examining the whole packet
        data = ''

    try:
        data += conn.recv(1)
    except Exception, e:
        # to avoid blocking, conn will throw exception after a timeout
        pass
