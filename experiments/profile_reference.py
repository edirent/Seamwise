"""Separate structural-work diagnostic; profiled times are not benchmark times."""
import cProfile,pstats,sys,json
from pathlib import Path
import numpy as np
from scipy import sparse
here=Path(__file__).resolve().parent;sys.path.insert(0,str(here/'research'))
import decoders
from bp_huf import BPHUF
model='bb144_p0.015_B4';path=here/'data'/model
raw=np.load(path/'samples.npz');a=np.load(path/'metadata_arrays.npz')
d=sparse.load_npz(path/'D.npz');l=sparse.load_npz(path/'L.npz')
summary=[];outputs=[]
for mode in [False,True]:
 decoders.make_solver=lambda matrix,p,engine:BPHUF(matrix,p,mode)
 st=decoders.Stack(d,l,a['p'],a['detector_blocks'],4,'BPSW' if mode else 'BPHUF');st.prepare(['repair1'])
 pr=cProfile.Profile();xs=[];pr.enable()
 for s in raw['detectors'][:8]:xs.append(st.decode(s.astype(np.uint8),'repair1')[0])
 pr.disable();tag='persistent' if mode else 'rebuild';pr.dump_stats(str(here/(tag+'_profile.pstats')))
 stats=pstats.Stats(pr)
 summary.append(dict(mode=tag,model=model,shots=8,basis_insertion_calls=sum(v[1] for k,v in stats.stats.items() if k[2]=='insert' and k[0].endswith('algebra.py'))))
 with (here/(tag+'_profile.txt')).open('w') as f:pstats.Stats(pr,stream=f).sort_stats('cumtime').print_stats(40)
 outputs.append(np.array(xs))
assert np.array_equal(*outputs)
(here/'profile_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary))
