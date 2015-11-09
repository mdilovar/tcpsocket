#!/usr/bin/env python

import socket, time, random, string, re, textwrap
from random import randint


TCP_IP = '127.0.0.1'
TCP_PORT = 11000
PACKET_SIZE = 20
PACKET_HEADER_SIZE = 5
MSG_HEADER_SIZE = 8

PACKETS = []


N  = 8 # window size
Rn = 0 # request number
Sn = 0 # sequence number
Sb = 0 # sequence base
Sm = 0 # sequence max
_sn = 0 # last assigned sn

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.settimeout(.1)


Sb = 0
Sm = N - 1

Rn_rgx = '^<rn(\d)>'

response = ''


def getPacket (Sn):
    global PACKETS, _sn
    #print 'debug: requested packet with sn: ', Sn
    #print 'debug: while current max sn is sm: : ', Sm
    #print 'debug: current packets len: ', len(PACKETS)
    while len(PACKETS) < N:
        # generate message and pack it
        msg = getMessage()
        new_packets = textwrap.wrap(msg, PACKET_SIZE)
        print "Message is broken into %s packet(s)" % (len(new_packets))
        for idx, packet in enumerate(new_packets):
            # stuff packet if it's not long enough
            while len(new_packets[idx]) < PACKET_SIZE:
                new_packets[idx] += '0'
            # add sequence number to packet
            new_packets[idx] = '<sn%s>%s' % (_sn % N, new_packets[idx])
            _sn += 1
        PACKETS += new_packets
    for packet in PACKETS:
        Sn_rgx = '^<sn(%s)>' % (Sn)
        if re.match(Sn_rgx, packet):
            print 'Sending packet # %s - %s' % (Sn,packet)
            return packet
    raise Exception ('Packet with sequence number %s not found in %s' % (Sn,PACKETS))

def ackPacketsUpto(Sn):
    global PACKETS
    upto_idx = 0
    for idx, packet in enumerate(PACKETS):
        Sn_rgx = '^<sn(%s)>' % (Sn)
        if re.match(Sn_rgx, packet):
            upto_idx = idx
            break
    print 'debug: before chopping: ', PACKETS
    print 'debug: sn: ', Sn
    PACKETS = PACKETS[upto_idx:]
    print 'debug: after chopping: ', PACKETS

def getMessage():
    msg_size = randint(1,5)
    msg_size *= PACKET_SIZE
    msg_size -= MSG_HEADER_SIZE
    msg = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(msg_size))
    # append headers to msg - length:message:end
    msg = '/mlen%s/%s' % ("%02d" % (len(msg),), msg)
    print 'Message is ready. Size (including headers): %s \nContent: %s' % (len(msg), msg)
    return msg

while True:
    #Repeat the following steps forever:

    print 'debug: Sb: %s | Sn: %s | Sm: %s | Rn: %s' % (Sb, Sn, Sm, Rn)
    print 'debug: res', response

    if re.match(Rn_rgx, response):
        #1. If you receive a request number where Rn > Sb
        Rn = int(re.match(Rn_rgx, response).group(1))
        print 'Receiver asked for packet with SN: ', Rn
        # if Rn > Sb:
        Sm = (Sm + (Rn - Sb)) % N
        Sb = Rn
        Sn += 1
        Sn %= N
        ackPacketsUpto(Sb)
        response = ''

    if True: #TODO: change the condition?
        #2.  If no packet is in transmission,
        #Transmit a packet where Sb <= Sn <= Sm.
        #Packets are transmitted in order.
        # mimic delay
        time.sleep(.1)
        # if not (Sb <= Sn <= Sm):
        #     Sn = Sb
        s.send(getPacket(Sn))
        Sn += 1
        Sn %= N

    try:
        response += s.recv(1)
    except Exception, e:
        # print 'debug: norec %s ' % e
        pass
