# Hue
## Reversing - 450
> Flag = WhiteHat{sha1(upper(key))}

## Overview
The target is an 64-bit exe file statically linked to the MFC library. It is an MFC dialog-based application that has the **WhiteHat icon** and an **about menu** appended to the dialog's system menu.

The dialog has just 2 controls: an edit control and a push button. We tried several test input and hit the button but no message shown up. The button click just makes the application exit. We also tried to set breakpoints at **GetWindowTextW** and **GetDlgItemTextW** to find out when the application get text from the edit control but we still had no chance.

The challenge here is to find the program logic with no clue of how the input text is processed. We may start by investigating the *mainCRTStartup*, then *AfxWinMain*, then the inherited *CWinApp::InitInstance* ... However, we will mention another approach in this writeup: the application GUI components are hints to discover the program structure. 

## The dialog event handlers
To understand the program, we have to find the dialog event handlers. For MFC dialog-based applications, there are 2 main entry-points:
* The inherited **CDialog::OnInitDialog**.
* The **GetThisMessageMap** static method that returns the **AFX_MSGMAP** structure (you can read source code of *BEGIN_MESSAGE_MAP*, *END_MESSAGE_MAP* and *DECLARE_MESSAGE_MAP* macros for more information). Here's the **AFX_MSGMAP** structure definition:

```C
struct AFX_MSGMAP_ENTRY
{
	UINT nMessage;   // windows message
	UINT nCode;      // control code or WM_NOTIFY code
	UINT nID;        // control ID (or 0 for windows messages)
	UINT nLastID;    // used for entries specifying a range of control id's
	UINT_PTR nSig;       // signature type (action) or pointer to message #
	AFX_PMSG pfn;    // routine to call (or special value)
};

struct AFX_MSGMAP
{
	const AFX_MSGMAP* (PASCAL* pfnGetBaseMap)();
	const AFX_MSGMAP_ENTRY* lpEntries;
};

```

### Finding the inherited CDialog::OnInitDialog
Our approach is based on the **WhiteHat icon** of this application. A dialog has no icon (more precisely, it has the default application icon) until we explicitly set new icon for it by sending **WM_SETICON** (*0x0080*) message. So we fire up WinDbg and set breakpoint at **SendMessageW**:
```
bp User32!SendMessageW ".if (rdx==0x80) {} .else {gc;}"
```
The breakpoint is hit twice, first with **ICON_BIG** (0x1) parameter, then **ICON_SMALL** (0x0). Here's the call stack when the breakpoint is hit:
```
USER32!SendMessageW
0x2408
0x16525
...
USER32!SendMessageW
0x2421
0x16525
```
Trace back to offset **0x2048** and offset **0x2421** we can easily find out that the inherited **CDialog::OnInitDialog** is at **0x2300**.

We can use the same method with the **about menu**. This menu is appended to the dialog's system menu. To do so the dialog should call the *GetSystemMenu* function. By setting breakpoint at **User32!GetSystemMenu** we can also trace back to **CDialog::OnInitDialog** at **0x2300**.

Actually all those setups are not neccessary to by placed at **OnInitDialog**, but they must be called after the dialog has been created (maybe in some event handlers). We would still use the same approach in that case.

### Finding the message map
We try clicking the about menu ("*About WhiteHatContest...*") and an about dialog will show up. This means that the application should call one of the following functions:
* DialogBoxParamW
* DialogBoxIndrectParamW
* CreateDialogParamW
* CreateDialogIndrectParamW

We set breakpoints on all those function calls then try clicking the about menu again. Breakpoint is hit at **CreateDialogIndirectParamW**
```
USER32!CreateDialogIndirectParamW
0x173c7
0x1696d
0x16b1b
0x16d11
0x2543
0x22426
0x23f30
0x1df0a
0x1ea30
USER32!TranslateMessageEx+0x2a1
```
**0x2543** is the lowest address in the call stack. We might guess that other addresses are from the MFC static library. From **0x2543** we can easily navigate to **0x2480** where the **WM_SYSCOMMAND**'s handler starts. From there we just "Jump to xref" to locate the message map structure of the dialog at **0x211290**:

```asm
.rdata:0140211288                 dq offset Message_Map
.rdata:0140211290 Message_Map     dd WM_SYSCOMMAND
.rdata:0140211294                 dd 0
.rdata:0140211298                 dd 0
.rdata:014021129C                 dd 0
.rdata:01402112A0                 dq 1Fh
.rdata:01402112A8                 dq offset sub_140002480 ; OnSysCommand
.rdata:01402112B0                 dd WM_PAINT
.rdata:01402112B4                 dd 0
.rdata:01402112B8                 dd 0
.rdata:01402112BC                 dd 0
.rdata:01402112C0                 dq 13h
.rdata:01402112C8                 dq offset sub_1400025A0 ; OnPaint
.rdata:01402112D0                 dd WM_QUERYDRAGICON
.rdata:01402112D4                 dd 0
.rdata:01402112D8                 dd 0
.rdata:01402112DC                 dd 0
.rdata:01402112E0                 dq 29h
.rdata:01402112E8                 dq offset sub_1400026D0 ; OnQueryDragIcon
.rdata:01402112F0                 dd WM_COMMAND
.rdata:01402112F4                 dd 0
.rdata:01402112F8                 dd 3E9h                 ; ID of the OK button
.rdata:01402112FC                 dd 3E9h                 ; ID of the OK button
.rdata:0140211300                 dq 3Ah
.rdata:0140211308                 dq offset sub_1400026E0 ; OnOkCommand
.rdata:0140211310                 dd 0                    ; End of the structure, zero-filled
.rdata:0140211314                 dd 0
.rdata:0140211318                 dd 0
.rdata:014021131C                 dd 0
.rdata:0140211320                 dd 0
.rdata:0140211324                 dq 0
```
By doing a quick investigation on all those message handlers we figure out that they just do the "default" (MFC generated) tasks. The OK button handler just sends the message **WM_NCDESTROY** to the dialog, no input text check here. So we just need to focus on the inherited **CDialog::OnInitDialog** at **0x2300**. 

## The main logic
Back to **CDialog::OnInitDialog** at **0x2300**, there are just one small suspicous code snippet:

```asm
.text:01400023EE                 mov     r9, [rdi+158h]  ; lParam
.text:01400023F5                 mov     edx, WM_SETICON ; Msg
.text:01400023FA                 lea     r8d, [rdx-7Fh]  ; wParam
.text:01400023FE                 mov     rcx, [rdi+40h]  ; hWnd
.text:0140002402                 call    cs:SendMessageW
.text:0140002408                 mov     r9, [rdi+158h]  ; lParam
.text:014000240F                 xor     r8d, r8d        ; wParam
.text:0140002412                 mov     edx, WM_SETICON ; Msg
.text:0140002417                 mov     rcx, [rdi+40h]  ; hWnd
.text:014000241B                 call    cs:SendMessageW
.text:0140002421                 mov     [rsp+68h+var_30], 0
.text:014000242A                 lea     rcx, off_140210DA8 ; Method table of WTF class
.text:0140002431                 mov     [rsp+68h+wtf_obj], rcx
.text:0140002436                 lea     rcx, LibFileName ; "User32.dll"
.text:014000243D                 call    cs:__imp_LoadLibraryW
.text:0140002443                 mov     [rsp+68h+var_20], rax
.text:0140002448                 mov     [rsp+68h+var_28], 0
.text:0140002450                 lea     rcx, [rsp+68h+wtf_obj]
.text:0140002455                 call    WTF_DoJob
.text:014000245A                 nop
```
The application initializes an instance of an unknown class that we named **WTF**. This class has method table at **0x210DA8**. From there we can find all methods and analyze the data structure of the class. Here's the pseudo code of the **WTF** class declaration:

```C
int WTF::DoJob() {
	WCHAR dirName[MAX_PATH];
	WCHAR tmp[MAX_PATH];

	m_Path = dirName;
	if (GetFolderName(dirName)) return 1;
	wcscpy_s(tmp, MAX_PATH, dirName);	// Store the directory name for later use
	EncryptString(dirName);
	DoCheck();
	if (m_OK)
		// Then displaying the flag using User32!MessageBoxW		
	
	return 0;
}

int WTF::EncryptString(LPWSTR input) {
	if (wcslen(input) != 42) return 1;
	for (int i = 0; i < 42; i++) {
		int j = i % 9;
		if (j == 0) j = 1;
		switch (i % j) {
		case 1:
			input[i] ^= 0xCC00; break;
		case 4:
			input[i] -= 0x100; break;
		case 6:
			input[i] = ~input[i]; break;
		case 8:
			input[i] -= 0x3C01; break;
		default:
			input[i] ^= 0xC3CC; break;
		}
	}
	for (int i = 0; i < 42; i++) {
		WCHAR delta = 0;
		for (int j = 42; j > 0; j -= 2)
			delta += i % j + i % (j - 1);
		input[i] += delta;
	}
	return 0;
}

void WTF::DoCheck() {
	DoCheck_00_20();
	DoCheck_01_19();
	DoCheck_02_18();
	DoCheck_03_17();
	DoCheck_04_16();
	DoCheck_05_15();
	DoCheck_06_14();
	DoCheck_07_13();
	DoCheck_08_12();
	DoCheck_09_11();
	DoCheck_10();
}

void WTF::DoCheck_00_20() {
	DWORD *buf = (DWORD*)m_Path;
	m_OK = (buf[0] == 0xC41EC3B7 && buf[20] == 0xCDCFC54C);
}

void WTF::DoCheck_01_19() {
	DWORD *buf = (DWORD*)m_Path;
	m_OK = (buf[1] == 0xC472C448 && buf[19] == 0xC57CC58A);
}

void WTF::DoCheck_02_18() {
	DWORD *buf = (DWORD*)m_Path;
	m_OK = (buf[2] == 0xC4B7C494 && buf[18] == 0xC597C592);
}

void WTF::DoCheck_03_17() {
	DWORD *buf = (DWORD*)m_Path;
	m_OK = (buf[3] == 0xC4F6C465 && buf[17] == 0xC5CB01A2);
}

void WTF::DoCheck_04_16() {
	DWORD *buf = (DWORD*)m_Path;
	m_OK = (buf[4] == 0xC532C513 && buf[16] == 0xC5E0C5E2);
}

void WTF::DoCheck_05_15() {
	DWORD *buf = (DWORD*)m_Path;
	m_OK = (buf[5] == 0xCDADC4D5 && buf[15] == 0xC586C5F0);
}

void WTF::DoCheck_06_14() {
	DWORD *buf = (DWORD*)m_Path;
	m_OK = (buf[6] == 0xCDCEC576 && buf[14] == 0xCE46C5F9);
}

void WTF::DoCheck_07_13() {
	DWORD *buf = (DWORD*)m_Path;
	m_OK = (buf[7] == 0xC5AE00ED && buf[13] == 0xC60FC59E);
}

void WTF::DoCheck_08_12() {
	DWORD *buf = (DWORD*)m_Path;
	m_OK = (buf[8] == 0xCE15C5BC && buf[12] == 0x152C5F9);
}

void WTF::DoCheck_09_11() {
	DWORD *buf = (DWORD*)m_Path;
	m_OK = (buf[9] == 0xC57EC5D7 && buf[11] == 0xC613C594);
}

void WTF::DoCheck_10() {
	DWORD *buf = (DWORD*)m_Path;
	m_OK = (buf[10] == 0xC5FCC5F1);
}
```

The logic is quite simple, key is an Unicode string of 42 characters. It is encrypted using *xor*, *add* (*subtract*) and *not* operations. The encrypted buffer is then compared every 4 bytes with a pre-calculated buffer. This class also has a decrypt method to inverse the encrypt operation.

## Key generation
Here are the key and flag generated by our [Python script](https://github.com/duc-le/ctf-writeups/blob/master/2015_WhiteHat_GrandPrix_Qual/RE450/gen.py):

> Key: {94076F571DB19F9494E01C08BB1962F732089666}

> Flag: WhiteHat{ef0d95c8e810ac272a1362236f02866bf51e72a0}

A final note on flag submission: although the key is a MSVC Unicode string (16-bit each character), we should UTF-8 encode it before getting sha1 checksum or else we would receive "wrong flag" message from the scoreboard!

