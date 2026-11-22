#pragma once
#include "decoder.hpp"
#include <cmath>
#include <set>
#include <unordered_set>
namespace seamwise {
struct AccuracyConfig {
 std::string init_family="bphuf",band_family="bphuf",selection="cost";
 int iterations=30,band_iterations=30,order=0,radius=1,K=1,depth=2,max_calls=2;
 double scale=.625,damping=0,weak_gap=.5;
 bool serial=false,adaptive=false,ensemble=false,audit=false,joint=false;
};
struct Proposal {Bytes x,logical;double cost=0;};
struct AccuracyEvent {
 int radius=0,seam=0,accessible_faults=0,pool_rank=0,generated_rank=0,classes=0,attempts=0;
 bool bp_converged=false,accepted=false,logical_changed=false,escalate=false;
 double oldcost=0,newcost=0,gap=0;
 Bytes before_frame,after_frame,incumbent_signature;
 std::vector<Proposal> candidates;
};
struct AccuracyPlan {Window win;std::vector<Support>moves;std::unique_ptr<LocalSolver>secondary;int rank=0,seam=0;};
struct AccuracyDecoder {
 Decoder base;AccuracyConfig cfg;
 std::map<int,std::vector<AccuracyPlan>>plans;
 std::vector<AccuracyEvent>events;
 Bytes initial_correction;
 int solver_calls=0,escalations=0,generated_attempts=0,accepted_updates=0,higher_cost_updates=0,logical_updates=0;
 uint64_t peak_candidate_payload=0;
 AccuracyDecoder(int n,std::vector<Support>d,std::vector<Support>l,std::vector<double>p,std::vector<double>w,Support labels,int blocks,AccuracyConfig c,std::map<int,std::vector<std::vector<Support>>>moves):
  base(n,std::move(d),std::move(l),std::move(p),std::move(w),std::move(labels),blocks,c.init_family,true,c.joint?"joint":"cut",c.audit,c.iterations,c.order,false),cfg(c){
  if(cfg.K<1||cfg.K>16||cfg.depth<1||cfg.depth>2||cfg.max_calls<1||cfg.max_calls>2)throw std::invalid_argument("bounded search settings");
  if(cfg.selection!="cost"&&cfg.selection!="class_mass")throw std::invalid_argument("selection policy");
  if(cfg.joint&&(cfg.radius!=2||cfg.adaptive))throw std::invalid_argument("joint control uses the full radius2 region");
  for(auto*s:base.solvers())configure_bp(*s,cfg.scale,cfg.damping,cfg.serial);
  std::vector<int>radii=cfg.adaptive?std::vector<int>{1,2}:std::vector<int>{cfg.radius};
  for(int radius:radii){
   if(radius<1||radius>2)throw std::invalid_argument("radius");int band=0;
   for(int seam=2;seam<base.blocks;seam+=2){
    Support cols,rows,touched(base.model.n);
    for(int j=0;j<base.model.m;++j)if(base.owner[j]>=std::max(0,seam-radius)&&base.owner[j]<std::min(base.blocks,seam+radius)){cols.push_back(j);for(int i:base.model.columns[j])touched[i]=1;}
    for(int i=0;i<base.model.n;++i)if(touched[i])rows.push_back(i);
    AccuracyPlan plan;plan.seam=seam;plan.win=base.window(std::move(cols),std::move(rows));
    if(plan.win.solver){
     plan.win.solver=std::make_unique<LocalSolver>(plan.win.solver->model,cfg.band_family,true,cfg.audit,cfg.band_iterations,cfg.order);
     configure_bp(*plan.win.solver,cfg.scale,cfg.band_family=="bphuf"?cfg.damping:0,cfg.serial);
     if(cfg.ensemble&&!cfg.adaptive){plan.secondary=std::make_unique<LocalSolver>(plan.win.solver->model,"bphuf",true,cfg.audit,cfg.band_iterations,0);configure_bp(*plan.secondary,cfg.scale==.625?.8:.625,0,false);}
    }
    if(moves.count(radius)&&band<int(moves[radius].size()))plan.moves=moves[radius][band];++band;
    if(!plan.win.solver&&!plan.moves.empty())throw std::invalid_argument("moves for empty band");
    Basis logical_basis;
    for(size_t k=0;k<plan.moves.size();++k){
     const auto&move=plan.moves[k];if(!std::is_sorted(move.begin(),move.end())||std::adjacent_find(move.begin(),move.end())!=move.end())throw std::invalid_argument("kernel indices sorted unique");
     Bytes vector(plan.win.columns.size());for(int j:move){if(j<0||j>=int(vector.size()))throw std::invalid_argument("kernel index");vector[j]=1;}
     auto parity=plan.win.solver->model.apply(vector);if(std::any_of(parity.begin(),parity.end(),[](auto x){return x;}))throw std::invalid_argument("invalid detector-kernel move");
     auto logical=signature(plan,vector);Support bits;for(int i=0;i<int(logical.size());++i)if(logical[i])bits.push_back(i);logical_basis.insert(bits,k);
    }
    plan.rank=logical_basis.pivots.size();plans[radius].push_back(std::move(plan));
   }
  }
 }
 Bytes signature(const AccuracyPlan&p,const Bytes&x)const{
  Bytes logical(base.observable_count);for(size_t j=0;j<x.size();++j)if(x[j])for(int q:base.logical[p.win.columns[j]])logical[q]^=1;return logical;
 }
 double cost(const AccuracyPlan&p,const Bytes&x)const{double sum=0;for(size_t j=0;j<x.size();++j)sum+=base.model.weights[p.win.columns[j]]*x[j];return sum;}
 static std::string key(const Bytes&x){return std::string(reinterpret_cast<const char*>(x.data()),x.size());}
 static bool less(const Proposal&a,const Proposal&b){return a.cost<b.cost||(a.cost==b.cost&&a.x<b.x);}
 Proposal proposal(const AccuracyPlan&p,Bytes x)const{double c=cost(p,x);auto l=signature(p,x);return Proposal{std::move(x),std::move(l),c};}
 std::vector<Proposal>retain(std::vector<Proposal>all){
  std::sort(all.begin(),all.end(),less);std::vector<Proposal>out;std::set<Bytes>classes,used;
  for(const auto&x:all)if(!classes.count(x.logical)){out.push_back(x);classes.insert(x.logical);used.insert(x.x);if(int(out.size())>=std::max(1,cfg.K/2))break;}
  for(const auto&x:all){if(int(out.size())>=cfg.K)break;if(!used.count(x.x)){out.push_back(x);used.insert(x.x);}}
  return out;
 }
 AccuracyEvent repair(AccuracyPlan&p,Bytes&x,int radius){
  AccuracyEvent e;e.radius=radius;e.seam=p.seam;e.accessible_faults=p.win.columns.size();e.pool_rank=p.rank;
  Bytes old;for(int j:p.win.columns)old.push_back(x[j]);auto incumbent=proposal(p,old);e.oldcost=incumbent.cost;
  if(cfg.audit){e.before_frame=base.frame(x);e.incumbent_signature=incumbent.logical;}
  auto target=p.win.solver->model.apply(old);Bytes z;
  if(cfg.joint&&cfg.band_family==cfg.init_family&&cfg.band_iterations==cfg.iterations){z=old;e.bp_converged=last_bp_converged(*base.global);}
  else{z=p.win.solver->decode(target);++solver_calls;e.bp_converged=last_bp_converged(*p.win.solver);}
  if(p.win.solver->model.apply(z)!=target)throw std::runtime_error("invalid inner proposal");
  std::vector<Proposal>set={incumbent,proposal(p,z)};e.attempts=1;
  if(p.secondary&&solver_calls<cfg.max_calls&&(!e.bp_converged||set[0].logical==set[1].logical)){
   auto extra=p.secondary->decode(target);++solver_calls;++e.attempts;if(p.secondary->model.apply(extra)!=target)throw std::runtime_error("invalid ensemble proposal");set.push_back(proposal(p,std::move(extra)));
  }
  std::unordered_set<std::string>seen;std::vector<Proposal>unique;
  for(auto&v:set)if(seen.insert(key(v.x)).second)unique.push_back(std::move(v));set=std::move(unique);
  if(cfg.K>1&&!p.moves.empty())for(int depth=0;depth<cfg.depth;++depth){
   std::vector<Proposal>expanded=set;seen.clear();for(const auto&c:set)seen.insert(key(c.x));
   for(const auto&current:set)for(const auto&move:p.moves){Bytes next=current.x;for(int j:move)next[j]^=1;++e.attempts;if(seen.insert(key(next)).second)expanded.push_back(proposal(p,std::move(next)));}
   peak_candidate_payload=std::max(peak_candidate_payload,uint64_t(expanded.size())*uint64_t(old.size()));set=retain(std::move(expanded));
  }
  // Incumbent is always considered once; duplicate configurations carry no extra mass.
  bool has_old=false;for(const auto&v:set)has_old|=v.x==old;if(!has_old)set.push_back(incumbent);
  Basis generated;std::map<Bytes,std::vector<int>>classes;
  for(int i=0;i<int(set.size());++i){classes[set[i].logical].push_back(i);if(cfg.audit){Support change;for(int q=0;q<int(incumbent.logical.size());++q)if(incumbent.logical[q]!=set[i].logical[q])change.push_back(q);generated.insert(change,i);}}
  e.classes=classes.size();e.generated_rank=generated.pivots.size();std::sort(set.begin(),set.end(),less);
  Proposal best=set.front();e.gap=set.size()>1?set[1].cost-set[0].cost:0;
  if(cfg.selection=="class_mass"){
   classes.clear();for(int i=0;i<int(set.size());++i)classes[set[i].logical].push_back(i);double best_score=-1;Bytes chosen;
   for(const auto&[logical,ids]:classes){double score=0;for(int id:ids)score+=std::exp(-(set[id].cost-set.front().cost));bool tie=std::abs(score-best_score)<=1e-12;
    if(score>best_score+1e-12||(tie&&logical==incumbent.logical)){best_score=score;chosen=logical;}
   }
   for(const auto&v:set)if(v.logical==chosen){best=v;break;}
   e.accepted=best.x!=old;
  }else e.accepted=best.cost<incumbent.cost-1e-10;
  e.newcost=e.accepted?best.cost:incumbent.cost;e.logical_changed=e.accepted&&best.logical!=incumbent.logical;
  if(e.accepted){if(p.win.solver->model.apply(best.x)!=target)throw std::runtime_error("invalid selected proposal");for(size_t j=0;j<best.x.size();++j)x[p.win.columns[j]]=best.x[j];++accepted_updates;higher_cost_updates+=best.cost>incumbent.cost+1e-10;logical_updates+=e.logical_changed;}
  e.escalate=!e.bp_converged||e.classes<2||e.gap<cfg.weak_gap;generated_attempts+=e.attempts;
  if(cfg.audit)e.after_frame=base.frame(x);
  if(cfg.audit)e.candidates=std::move(set);return e;
 }
 Result decode(const Bytes&s){
  if(s.size()!=size_t(base.model.n)||std::any_of(s.begin(),s.end(),[](auto b){return b>1;}))throw std::invalid_argument("binary syndrome dimensions");
  solver_calls=escalations=generated_attempts=accepted_updates=higher_cost_updates=logical_updates=0;peak_candidate_payload=0;events.clear();
  if(cfg.audit){for(auto*solver:base.solvers()){solver->counts={};solver->histories.clear();solver->last_llr.clear();}for(auto&[r,ps]:plans)for(auto&p:ps){if(p.win.solver){p.win.solver->counts={};p.win.solver->histories.clear();p.win.solver->last_llr.clear();}if(p.secondary){p.secondary->counts={};p.secondary->histories.clear();p.secondary->last_llr.clear();}}}
  Result out;out.correction=cfg.joint?base.joint(s):base.cut(s,out.fallback);if(cfg.audit)initial_correction=out.correction;bool escalate=false;int first=cfg.adaptive?1:cfg.radius;
  for(auto&p:plans[first]){if(!p.win.solver){escalate|=cfg.adaptive;continue;}if(solver_calls>=cfg.max_calls)break;auto e=repair(p,out.correction,first);escalate|=e.escalate;if(cfg.audit)events.push_back(std::move(e));}
  if(cfg.adaptive&&escalate)for(auto&p:plans[2])if(p.win.solver&&solver_calls<cfg.max_calls){++escalations;auto e=repair(p,out.correction,2);if(cfg.audit)events.push_back(std::move(e));}
  if(base.model.apply(out.correction)!=s)throw std::runtime_error("invalid full syndrome");out.frame=base.frame(out.correction);return out;
 }
 uint64_t prepared_bytes()const{uint64_t total=base.prepared_bytes();for(const auto&[r,ps]:plans)for(const auto&p:ps){total+=(p.win.columns.capacity()+p.win.rows.capacity())*sizeof(int);if(p.win.solver)total+=p.win.solver->model.storage_bytes();if(p.secondary)total+=p.secondary->model.storage_bytes();for(const auto&m:p.moves)total+=m.capacity()*sizeof(int);}return total;}
 uint64_t workspace_bytes(){uint64_t total=0;for(auto*s:base.solvers())total+=s->workspace_bytes();for(auto&[r,ps]:plans)for(auto&p:ps){if(p.win.solver)total+=p.win.solver->workspace_bytes();if(p.secondary)total+=p.secondary->workspace_bytes();}return total;}
};
}
