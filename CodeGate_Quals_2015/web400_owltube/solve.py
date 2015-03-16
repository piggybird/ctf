import urllib

def xs(s1,s2):
    return ''.join(chr(ord(a) ^ ord(b)) for a,b in zip(s1,s2))

cipher = 'ts3llI/++FD5ERSx3So+v6MyDy6t7cshLKyPmhVk1m14GCSnvU4wc6SF0nhpns9c5uxzaQwZvH17WxbptQLxKeKuNN1qZFoEUhgUcXjqUdw='
cipher=cipher.decode('base64')
print 'Len cipher: %d' % len(cipher)

b1 = '{"u": "xxxx3", "'
nb1 = '{"u": "admin"} "'
iv = cipher[0:16]

b4 = 'ccccccccccccc"}\x01'
nb4 = 'ccccccccccccc"}1'
c3 = cipher[48:48+16]

niv = xs(b1, xs(nb1,iv))
nc3 = xs(b4, xs(nb4,c3))

ncipher = niv + cipher[16:48] + nc3 + cipher[48+16:]
print 'Len ncipher: %d' % len(ncipher)
ncipher = ncipher.encode('base64')
print ncipher

from Crypto.Cipher import AES
from Crypto import Random
BS = AES.block_size
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[0:-ord(s[-1])]
SECRET_KEY='1234567890123456'
aes = AES.new(SECRET_KEY, AES.MODE_CBC, iv)


