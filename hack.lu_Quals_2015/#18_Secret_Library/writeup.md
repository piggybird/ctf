#Secret Library

##by TheJH (Reversing) 

> Books are a great thing. And since libraries are a big amount of books you can read in one place, they're great, too.

> But this secret library some guys started is a bit different. You have to know the exact title of a book to get it, you can't look around. So you have to know another person in the library who knows some book titles or you won't be able to read anything. A bit like an invite-only library.

> This whole thing seems weird. Could you poke around and try to figure out what they're up to? If you could grab one of their books, that would be awesome.

> connect to school.fluxfingers.net:1527


##The main logic
The target is a 64-bit ELF file. Since its logic is quite simple I won't explain in details the assembly code.
Here's the pseudo code of the main communication:

```C
special_input = 0;              // stored at 0x603394
char input_buffer[9];
char file_name[9];

while (true) {
    input = read_user_input();  // Read user input into input_buffer and
                                // return the number represented by input_buffer as hex string
                                // Only '0'-'9', 'A'-'F' are accepted.
    switch (input) {
    case 0x952A7224:
        if (special_input == 0x278F03): {
            display("sure! the head librarian ...\n");
            display_current_dir();          // Display content of current directory
        }
        break;
    case 0xF1140B88:
        display("you want me to show you a book?....\n");
        file_name[0] = 0;
        for (int i = 0; i < 2; i++) {
            if (read_user_input() & 1)
                strcat(file_name, input_buffer);
            else: {
                display("pah! we don't have books ....\n");
                break;
            }
        }
        display_file_content(file_name);
        break;
    case 0xF39ED0C:
        convert_bin_to_hex();
        break;
    case 0x420B65F7:
        display("alright, show me your library card.\n");
        special_input = read_user_input();
        if (special_input == 0x278F03) {
            display("oh, you say you're the head librarian? prove it!\n");
            // Here's is the guessing game
            // we have 10 tries to guess the random number from "/dev/urandom"
            if (failed_to_guess)
                special_input = 0;
        }
        display("alright!\n");
    }
}
```

So here are the steps we should follow to get the flag:

* Enter "**420B65F7**", the program responses: "**alright, show me your library card.**"
* Enter "**00278F03**", the program responses: "**oh, you say you're the head librarian? prove it!**"
* Playing the guessing game and win the game to ensure that **special_input == 0x278F03**
* Enter "**952A7224**", then the program will tell us the content of the current directory and of course the name of the flag file which contains hopefully only hex characters.
* Enter "**F1140B88**", the program response: "**you want me to show you a book? ...**", then we enter the flag file name twice as hex string, then we have a flag.

But how can we win the guessing game? Well I may say it's *impossible*!

## rt_sigprocmask
The trick here is the function at **0x400AF6** that converts an 8-bit hex character into the number it represents:
```C
int hex_char_to_number(char ch) {
    if (ch < '0')
        return -1;
    if (ch <= '9')
        return (ch - '0');  // '0' -> '9'
    if (ch < 'A') {
        // Tricky
        //ch = [0x3A - 0x40]
        rt_sigprocmask(SIG_BLOCK, NULL, (sigset_t*)0x603397, sizeof(sigset_t));
    } else if (ch <= 'F')
        return (ch - 'A' + 10); // 'A' -> 'F'
    else
        return -1;
}
```
If we enter any character in range from 0x3A (':') to 0x40 ('@') the program will call **rt_sigprocmask** to return the current blocked signals to offset **0x603397**. Since there is usually no blocked signal, the 8 bytes starting at **0x603397** will be zero-filled.

The interesting part is the **special_input** variable which is stored at **0x603394**. Since this ELF is little-endian, the **rt_sigprocmask** call will overwrite the most significant byte of **special_input** and set it to zero.

##Solution
So here's how we should enter to get the flag:

* Enter "**420B65F7**", the program responses: "**alright, show me your library card.**".
* Enter "**XY278F03**", where **XY** could be any two hex characters ('0'-'F','A'-'9') except "00". The program responses: "**alright!**" and set the value of **special_input** to **XY278F03**.
* Enter a string that contains at least one character in range 0x3A-0x40 to trigger the **rt_sigprocmask**. The most significant byte of **special_input** will be set to zero. This means that **secial_input == 0x00278F03**
* Enter "**952A7224**", then the program will show us the name of the flag file.
* Enter "**F1140B88**", then enter two hex strings representing the name of the flag file to get the flag.

Here's our example input while connecting to **school.fluxfingers.net:1527**:

* **420B65F7**
* **12278F03**
* **12278F0@**
* **952A7224**

And we have the following responses from server:

```
hi! this is the secret library. if you want me to speak to you, you need to know the magic words.
alright, show me your library card.
alright!
warning: invalid hexchar '@'
you do know the magic words, right?
sure! the head librarian is allowed to know about all the books!
------------
16F7F4D391F030CF
------------
```

Then we know the flag file name is "16F7F4D391F030CF". We connect to **school.fluxfingers.net:1527** again and enter the following sequences:

* **F1140B88**
* **16F7F4D3**
* **91F030CF**

Here's how the server responses:

```
hi! this is the secret library. if you want me to speak to you, you need to know the magic words.
you want me to show you a book? certainly! just tell me the name of the book.
oh, yes, we have that! here you go...
flag{our_secret_is_that_we_really_just_have_this_one_book}

====================
```

So the flag is **flag{our_secret_is_that_we_really_just_have_this_one_book}**
