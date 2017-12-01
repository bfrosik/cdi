/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef pcdi_hpp
#define pcdi_hpp

#include "vector"

class Params;

namespace af {
    class array;
}

class PartialCoherence
{
private:
    std::vector<int> roi;
    int crop[6];
    std::vector<int> triggers;
    int trigger_index;
    int algorithm;
    bool normalize;
    int iteration_num;

    void DeconvLucy(af::array image, af::array filter, int iter_num);
    void OnTrigger(af::array abs_image);
    void TuneLucyCoherence(af::array);
    int GetTriggerAlgorithm();
    std::vector<int> GetRoi();
    af::array fftConvolve(af::array arr, af::array kernel);

public:
    PartialCoherence(Params *params, af::array coherence_array);
    void Init(af::array data);
    void SetPrevious(af::array abs_amplitudes);
    std::vector<int> GetTriggers();
    af::array ApplyPartialCoherence(af::array abs_image, int current_iteration);
    af::array GetKernelArray();
};

#endif /* pcdi_hpp */
