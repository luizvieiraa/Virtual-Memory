CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Wpedantic -O2
THREAD_FLAGS = -pthread
PYTHON ?= python3

.PHONY: all clean test package

all: vm

vm: vm.c
	$(CC) $(CPPFLAGS) $(CFLAGS) $(THREAD_FLAGS) $(LDFLAGS) -o $@ $< $(LDLIBS)

clean:
	$(RM) vm vm.exe

test: vm
	$(PYTHON) tests/test_vm.py --executable ./vm

package:
	$(PYTHON) scripts/package.py
