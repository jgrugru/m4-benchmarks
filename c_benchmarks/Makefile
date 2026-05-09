CC := clang
CFLAGS := -O3 -mcpu=apple-m4 -Wall -Wextra -std=c11
BUILD := build
COMMON := common.c

# Detect Homebrew prefixes for libgmp and openssl@3.
GMP_PREFIX := $(shell brew --prefix gmp 2>/dev/null)
OPENSSL_PREFIX := $(shell brew --prefix openssl@3 2>/dev/null)

GMP_FLAGS := -I$(GMP_PREFIX)/include -L$(GMP_PREFIX)/lib -lgmp
OPENSSL_FLAGS := -I$(OPENSSL_PREFIX)/include -L$(OPENSSL_PREFIX)/lib -lcrypto

BENCHES := float_ops mandelbrot nbody fannkuch prime_sieve pidigits matmul_numpy sha256_mp

.PHONY: all clean
all: $(addprefix $(BUILD)/, $(BENCHES))

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/float_ops: float_ops.c $(COMMON) common.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ float_ops.c $(COMMON) -lm

$(BUILD)/mandelbrot: mandelbrot.c $(COMMON) common.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ mandelbrot.c $(COMMON) -lm

$(BUILD)/nbody: nbody.c $(COMMON) common.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ nbody.c $(COMMON) -lm

$(BUILD)/fannkuch: fannkuch.c $(COMMON) common.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ fannkuch.c $(COMMON)

$(BUILD)/prime_sieve: prime_sieve.c $(COMMON) common.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ prime_sieve.c $(COMMON) -lm

$(BUILD)/pidigits: pidigits.c $(COMMON) common.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ pidigits.c $(COMMON) $(GMP_FLAGS)

$(BUILD)/matmul_numpy: matmul_numpy.c $(COMMON) common.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ matmul_numpy.c $(COMMON) -framework Accelerate -lm

$(BUILD)/sha256_mp: sha256_mp.c $(COMMON) common.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ sha256_mp.c $(COMMON) $(OPENSSL_FLAGS) -lpthread

clean:
	rm -rf $(BUILD)
