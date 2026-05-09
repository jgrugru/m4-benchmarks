/* SHA-256 fan-out across all CPU cores via pthreads + OpenSSL EVP. */

#include <openssl/evp.h>
#include <openssl/sha.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/sysctl.h>

#include "common.h"

#define WORK_PER_PROC 200000
#define DATA_SIZE 4096
#define HASH_LEN 32

typedef struct {
    long seed;
    unsigned char result;
} thread_arg_t;

static void sha256_once(const unsigned char *in, size_t inlen, unsigned char *out) {
    unsigned int outlen = 0;
    EVP_Digest(in, inlen, out, &outlen, EVP_sha256(), NULL);
}

static void *worker(void *p) {
    thread_arg_t *arg = (thread_arg_t *)p;
    unsigned char data[DATA_SIZE];
    memset(data, 0, DATA_SIZE);
    long seed = arg->seed;
    for (int i = 0; i < 8; i++) {
        data[i] = (unsigned char)((seed >> (i * 8)) & 0xff);
    }
    unsigned char h[HASH_LEN];
    sha256_once(data, DATA_SIZE, h);
    for (int i = 0; i < WORK_PER_PROC; i++) {
        sha256_once(h, HASH_LEN, h);
    }
    arg->result = h[0];
    return NULL;
}

static int cpu_count(void) {
    int n = 1;
    size_t sz = sizeof(n);
    if (sysctlbyname("hw.logicalcpu", &n, &sz, NULL, 0) != 0) {
        n = 1;
    }
    return n;
}

void run(void) {
    int n = cpu_count();
    pthread_t *th = malloc(sizeof(pthread_t) * (size_t)n);
    thread_arg_t *args = malloc(sizeof(thread_arg_t) * (size_t)n);
    if (!th || !args) {
        fprintf(stderr, "alloc fail\n");
        exit(1);
    }
    for (int i = 0; i < n; i++) {
        args[i].seed = i;
        if (pthread_create(&th[i], NULL, worker, &args[i]) != 0) {
            fprintf(stderr, "pthread_create fail\n");
            exit(1);
        }
    }
    for (int i = 0; i < n; i++) pthread_join(th[i], NULL);
    free(th);
    free(args);
}
