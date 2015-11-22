import socket, time, random 

UDP_IP = "127.0.0.1"
UDP_PORT = 11000
MESSAGE = "Hello, World!"
TIMEOUT = 1.0
NUM_PINGS = 10


print "UDP target IP:", UDP_IP
print "UDP target port:", UDP_PORT


sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.settimeout(TIMEOUT)

minRTT = TIMEOUT
maxRTT = 0
avgRTT = 0
sumRTT = 0
numRTT = 0
lossRate = 0

sn = 1
while sn <= NUM_PINGS:
    time.sleep(random.uniform(0.5, 1))
    start = time.time()
    sock.sendto('PING   %s   %s ' % (sn, start), (UDP_IP, UDP_PORT))
    sn += 1
    try:
        message, address = sock.recvfrom(1024)
    except Exception,e:
        print 'Request timed out'
    else:
        print message
        end = time.time()
        RTT = end - start
        numRTT += 1
        sumRTT += RTT
        if RTT > maxRTT:
            maxRTT = RTT
        if RTT < minRTT:
          minRTT = RTT
        print 'RTT in seconds: %s' % RTT

if  numRTT != 0:
    avgRTT = sumRTT / numRTT
else:
    avgRTT = '-'
    minRTT = '-'
    maxRTT = '-'

lossRate = int (100 * float(( NUM_PINGS - numRTT )) / NUM_PINGS )


print 'Minimum RTT: %s' % minRTT
print 'Average RTT: %s' % avgRTT
print 'Maximum RTT: %s' % maxRTT
print 'Loss rate: %s%%' % lossRate
