#Zoo
##by TheJH (Reversing) 

> Instead of sitting in the classroom, let's go to the zoo today and look at some strange animals!
 You'll need a license key for entering though. Can you make one?

> connect to school.fluxfingers.net:1532

Due to a silly coding bug I didn't succeed to get the flag from the server on time, however I still make a writeup for this cool challenge.

## The SIGILL handler
The program starts by installing the handler for SIGILL then requiring user name and license code. It reads those information from *stdout* (not from stdin as usual) and do the checking.
The SIGILL handler code is quite interesting:

```asm
.text:00400083           mov     esp, 0FFFFE000h
.text:00400088           mov     eax, 13               ; rt_sigaction
.text:0040008D           mov     edi, 4                ; SIGILL
.text:00400092           mov     rsi, offset _4001A7   ; pointer to struct sigaction
.text:0040009C           mov     edx, 0
.text:004000A1           mov     r10d, 8
```

The address **0x4001A7** is the location of the ```struct sigaction``` provided by the program.

```c
struct sigaction {
	__sighandler_t sa_handler;
	unsigned long sa_flags;
	__sigrestore_t sa_restorer;
	sigset_t sa_mask;		/* mask last for extensibility */
};
```

Let's have a look at this data structure:

```asm
.text:004001A7 _4001A7   dq offset _40028C             ; handler function
.text:004001AF           dq 44000004h                  ; flags
.text:004001B7           dq offset _400271             ; restorer
```

The flags value **0x44000004** has **SA_SIGINFO** bit (0x00000004) turned on indicating that the function at **0x40028C** is a sigaction function with the following prototype:

```c
void (*_sa_sigaction)(int signum, struct siginfo *info, void *context);
```

Let's dig deeper:
```asm
.text:0040028C           add     rdx, 0A8h             ; rdx -> context, (rdx + 0xA8) -> the value of 
															   ; rip that raises the signal
.text:00400293           mov     rax, [rdx]            ; rax = value of rip that raises the signal
.text:00400296           mov     ebx, 0FFFC0F00h       ; store the previous rip where SIGILL were raised
.text:0040029B           cmp     [rbx], rax
.text:0040029E           mov     [rbx], rax
.text:004002A1           jnz     short _4002A8         ; rdx -> cs
.text:004002A3           add     qword ptr [rdx], 7    ; skip 7 bytes to the next instruction
.text:004002A7           retn
.text:004002A8 _4002A8:                              
.text:004002A8           add     rdx, 10h              ; rdx -> cs
.text:004002AC           xor     qword ptr [rdx], 12h  ; switch between x86 mode and x64 mode
.text:004002B0           retn
```

So for each instruction that raises **SIGILL**, this handler switches between x86 mode and x64 mode and also changes privileges (by XORing the **cs** segment register with **0x12**), then executes that instruction again. If SIGILL is still raised then the handler skips 7 bytes to go to the next instruction.

## The fork call
After reading user name and license code, the program invokes the **fork** call:
```asm
.text:00400260           mov     eax, 57
.text:00400265           syscall                       ; fork
.text:00400267           test    eax, eax
.text:00400269           jz      _4001C7               ; is child process, goto _4001C7
.text:0040026F _40026F:                                
.text:0040026F           jmp     short _40026F         ; infinite loop for parent process
```

Then the parent process goes to the infinite loop at **0x40026F**, while the child process continues its work explained by the following pseudo code:

```c
ppid = getppid();							// Get parent process ID
ptrace(PTRACE_ATTACH, ppid, NULL, NULL);	// Attach to parent process
wait4(ppid, NULL, 0, NULL);					// Wait until the parent process breaks.
ptrace(PTRACE_POKEUSR,
  	ppid,
	offsetof(struct user, regs.eip),
	0x04002B1);								// Write 0x4002B1 into register eip of the parent process
ptrace(PTRACE_DETACH, ppid, NULL, NULL);
```

So the child process just changes the register **eip** of the parent process to **0x4002B1**. The parent process then continues its execution from **0x4002B1**.

## The license code checking
The license code checking is explained by the pseudo code below:

```c
char *license;				// Liscense code is stored here
char *name;					// Name stored here
ev = eventfd(0, EFD_NONBLOCK | EFD_SEMAPHORE);	// Initialize the eventfd
DWORD f1 = (*(DWORD*)name) ^ 0x0023002B ^ (*(DWORD*)license);

DWORD prev_x = 0;
DWORD prev_y = 0;
char *s = license + 3;
do {
	DWORD s0 = ((DWORD)s[0] + 0xE0) & 0x3F);
	DWORD s1 = ((DWORD)s[1] + 0xE0) & 0x3F);
	DWORD s2 = ((DWORD)s[2] + 0xE0) & 0x3F);
	DWORD sum = (s0 << 12) | (s2 << 6) ^ s1;
	x = sum & 0x1FF;						// The lower 9-bit
	y = sum >> 9;							// The higher 9-bit
	s += 3;
	dx = abs(x - prev_x);
	dy = abs(y - prev_y);
	if (dx == 0) {
		QWORD chk = 0;
		for (int i = 0; i < 16; i += 2)
			chk += *(WORD*)(name + i);		// Get name's checksum
		chk &= 0xFFFF;						// Get the lower 16-bit
		DWORD H1 = (chk & 0xFF + 0x100);
		DWORD H2 = (chk >> 8 + 0x100);

		QWORD h = (H1 ^ prev_x) | (H2 ^ prev_y);
		write(ev, &h, 8);					// Write value of h to ev
		break;								// Now check the result
	}
	else {
		prev_x = x;
		prev_y = y;
		QWORD h = 1;
		if (dx | dy == 3 && dx ^ dy == 3)
			h = 0;
		if (dx & dy & 0xFFFFFFFC)
			h = 2;
		write(ev, &h, 8);
	}
} while (dx != 0);

// Check the result
QWORD h;
if (f1 || read(ev, &h, 8) == 8)
	display("nope, that is not valid\n");
else
	display_flag();
```

For each 3 characters from the license the program calculates the value of **x** and **y** and performs the check based on those values and the values calculated from the the previous iteration.

The program only displays flag if **f1 == 0** and the last read of **ev** returns error.

> If the eventfd counter is zero at the time of the call to **read**, then the call either blocks until the counter becomes nonzero (at which time, the **read** proceeds as described above) or fails with the error EAGAIN if the file descriptor has been made nonblocking.


Here are our targets:

* to make **f1 == 0**: We just need to generate the first 4 bytes of the license code by simple XOR operations.
* to make the program always **write** the value of **0x0** (QWORD) to **ev**.

  
There are 2 locations the program writes to **ev**. Let's examine the first location, when **dx == 0**:
```c
DWORD H1 = (chk & 0xFF + 0x100); 	// H1 and H2 are generated from user name's checksum
DWORD H2 = (chk >> 8 + 0x100);
QWORD h = (H1 ^ prev_x) | (H2 ^ prev_y); 
write(ev, &h, 8);
```

For the value written to **ev** being equal zero we should have **H1 == prev_x** and **H2 == prev_y**. So the last values of **x** and **y** can be generated from name's checksum.

Let's examine the 2nd location of the **write** operation, when **dx > 0**:
```c
prev_x = x;
prev_y = y;
QWORD h = 1;
if (dx | dy == 3 && dx ^ dy == 3)
	h = 0;
if (dx & dy & 0xFFFFFFFC)
	h = 2;
write(ev, &h, 8);
```

We realize that there are few combinations of (dx, dy) that will cause the value of **0x0** (QWORD) written to **ev**:

 * (dx, dy) = (1, 2)
 * (dx, dy) = (2, 1)
 * (dx, dy) = (3, 0)
 
## Generating license code from name
The first 4 bytes of license can be easily generated:

```c
char *license;
char *name;		// Name stored here

*(DWORD*)license = *(DWORD*)name ^ 0x0023002B;
```

The remain of the license is generated as described below:

* Step 1: Initially prev_x = 0, prev_y = 0
* Step 2: Generate 3 license characters so that **x == prev_x + dx**, **y == prev_y + dy**, where (dx, dy) can be one of the following values:
  * (dx, dy) = (1, 2)
  * (dx, dy) = (2, 1) 
  * (dx, dy) = (3, 0)
* Step 3: If we have **x == H1** and **y == H2**: just replicate the last 3 characters of the license and we finish. Otherwise back to step 2

Let's assume:

* A is the number of times (dx, dy) == (1, 2)
* B is the number of times (dx, dy) == (2, 1)
* C is the number of times (dx, dy) == (3, 0)

We should solve the following equation:

* A + 2B + 3C = H1
* 2A + B = H2

That's where **z3** comes to play!

## The license generation code
We use Python and z3 to create our license generation. Here's the [source file](https://github.com/duc-le/ctf-writeups/blob/master/2015_hack.lu_CTF/%2324_Zoo/gen.py)



Please note that for some names we cannot find the appropriated license code.

Below is an example of the succeeded generation:

> hello hndlpcngfdlnhg!

> starting the license checker for you...

> your name: your license code: 

> flag{this is flag, plz submit me}

> wrapper: read from child

So the flag is **flag{this is flag, plz submit me}**
