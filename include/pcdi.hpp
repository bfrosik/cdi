
#ifndef pcdi_hpp
#define pcdi_hpp

#include "vector"

class Params;
class Reconstruction;
namespace af {
    class array;
}

class PartialCoherence
{
private:
    Params *params;
    int * roi;
    int * kernel;
    std::vector<int> triggers;
    int algorithm;
    bool normalize;
    int iteration_num;
public:
    PartialCoherence(Params * params, int * roi, int * kernel, std::vector<int> partial_coherence_trigger, int alg, bool pcdi_normalize, int pcdi_iter);
    std::vector<int> GetTriggers();
    int GetTriggerAlgorithm();
    int * GetRoi();
    int * GetKernel();
    void OnTrigger(af::array abs_image, af::array abs_data, Reconstruction *rec);
    af::array DeconvLucy(af::array image, af::array filter, int iter_num);
};

#endif /* pcdi_hpp */
