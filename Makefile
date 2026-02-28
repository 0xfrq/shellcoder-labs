all:
	gcc labs/chapter2-stack-overflow/vuln.c -o vuln \
	-fno-stack-protector \
	-z execstack \
	-no-pie \
	-m32

clean:
	rm -f vuln