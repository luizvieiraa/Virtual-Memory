#include <ctype.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum {
    PAGE_SIZE = 256,
    MAX_LOGICAL_ADDRESS = 65535
};

enum address_result {
    ADDRESS_OK,
    ADDRESS_END,
    ADDRESS_INVALID,
    ADDRESS_READ_ERROR
};

static enum address_result read_address(FILE *file, unsigned int *address)
{
    unsigned int value = 0;
    bool has_digit = false;
    bool has_trailing_space = false;
    bool has_input = false;
    int character;

    while ((character = fgetc(file)) != EOF && character != '\n') {
        has_input = true;
        if (isspace(character)) {
            has_trailing_space = has_digit;
            continue;
        }

        if (character < '0' || character > '9' || has_trailing_space) {
            return ADDRESS_INVALID;
        }

        unsigned int digit = (unsigned int)(character - '0');
        if (value > (MAX_LOGICAL_ADDRESS - digit) / 10) {
            return ADDRESS_INVALID;
        }

        value = value * 10 + digit;
        has_digit = true;
    }

    if (character == EOF) {
        if (ferror(file)) {
            return ADDRESS_READ_ERROR;
        }
        if (!has_input) {
            return ADDRESS_END;
        }
    }

    if (!has_digit) {
        return ADDRESS_INVALID;
    }

    *address = value;
    return ADDRESS_OK;
}

static bool valid_policy(const char *policy)
{
    return strcmp(policy, "fifo") == 0 || strcmp(policy, "lru") == 0;
}

static void print_translation(unsigned int address)
{
    printf("Address: %u Page: %u Offset: %u\n",
           address, address / PAGE_SIZE, address % PAGE_SIZE);
}

int main(int argc, char *argv[])
{
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <address file> <fifo|lru> <fifo|lru>\n", argv[0]);
        return EXIT_FAILURE;
    }

    if (!valid_policy(argv[2])) {
        fprintf(stderr, "Invalid page replacement policy '%s': expected fifo or lru\n", argv[2]);
        return EXIT_FAILURE;
    }
    if (!valid_policy(argv[3])) {
        fprintf(stderr, "Invalid TLB replacement policy '%s': expected fifo or lru\n", argv[3]);
        return EXIT_FAILURE;
    }

    FILE *file = fopen(argv[1], "rb");
    if (file == NULL) {
        fprintf(stderr, "Cannot open address file '%s'\n", argv[1]);
        return EXIT_FAILURE;
    }

    unsigned int address;
    size_t line = 1;
    enum address_result result;
    while ((result = read_address(file, &address)) == ADDRESS_OK) {
        print_translation(address);
        ++line;
    }
    fclose(file);

    if (result == ADDRESS_READ_ERROR) {
        fprintf(stderr, "Cannot read address file '%s' at line %zu\n", argv[1], line);
        return EXIT_FAILURE;
    }
    if (result == ADDRESS_INVALID) {
        fprintf(stderr, "Invalid logical address in '%s' at line %zu: expected an integer from 0 to %u\n",
                argv[1], line, (unsigned int)MAX_LOGICAL_ADDRESS);
        return EXIT_FAILURE;
    }
    if (line == 1) {
        fprintf(stderr, "Address file '%s' is empty\n", argv[1]);
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
