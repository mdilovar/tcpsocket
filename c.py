#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import time
import random
import string
import re
import textwrap
from random import randint

TCP_IP = '127.0.0.1'
TCP_PORT = 11000

PACKET_SIZE = 20
PACKET_HEADER_SIZE = 5
MSG_HEADER_SIZE = 12
PACKETS = []
PACKETS_BUFFER = []

N = 8  # window size
Rn = 0  # request number
Sn = 0  # sequence number
Sb = 0  # sequence base
Sm = N - 1  # sequence max
_sn = 0  # last assigned sn

# ACK pattern
ack_rgx = '^<a(\d)>'
# NACK pattern
nack_rgx = '^<n(\d)>'

# Response byffer (for acks and nack from the receiver)
response = ''

# generated messages are also saved in this file
msg_log_file = open("msg_log_file.txt", "wb")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
# set timeout for socket to avoid blocking
s.settimeout(.1)


def getPacket(Sn):
    global PACKETS, PACKETS_BUFFER, _sn
    # print 'debug: requested packet with sn: ', Sn
    # print 'debug: while current max sn is sm: : ', Sm
    # print 'debug: current packets len: ', len(PACKETS)
    while len(PACKETS_BUFFER) < N:
        # generate message and pack it
        msg = getMessage()
        new_packets = textwrap.wrap(msg, PACKET_SIZE)
        print 'Message is broken into %s packet(s)' % len(new_packets)
        for (idx, packet) in enumerate(new_packets):
            # stuff packet if it's not long enough
            while len(new_packets[idx]) < PACKET_SIZE:
                new_packets[idx] += '0'
            # add sequence number to packet
            new_packets[idx] = '<sn%s>%s' % (_sn % N, new_packets[idx])
            _sn += 1
        PACKETS_BUFFER += new_packets
    while len(PACKETS) < N:
        # keep PACKETS always N long by popping from packets buffer
        PACKETS.append(PACKETS_BUFFER.pop(0))
    for packet in PACKETS:
        Sn_rgx = '^<sn(%s)>' % Sn
        if re.match(Sn_rgx, packet):
            # print 'Sending packet # %s - %s' % (Sn,packet)
            return packet
    raise Exception('Packet with sequence number %s not found in %s' % (Sn, PACKETS))


def ackPacketsUpto(Sn):
    # SN IS INCLUSIVE - the method chops off all packets
    # up to and including Sn
    global PACKETS
    upto_idx = 0
    for (idx, packet) in enumerate(PACKETS):
        Sn_rgx = '^<sn(%s)>' % Sn
        if re.match(Sn_rgx, packet):
            upto_idx = idx + 1
            break
    # print 'debug: before chopping: ', PACKETS
    # print 'debug: sn: ', Sn
    PACKETS = PACKETS[upto_idx:]
    # print 'debug: after chopping: ', PACKETS


def getMessage():
    msg_size = randint(1, 5)
    msg_size *= PACKET_SIZE
    msg_size -= MSG_HEADER_SIZE
    msg = ''.join(random.choice(string.ascii_uppercase + string.digits)
                  for _ in range(msg_size))
    # append headers to msg - /start/message/end/
    msg = '/start/%s/end/' % msg
    print 'Message is ready. Size (including headers): %s \nContent: %s' % (len(msg), msg)
    msg_log_file.write(msg+'\n')
    return msg

needle = 0

while True:
    # Repeat forever:

    # print 'debug: Sb: %s | Sn: %s | Sm: %s | Rn: %s' % (Sb, Sn, Sm, Rn)
    # print 'debug: res', response

    if re.match(ack_rgx, response):
        # If you receive an ACK
        AckN = int(re.match(ack_rgx, response).group(1))
        print 'Receiver ACKed packet with SN: ', AckN

        Sm = (Sm + AckN + 1 - Sb) % N
        Sb = (AckN + 1) % N
        Sn = Sb
        needle = 0
        ackPacketsUpto(AckN)
        response = ''

    elif re.match(nack_rgx, response):
        # If you receive an NACK
        NackN = int(re.match(nack_rgx, response).group(1))
        print 'Receiver NACKed packet with SN: ', NackN

        if NackN != Sb:
            # ignore the nack if it's for the packet
            # with SN that is already == Base SN
            Sm = (Sm + NackN - Sb) % N
            Sb = NackN
            Sn = Sb
            needle = 0
            ackPacketsUpto((NackN - 1) % N)
        else:
            # if base number packet nacked,
            # resend from base number again
            needle = 0
        response = ''

    if needle < N:
        # transmit packets of window in order - Sb <= Sn <= Sm
        # mimic delay
        time.sleep(1)

        s.send(getPacket(Sn))
        Sn = (Sn + 1) % N
        needle += 1

    try:
        response += s.recv(1)
    except Exception, e:
        # to avoid blocking, conn will throw exception after a timeout
        pass
