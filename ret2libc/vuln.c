#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Sisipkan gadget pop rdi ; ret secara eksplisit
void gadgets() {
    __asm__("pop %rdi\n\t"
            "ret\n\t");
}

void vuln() {
    char buffer[64];
    puts("Input:");
    gets(buffer);
}

int main() {
    vuln();
    return 0;
}
