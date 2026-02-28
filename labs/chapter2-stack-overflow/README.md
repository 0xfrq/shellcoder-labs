# Chapter 2 Lab – Stack Overflow

Goal: overwrite the return address.

Steps:

1 Compile program

make

2 Run it

./vuln

3 Crash it

python3 -c "print('A'*200)" | ./vuln

4 Inspect with gdb

gdb ./vuln

run

5 Find EIP control

ulimit -c unlimited
gdb vuln core


[![Open in Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?repo=0xfrq/shellcoder-labs)