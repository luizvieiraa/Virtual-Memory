#include <ctype.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum {
    PAGE_SIZE = 256,
    PAGE_COUNT = 256,
    FRAME_COUNT = 128,
    TLB_SIZE = 16,
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

struct tlb_entry {
    bool valid;
    unsigned int page;
    unsigned int frame;
    uint64_t last_used;
};

struct virtual_memory {
    int page_table[PAGE_COUNT];
    unsigned int frame_pages[FRAME_COUNT];
    unsigned char frames[FRAME_COUNT][PAGE_SIZE];
    unsigned int next_frame;
    unsigned int fifo_victim;
    bool use_lru;
    unsigned int recency[FRAME_COUNT];
    struct tlb_entry tlb[TLB_SIZE];
    bool tlb_use_lru;
    uint64_t clock;
    size_t translated;
    size_t page_faults;
    size_t tlb_hits;
};

static int find_tlb(const struct virtual_memory *memory, unsigned int page)
{
    for (unsigned int entry = 0; entry < TLB_SIZE; ++entry) {
        if (memory->tlb[entry].valid && memory->tlb[entry].page == page) {
            return (int)entry;
        }
    }
    return -1;
}

static void invalidate_tlb(struct virtual_memory *memory, unsigned int page)
{
    int entry = find_tlb(memory, page);
    if (entry != -1) {
        memory->tlb[entry].valid = false;
    }
}

static unsigned int insert_tlb(struct virtual_memory *memory,
                               unsigned int page, unsigned int frame)
{
    unsigned int victim = 0;
    for (unsigned int entry = 0; entry < TLB_SIZE; ++entry) {
        if (!memory->tlb[entry].valid) {
            victim = entry;
            break;
        }
        if (memory->tlb[entry].last_used < memory->tlb[victim].last_used) {
            victim = entry;
        }
    }
    memory->tlb[victim] = (struct tlb_entry){true, page, frame, memory->clock};
    return victim;
}

static unsigned int replacement_frame(const struct virtual_memory *memory)
{
    if (!memory->use_lru) {
        return memory->fifo_victim;
    }

    unsigned int victim = 0;
    for (unsigned int frame = 1; frame < FRAME_COUNT; ++frame) {
        if (memory->recency[frame] < memory->recency[victim]) {
            victim = frame;
        }
    }
    return victim;
}

static void record_access(struct virtual_memory *memory, unsigned int frame)
{
    /* Ranks run from least to most recent and stay bounded by FRAME_COUNT. */
    unsigned int previous = memory->recency[frame];
    for (unsigned int other = 0; other < memory->next_frame; ++other) {
        if (memory->recency[other] > previous) {
            --memory->recency[other];
        }
    }
    memory->recency[frame] = memory->next_frame - 1;
}

static bool translate_address(struct virtual_memory *memory, FILE *backing_store,
                              FILE *output, unsigned int address)
{
    unsigned int page = address / PAGE_SIZE;
    unsigned int offset = address % PAGE_SIZE;
    ++memory->clock;
    int entry = find_tlb(memory, page);
    int frame;
    if (entry != -1) {
        ++memory->tlb_hits;
        frame = (int)memory->tlb[entry].frame;
        if (memory->tlb_use_lru) {
            memory->tlb[entry].last_used = memory->clock;
        }
    } else {
        frame = memory->page_table[page];
    }

    if (frame == -1) {
        bool replacing = memory->next_frame == FRAME_COUNT;
        frame = (int)(replacing ? replacement_frame(memory) : memory->next_frame);
        if (fseek(backing_store, (long)(page * PAGE_SIZE), SEEK_SET) != 0) {
            fprintf(stderr, "Cannot seek to page %u in BACKING_STORE.bin\n", page);
            return false;
        }
        if (fread(memory->frames[frame], 1, PAGE_SIZE, backing_store) != PAGE_SIZE) {
            fprintf(stderr, "Cannot read complete page %u from BACKING_STORE.bin\n", page);
            return false;
        }
        if (replacing) {
            invalidate_tlb(memory, memory->frame_pages[frame]);
            memory->page_table[memory->frame_pages[frame]] = -1;
            if (!memory->use_lru) {
                memory->fifo_victim = (memory->fifo_victim + 1) % FRAME_COUNT;
            }
        } else {
            memory->recency[frame] = memory->next_frame;
            ++memory->next_frame;
        }
        memory->frame_pages[frame] = page;
        memory->page_table[page] = frame;
        ++memory->page_faults;
    }

    if (entry == -1) {
        entry = (int)insert_tlb(memory, page, (unsigned int)frame);
    }
    if (memory->use_lru) {
        record_access(memory, (unsigned int)frame);
    }

    unsigned int physical_address = (unsigned int)frame * PAGE_SIZE + offset;
    unsigned int byte = memory->frames[frame][offset];
    int value = byte < 128 ? (int)byte : (int)byte - 256;
    if (fprintf(output, "Virtual address: %u TLB: %d Physical address: %u Value: %d\n",
                address, entry, physical_address, value) < 0) {
        fprintf(stderr, "Cannot write correct.txt\n");
        return false;
    }
    ++memory->translated;
    return true;
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

    FILE *backing_store = fopen("BACKING_STORE.bin", "rb");
    if (backing_store == NULL) {
        fprintf(stderr, "Cannot open BACKING_STORE.bin\n");
        fclose(file);
        return EXIT_FAILURE;
    }

    struct virtual_memory memory = {0};
    memory.use_lru = strcmp(argv[2], "lru") == 0;
    memory.tlb_use_lru = strcmp(argv[3], "lru") == 0;
    for (unsigned int page = 0; page < PAGE_COUNT; ++page) {
        memory.page_table[page] = -1;
    }

    unsigned int address;
    size_t line = 1;
    enum address_result result;
    FILE *output = fopen("correct.txt", "w");
    if (output == NULL) {
        fprintf(stderr, "Cannot open correct.txt for writing\n");
        fclose(backing_store);
        fclose(file);
        return EXIT_FAILURE;
    }
    while ((result = read_address(file, &address)) == ADDRESS_OK) {
        if (!translate_address(&memory, backing_store, output, address)) {
            fclose(output);
            fclose(backing_store);
            fclose(file);
            return EXIT_FAILURE;
        }
        ++line;
    }
    fclose(file);
    fclose(backing_store);

    bool output_ok = true;
    if (result == ADDRESS_END && memory.translated != 0) {
        output_ok = fprintf(output,
            "Number of Translated Addresses = %zu\n"
            "Page Faults = %zu\n"
            "Page Fault Rate = %.3f\n"
            "TLB Hits = %zu\n"
            "TLB Hit Rate = %.3f\n",
            memory.translated, memory.page_faults,
            (double)memory.page_faults / memory.translated,
            memory.tlb_hits, (double)memory.tlb_hits / memory.translated) >= 0;
    }
    if (fclose(output) != 0) {
        output_ok = false;
    }
    if (!output_ok) {
        fprintf(stderr, "Cannot write correct.txt\n");
        return EXIT_FAILURE;
    }

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
