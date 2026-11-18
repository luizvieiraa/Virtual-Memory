#include <errno.h>
#include <stdio.h>
#include <stdlib.h>

enum {
    PAGE_SIZE = 256,
    MAX_LOGICAL_ADDRESS = 65535
};

static void print_translation(unsigned int address)
{
    printf("Address: %u Page: %u Offset: %u\n",
           address, address / PAGE_SIZE, address % PAGE_SIZE);
}

int main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <logical address>\n", argv[0]);
        return EXIT_FAILURE;
    }

    char *end;
    errno = 0;
    long address = strtol(argv[1], &end, 10);
    if (errno == ERANGE || end == argv[1] || *end != '\0' ||
        address < 0 || address > MAX_LOGICAL_ADDRESS) {
        fprintf(stderr, "Invalid logical address: %s\n", argv[1]);
        return EXIT_FAILURE;
    }

    print_translation((unsigned int)address);
    return EXIT_SUCCESS;
}
