"""Offline exact GF(2) column elimination and logical-image certificates."""
import numpy as np

def column_bits(a):
 a=a.tocsc();return [sum(1<<int(i) for i in a.indices[a.indptr[j]:a.indptr[j+1]]) for j in range(a.shape[1])]
def mask(v):return sum(1<<int(i) for i in np.flatnonzero(v))
def reduce(v,basis):
 while v:
  p=v.bit_length()-1
  if p not in basis:return v
  v^=basis[p]
 return 0
def span(vectors):
 basis={}
 for v in vectors:
  v=reduce(v,basis)
  if v:basis[v.bit_length()-1]=v
 return basis
class LogicalImage:
 def __init__(self,d,l):
  self.m=d.shape[1];db,lb=column_bits(d),column_bits(l);self.detector_basis={};self.logical_basis={};self.relations=[]
  for j,(v,logical) in enumerate(zip(db,lb)):
   witness=1<<j
   while v:
    pivot=v.bit_length()-1
    if pivot not in self.detector_basis:
     self.detector_basis[pivot]=(v,logical,witness);break
    b,ll,ww=self.detector_basis[pivot];v^=b;logical^=ll;witness^=ww
   if not v:
    self.relations.append((logical,witness))
    while logical:
     pivot=logical.bit_length()-1
     if pivot not in self.logical_basis:self.logical_basis[pivot]=(logical,witness);break
     ll,ww=self.logical_basis[pivot];logical^=ll;witness^=ww
  self.detector_rank=len(self.detector_basis);self.rank=len(self.logical_basis)
 def witness(self,b):
  v=mask(b) if not isinstance(b,int) else b;w=0
  while v:
   p=v.bit_length()-1
   if p not in self.logical_basis:return None
   ll,ww=self.logical_basis[p];v^=ll;w^=ww
  return np.array([(w>>j)&1 for j in range(self.m)],dtype=np.uint8)
 def exposed(self,d,l,clusters,b):
  vectors=[]
  for cols in clusters:
   if not cols:continue
   local=LogicalImage(d[:,cols],l[:,cols]);vectors += [v[0] for v in local.logical_basis.values()]
  basis=span(vectors);return dict(rank=len(basis),fix_direction_in_span=not bool(reduce(mask(b),basis)),cluster_count=len(clusters))
