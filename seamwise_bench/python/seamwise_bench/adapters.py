"""Preparation-only Python adapters; production Seamwise loops are native."""
import numpy as np
from .common import ROOT,HIST,UnsupportedModel

def supports(a):
    a=a.tocsc()
    return [a.indices[a.indptr[j]:a.indptr[j+1]].astype(int).tolist() for j in range(a.shape[1])]

class Native:
    validity="CORRECTION_AUDITED_EXTERNALLY"
    def __init__(self,model,cfg,audit=False):
        import sys
        if cfg.get("family","bphuf")!="huf" and cfg.get("iterations",30)<1:raise ValueError("native BP iterations must be positive")
        if cfg.get("build"):sys.path.insert(0,str(ROOT/cfg["build"]))
        import _native
        p=model["p"]
        self.backend=_native.Decoder(model["d"].shape[0],supports(model["d"]),supports(model["l"]),p.tolist(),np.log((1-p)/p).tolist(),
                                    model["labels"].astype(int).tolist(),model["meta"]["blocks"],cfg.get("family","bphuf"),
                                    cfg.get("persistent",True),cfg.get("policy","repair1"),audit,cfg.get("iterations",30),cfg.get("order",0),cfg.get("dense_terminal",False))
        self.backend.observable_count=model["l"].shape[0]
        self.resolved_config=dict(cfg,iterations=cfg.get("iterations",30),bp_schedule="parallel",bp_scale=.625,bp_precision="float64",residual_LLR_clip=[-100,100],terminal_policy="reference canonical column solve")
    def decode(self,s): return self.backend.decode(s)

class PythonReference:
    validity="CORRECTION_AUDITED_EXTERNALLY"
    def __init__(self,model,cfg,audit=False):
        import decoders
        from huf import HUF
        from bp_huf import BPHUF
        if cfg.get("family","bphuf") not in ["huf","bphuf"]:raise ValueError("frozen Python oracle supports HUF and BPHUF only")
        if cfg.get("iterations",30)!=30:raise ValueError("frozen BP oracle has exactly 30 iterations")
        self.model=model;self.policy=cfg.get("policy","repair1");self.objects=[]
        def factory(a,p,unused):
            h=(BPHUF if cfg.get("family","bphuf")=="bphuf" else HUF)(a,p,cfg.get("persistent",True))
            if audit:
                # Instrument a derived oracle function in memory. The frozen
                # historical source stays untouched; timing uses the original.
                import inspect,textwrap,types,huf
                code=textwrap.dedent(inspect.getsource(HUF._decode))
                code=code.replace("clocks=self.weights.copy();sizes=[];unions=0;activations=0","clocks=self.weights.copy();sizes=[];unions=0;activations=0;semantic=[]")
                code=code.replace("new=eligible(s)-s.inserted","new=eligible(s)-s.inserted\n            semantic.append([a,b,a,len(members[a])]+sorted(new))")
                code=code.replace("    return x","    self.semantic_histories.append(semantic)\n    return x")
                namespace={};exec(code,vars(huf),namespace)
                h.semantic_histories=[];h._decode=types.MethodType(namespace["_decode"],h)
            self.objects.append(h);return h
        saved=decoders.make_solver;decoders.make_solver=factory
        try:
            self.stack=decoders.Stack(model["d"],model["l"],model["p"],model["labels"],model["meta"]["blocks"],"frozen_reference")
            self.stack.prepare([self.policy])
        finally:decoders.make_solver=saved
        self.last=None
    def decode(self,s):
        x,fb,events=self.stack.decode(s,self.policy);self.last=(fb,events)
        return np.asarray(self.model["l"]@x%2,dtype=np.uint8),x

class External:
    def __init__(self,model,cfg,audit=False):
        self.model=model;self.name=cfg["kind"]
        self.validity="UNAVAILABLE" if self.name=="tesseract" else "CORRECTION_AUDITED_EXTERNALLY"
        if self.name=="tesseract":
            invisible=np.asarray(model["d"].getnnz(axis=0)).ravel()==0
            logical=np.asarray(model["l"].getnnz(axis=0)).ravel()!=0
            if np.any(invisible&logical&(model["p"]>.5)):raise UnsupportedModel("Tesseract upstream does not apply detector-invisible p>0.5 logical-frame offsets; exact normalization is required")
            import stim
            from tesseract_decoder import tesseract as te
            kwargs={k:v for k,v in cfg.items() if k not in ["name","kind"]}
            self.backend=te.TesseractDecoder(te.TesseractConfig(dem=stim.DetectorErrorModel.from_file(model["path"]/"detector_model.dem"),**kwargs))
            c=self.backend.config
            self.resolved_config={k:getattr(c,k) for k in ["det_beam","pqlimit","beam_climbing","no_revisit_dets","merge_errors","det_penalty","det_orders","sparsify_errors","sparsify_base_degree","sparsify_max_degree","sparsify_reactivate_limit"]}
        elif self.name=="relay":
            import relay_bp
            kwargs={k:v for k,v in cfg.items() if k not in ["name","kind","precision"]}
            cls=getattr(relay_bp,"RelayDecoder"+cfg.get("precision","F64"))
            self.backend=cls(model["d"],error_priors=model["p"].astype(np.float64),**kwargs)
            defaults=dict(alpha=None,alpha_iteration_scaling_factor=1.0,gamma0=.1,data_scale_value=None,max_data_value=None,pre_iter=80,num_sets=300,set_max_iter=60,gamma_dist_interval=[-.24,.66],explicit_gammas=None,stop_nconv=1,stopping_criterion="nconv",logging=False,seed=0,min_log_prior_ratio=None)
            defaults.update(kwargs);self.resolved_config=defaults
        else:
            from ldpc import BpLsdDecoder,BpOsdDecoder
            kwargs=dict(error_channel=model["p"].tolist(),max_iter=cfg.get("iterations",30),bp_method="minimum_sum",ms_scaling_factor=.625,schedule=cfg.get("schedule","parallel"),omp_thread_count=1)
            order=cfg.get("order",2)
            if self.name=="lsd":self.backend=BpLsdDecoder(model["d"],lsd_method="LSD_CS" if order else "LSD_0",lsd_order=order,**kwargs)
            elif self.name=="osd":self.backend=BpOsdDecoder(model["d"],osd_method="OSD_CS" if order else "OSD_0",osd_order=order,**kwargs)
            else:raise ValueError(f"unknown external backend {self.name}")
            self.resolved_config={k:v for k,v in kwargs.items() if k!="error_channel"}
            self.resolved_config.update(order=order,input_vector_type="syndrome",precision="float64",damping=None,error_channel_source="frozen metadata_arrays.npz:p")
    def decode(self,s):
        x=np.asarray(self.backend.decode(s.astype(bool) if self.name=="tesseract" else s),dtype=np.uint8).copy()
        if self.name=="tesseract":return x,None
        return np.asarray(self.model["l"]@x%2,dtype=np.uint8),x

def make(model,cfg,audit=False):
    if cfg["kind"]=="gari":
        from .gari import GariAdapter
        return GariAdapter(model,cfg,audit)
    return (Native if cfg["kind"]=="native" else PythonReference if cfg["kind"]=="python" else External)(model,cfg,audit)
