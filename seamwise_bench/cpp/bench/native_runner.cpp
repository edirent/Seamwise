#include "seamwise/decoder.hpp"
#include <fstream>
#include <iostream>
// Simple versioned text protocol; model/sample I/O is outside online timing.
// SWB1 n m q blocks shots family persistent policy, then priors, weights,
// detector labels, each column (degree IDs, logical degree IDs), shot bits.
int main(int argc,char**argv){
    try{
        if(argc!=2){std::cerr<<"usage: native_runner MODEL.swb\n";return 2;}
        std::ifstream in(argv[1]);std::string magic,f,policy;int n,m,q,b,shots,persist;
        if(!(in>>magic>>n>>m>>q>>b>>shots>>f>>persist>>policy)||magic!="SWB1"||n<0||m<0||q<0||shots<0)throw std::runtime_error("SWB1 header");
        std::vector<double>p(m),w(m);seamwise::Support labels(n);std::vector<seamwise::Support>cols(m),logs(m);
        for(auto&v:p)in>>v;for(auto&v:w)in>>v;for(auto&v:labels)in>>v;
        for(int j=0;j<m;++j){int k;in>>k;if(k<0||k>n)throw std::runtime_error("column degree");cols[j].resize(k);for(auto&i:cols[j])in>>i;in>>k;if(k<0||k>q)throw std::runtime_error("logical degree");logs[j].resize(k);for(auto&i:logs[j])in>>i;}
        auto prep=std::chrono::steady_clock::now();seamwise::Decoder decoder(n,cols,logs,p,w,labels,b,f,persist,policy);
        decoder.observable_count=q;
        auto prep_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-prep).count();
        std::cerr<<"{\"preparation_ns\":"<<prep_ns<<",\"prepared_capacity_payload_bytes\":"<<decoder.prepared_bytes()<<"}\n";
        for(int k=0;k<shots;++k){seamwise::Bytes s(n);int bit;for(auto&v:s){if(!(in>>bit)||bit<0||bit>1)throw std::runtime_error("syndrome bit");v=bit;}
            auto t=std::chrono::steady_clock::now();auto r=decoder.decode(s);auto elapsed=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-t).count();
            std::cout<<"{\"shot\":"<<k<<",\"latency_ns\":"<<elapsed<<",\"frame\":[";for(size_t j=0;j<r.frame.size();++j){if(j)std::cout<<',';std::cout<<int(r.frame[j]);}std::cout<<"],\"valid\":"<<(decoder.model.apply(r.correction)==s?"true":"false")<<"}\n";
        }
    }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
