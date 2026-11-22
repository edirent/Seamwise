import ctypes,gc,resource
from common import atomic

def rss():
 import psutil
 return psutil.Process().memory_info().rss

def audit_memory(decoder,detectors,ids,dest,summary):
 gc.collect();lib=ctypes.CDLL(None);available=hasattr(lib,'seamwise_alloc_begin');audit=dict(corpus_shots=len(ids),allocation_counts=[],soak=[],baseline_rss_bytes=summary['baseline_rss_bytes'],prepared_rss_bytes=summary['prepared_rss_bytes'],scope='calling-thread glibc requests, resident process pages, owned capacity payloads; no live-byte claim')
 if available:
  lib.seamwise_alloc_begin.restype=None;lib.seamwise_alloc_end.restype=None
  for symbol in ['seamwise_alloc_calls','seamwise_alloc_bytes']:getattr(lib,symbol).restype=ctypes.c_uint64
 peak=0
 for cycle in range(2):
  for idx in ids:
   if available:lib.seamwise_alloc_begin()
   decoder.decode(detectors[idx])
   if available:
    lib.seamwise_alloc_end()
    if cycle==0:audit['allocation_counts'].append(dict(shot=int(idx),calls=lib.seamwise_alloc_calls(),requested_bytes=lib.seamwise_alloc_bytes()))
   if hasattr(decoder,'stats'):peak=max(peak,int(decoder.stats().get('peak_candidate_payload_lower_estimate_bytes',0)))
  for _ in ids:decoder.decode(detectors[ids[0]])
  audit['soak'].append(dict(cycle=cycle,independent_shots=len(ids),repeated_shots=len(ids),rss_bytes=rss()));atomic(dest/'memory.partial.json',audit)
 if hasattr(decoder,'memory'):audit['native_capacity']=dict(decoder.memory())
 elif hasattr(decoder,'backend') and hasattr(decoder.backend,'diagnostics'):
  d=decoder.backend.diagnostics();audit['native_capacity']=dict(prepared_capacity_payload_bytes=d['prepared_capacity_payload_bytes'],workspace_capacity_payload_bytes=sum(s['workspace_capacity_payload_bytes'] for s in d['solvers']))
 audit.update(high_water_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,max_candidate_dense_payload_lower_estimate_bytes=peak);atomic(dest/'memory.json',audit);return audit
