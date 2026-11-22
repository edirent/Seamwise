/* Diagnostic interposer contract, compiled separately from decoder binaries. */
#include <stdlib.h>
#include <stdint.h>
#include <dlfcn.h>
#include <assert.h>
#include <stdio.h>
int main(void){
    void (*begin)(void)=dlsym(RTLD_DEFAULT,"seamwise_alloc_begin");
    void (*end)(void)=dlsym(RTLD_DEFAULT,"seamwise_alloc_end");
    uint64_t (*calls)(void)=dlsym(RTLD_DEFAULT,"seamwise_alloc_calls");
    uint64_t (*bytes)(void)=dlsym(RTLD_DEFAULT,"seamwise_alloc_bytes");
    uint64_t (*frees)(void)=dlsym(RTLD_DEFAULT,"seamwise_alloc_frees");
    assert(begin && end && calls && bytes && frees);
    /* Resolve the malloc family before enabling the counter. */
    void *p=malloc(8),*q=calloc(1,8);p=realloc(p,16);free(p);free(q);
    begin();p=malloc(20);q=calloc(5,8);p=realloc(p,80);free(p);free(q);end();
    assert(calls()==3 && bytes()==140 && frees()==2);
    puts("PASS: 3 requests, 140 requested bytes, 2 explicit frees");
}
