/* Linux/glibc diagnostic-only malloc-request counter. Never preload in timing. */
#include <stddef.h>
#include <stdint.h>
extern void *__libc_malloc(size_t);
extern void *__libc_calloc(size_t,size_t);
extern void *__libc_realloc(void*,size_t);
extern void __libc_free(void*);
/* This library is LD_PRELOADed. Initial-exec TLS avoids __tls_get_addr inside
 * malloc: loading a native extension can grow the DTV using malloc itself. */
static __thread int enabled __attribute__((tls_model("initial-exec")))=0;
static __thread uint64_t calls __attribute__((tls_model("initial-exec")))=0;
static __thread uint64_t bytes __attribute__((tls_model("initial-exec")))=0;
static __thread uint64_t frees __attribute__((tls_model("initial-exec")))=0;
void seamwise_alloc_begin(void){calls=bytes=frees=0;enabled=1;}
void seamwise_alloc_end(void){enabled=0;}
uint64_t seamwise_alloc_calls(void){return calls;}
uint64_t seamwise_alloc_bytes(void){return bytes;}
uint64_t seamwise_alloc_frees(void){return frees;}
void *malloc(size_t n){if(enabled){++calls;bytes+=n;}return __libc_malloc(n);}
void *calloc(size_t n,size_t m){if(enabled){++calls;bytes+=n*m;}return __libc_calloc(n,m);}
void *realloc(void*p,size_t n){if(enabled){++calls;bytes+=n;}return __libc_realloc(p,n);}
void free(void*p){if(enabled && p)++frees;__libc_free(p);}
