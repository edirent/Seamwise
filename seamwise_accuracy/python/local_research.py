"""Offline bounded beam prototype. Inputs never include logical ground truth."""
import numpy as np
from gf2 import LogicalImage,span,reduce

def indices(w):
 out=[]
 while w:
  b=w&-w;out.append(b.bit_length()-1);w^=b
 return np.array(out,dtype=int)
def pool(d,l,weights,limit=128):
 image=LogicalImage(d,l);unique={}
 for logical,witness in image.relations:
  ids=indices(witness);key=witness
  if key not in unique:unique[key]=dict(logical=logical,indices=ids,base_cost=float(weights[ids].sum()))
 ordered=sorted(unique.values(),key=lambda r:(r['base_cost'],r['logical'],tuple(r['indices'])))
 basis={};chosen=[];seen=set()
 for r in ordered:
  v=reduce(r['logical'],basis)
  if v and len(chosen)<limit:
   basis[v.bit_length()-1]=v;chosen.append(r);seen.add(tuple(r['indices']))
 for r in ordered:
  if len(chosen)>=limit:break
  if tuple(r['indices']) not in seen:chosen.append(r);seen.add(tuple(r['indices']))
 return chosen,dict(available_logical_rank=image.rank,pool_logical_rank=len(span(r['logical'] for r in chosen)),pool_size=len(chosen),pool_limit=limit)
def beam(incumbent,l,weights,moves,K=16,depth=2):
 def sig(x):return bytes(np.asarray(l@x%2,dtype=np.uint8))
 def select(candidates):
  ordered=sorted(candidates,key=lambda x:(float(weights@x),x.tobytes()));out=[];classes=set();seen=set()
  # Reserve half of K for distinct classes; remaining slots retain low cost mass.
  for x in ordered:
   s=sig(x)
   if s not in classes:out.append(x);classes.add(s);seen.add(x.tobytes())
   if len(out)>=max(1,K//2):break
  for x in ordered:
   if len(out)>=K:break
   if x.tobytes() not in seen:out.append(x);seen.add(x.tobytes())
  return out
 current=[np.asarray(incumbent,dtype=np.uint8).copy()];generated=1
 for level in range(depth):
  proposed={x.tobytes():x for x in current}
  for x in current:
   for move in moves:
    z=x.copy();z[move['indices']]^=1;proposed.setdefault(z.tobytes(),z);generated+=1
  current=select(list(proposed.values()))
 return current,dict(generated_attempts=generated,depth=depth,K=K,maximum_generated_attempts=1+len(moves)*(1+K)*(depth>1) if depth==2 else None)
