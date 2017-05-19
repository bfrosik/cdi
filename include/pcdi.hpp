
#ifndef pcdi_hpp
#define pcdi_hpp

#include "vector"

class Params;
//class Reconstruction;
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
    int trigger_index;
    int algorithm;
    bool normalize;
    int iteration_num;

    af::array DeconvLucy(af::array image, af::array filter, int iter_num);
    void OnTrigger(af::array abs_image, af::array abs_data);
    void TuneLucyCoherence();
    int GetTriggerAlgorithm();
    int * GetRoi();
    int * GetKernel();

public:
    PartialCoherence(Params * params, int * roi, int * kernel, std::vector<int> partial_coherence_trigger, int alg, bool pcdi_normalize, int pcdi_iter);
    void SetPrevious(af::array abs_amplitudes);
    std::vector<int> GetTriggers();
    af::array ApplyPartialCoherence(af::array abs_image, af::array abs_data, int current_iteration);
};

#endif /* pcdi_hpp */
