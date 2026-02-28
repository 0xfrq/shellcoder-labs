#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void vuln() {
    char buffer[64];

    printf("Enter data:\n");
    gets(buffer);   // intentionally

    printf("You entered: %s\n", buffer);
}

int main() {
    vuln();
    return 0;
}