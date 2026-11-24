CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Wpedantic -O2
THREAD_FLAGS = -pthread

.PHONY: all clean

all: vm

vm: vm.c
	$(CC) $(CPPFLAGS) $(CFLAGS) $(THREAD_FLAGS) $(LDFLAGS) -o $@ $< $(LDLIBS)

clean:
	$(RM) vm vm.exe
