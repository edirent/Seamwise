// Full-joint, one-core adapter to the unmodified official GARI-NMS C kernel.
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <limits>
#include <stdexcept>
namespace py=pybind11;
using Bits=std::vector<uint8_t>;
extern "C" int ldpc_dec_msaa_quantum_serial_big_matrix_c(double*,int,int*,int,int,int*,int,int,double,int8_t*,int,int,int,int,int,int8_t*,double*);
struct Gari {
    int n,m,q,mx,nx,nz,rows,cols,rwidth,cwidth,iterations,ensemble,seed,schedule;
    double scale;
    std::vector<int> hrows,hcols,detector_order,marginal_faults;
    std::vector<int> swapped_rows;
    bool two_sector=false;
    std::vector<double> llr,score_weights;
    std::vector<std::vector<int>> detector_columns,logical_columns;
    std::vector<int8_t> target,estimate;
    std::vector<double> posterior;
    Gari(py::array_t<int,py::array::c_style|py::array::forcecast>hr,
         py::array_t<int,py::array::c_style|py::array::forcecast>hc,
         std::vector<double> l,std::vector<double>sw,std::vector<int>permutation,std::vector<int>faults,
         std::vector<std::vector<int>>d,std::vector<std::vector<int>>log,int nq,int xm,int xn,int zn,int it,int en,int sd,int sch,double sc):
         n(permutation.size()),m(d.size()),q(nq),mx(xm),nx(xn),nz(zn),iterations(it),ensemble(en),seed(sd),schedule(sch),scale(sc),detector_order(std::move(permutation)),marginal_faults(std::move(faults)),llr(std::move(l)),score_weights(std::move(sw)),detector_columns(std::move(d)),logical_columns(std::move(log)) {
        if(hr.ndim()!=2||hc.ndim()!=2||it<1||en<1||q<0)throw std::invalid_argument("GARI dimensions/budget");
        rows=hr.shape(0);rwidth=hr.shape(1);cols=hc.shape(0);cwidth=hc.shape(1);
        hrows.assign(hr.data(),hr.data()+hr.size());hcols.assign(hc.data(),hc.data()+hc.size());
        if(llr.size()!=size_t(cols)||score_weights.size()!=size_t(nx+nz)||marginal_faults.size()!=size_t(nx+nz)||logical_columns.size()!=size_t(m))throw std::invalid_argument("GARI map dimensions");
        target.resize(rows,1);estimate.resize(cols);posterior.resize(cols);
        swapped_rows=hrows;
        for(int i=0;i<n;++i){int source=i<n-mx?mx+i:i-(n-mx);std::copy_n(hrows.begin()+source*rwidth,rwidth,swapped_rows.begin()+i*rwidth);}
    }
    std::pair<Bits,Bits> decode(const Bits&s){
        if(s.size()!=size_t(n))throw std::invalid_argument("GARI syndrome length");
        for(int i=0;i<n;++i){if(s[detector_order[i]]>1)throw std::invalid_argument("GARI binary syndrome");target[i]=1-2*s[detector_order[i]];}
        std::fill(target.begin()+n,target.end(),1);
        if(two_sector){
            // The official fast stopping checks one monitored sector. Decode
            // both sectors with two correlated-graph passes, each retaining
            // ALL detector evidence and original joint fault priors. Resource
            // cost is explicitly 2*ensemble single-core kernel calls.
            auto normal_target=target;auto swapped_target=target;
            for(int i=0;i<n;++i)swapped_target[i]=normal_target[i<n-mx?mx+i:i-(n-mx)];
            Bits result(m,0);
            for(int sector=0;sector<2;++sector){
                int first=sector==0?0:nx,last=sector==0?nx:nx+nz;
                Bits selected(m,0);bool selected_valid=false;double selected_cost=std::numeric_limits<double>::infinity();
                for(int e=0;e<ensemble;++e){
                    std::fill(estimate.begin(),estimate.end(),0);std::fill(posterior.begin(),posterior.end(),0.);
                    auto&hr=sector==0?swapped_rows:hrows;auto&sy=sector==0?swapped_target:normal_target;
                    ldpc_dec_msaa_quantum_serial_big_matrix_c(llr.data(),iterations,hr.data(),rows,rwidth,hcols.data(),cols,cwidth,scale,sy.data(),seed+e,n,sector==0?n-mx:mx,schedule,1,estimate.data(),posterior.data());
                    Bits x(m,0),check(n,0);double cost=0;for(int k=first;k<last;++k)if(estimate[k]){x[marginal_faults[k]]^=1;cost+=score_weights[k];}
                    for(int j=0;j<m;++j)if(x[j])for(int i:detector_columns[j])check[i]^=1;
                    bool valid=true;for(int k=sector==0?0:mx;k<(sector==0?mx:n);++k)valid=valid&&(check[detector_order[k]]==s[detector_order[k]]);
                    if((valid&&!selected_valid)||(valid==selected_valid&&cost<selected_cost)){selected=std::move(x);selected_valid=valid;selected_cost=cost;}
                }
                for(int j=0;j<m;++j)result[j]^=selected[j];
            }
            Bits frame(q,0);for(int j=0;j<m;++j)if(result[j])for(int i:logical_columns[j])frame[i]^=1;return {frame,result};
        }
        Bits best(m,0);double bestscore=std::numeric_limits<double>::infinity();bool bestvalid=false;
        for(int e=0;e<ensemble;++e){
            std::fill(estimate.begin(),estimate.end(),0);std::fill(posterior.begin(),posterior.end(),0.);
            // Every decode uses the same declared independently restarted RNG
            // schedule; no stream leaks between syndromes or workers.
            ldpc_dec_msaa_quantum_serial_big_matrix_c(llr.data(),iterations,hrows.data(),rows,rwidth,hcols.data(),cols,cwidth,
                    scale,target.data(),seed+e,n,mx,schedule,0,estimate.data(),posterior.data());
            Bits x(m,0),check(n,0);double cost=0;
            for(int k=0;k<nx+nz;++k)if(estimate[k]){x[marginal_faults[k]]^=1;cost+=score_weights[k];}
            for(int j=0;j<m;++j)if(x[j])for(int i:detector_columns[j])check[i]^=1;
            bool valid=check==s;
            if((valid&&!bestvalid)||(valid==bestvalid&&cost<bestscore)){best=std::move(x);bestscore=cost;bestvalid=valid;}
        }
        Bits frame(q,0);for(int j=0;j<m;++j)if(best[j])for(int i:logical_columns[j])frame[i]^=1;
        return {frame,best};
    }
};
static py::array_t<uint8_t> out(const Bits&v){py::array_t<uint8_t>a(v.size());std::copy(v.begin(),v.end(),a.mutable_data());return a;}
PYBIND11_MODULE(_gari,m){
    py::class_<Gari>(m,"Gari")
       .def_readwrite("two_sector",&Gari::two_sector)
       .def(py::init<py::array_t<int,py::array::c_style|py::array::forcecast>,py::array_t<int,py::array::c_style|py::array::forcecast>,std::vector<double>,std::vector<double>,std::vector<int>,std::vector<int>,std::vector<std::vector<int>>,std::vector<std::vector<int>>,int,int,int,int,int,int,int,int,double>())
       .def("decode",[](Gari&g,py::array_t<uint8_t,py::array::c_style|py::array::forcecast>s){if(s.ndim()!=1)throw std::invalid_argument("GARI input rank");Bits input(s.data(),s.data()+s.size());std::pair<Bits,Bits>result;{py::gil_scoped_release release;result=g.decode(input);}return py::make_tuple(out(result.first),out(result.second));});
}
