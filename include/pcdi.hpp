
#ifndef pcdi_hpp
#define pcdi_hpp

#include "vector"

//class Reconstruction;
namespace af {
    class array;
}

class PartialCoherence
{
private:
    std::vector<int> roi;
    int * kernel;
    int crop[6];
    std::vector<int> triggers;
    int trigger_index;
    int algorithm;
    bool normalize;
    int iteration_num;
    bool clip;

    void DeconvLucy(af::array image, af::array filter, int iter_num);
    void OnTrigger(af::array abs_image);
    void TuneLucyCoherence(af::array);
    int GetTriggerAlgorithm();
    std::vector<int> GetRoi();
    int * GetKernel();
    af::array fftConvolve(af::array arr, af::array kernel);

public:
    PartialCoherence(std::vector<int> roi, int * kernel, std::vector<int> partial_coherence_trigger, int alg, bool pcdi_normalize, int pcdi_iter, bool pcdi_clip);
    void Init(af::array data);
    void SetPrevious(af::array abs_amplitudes);
    std::vector<int> GetTriggers();
    af::array ApplyPartialCoherence(af::array abs_image, int current_iteration);
    af::array GetKernelArray();
};

#endif /* pcdi_hpp */
