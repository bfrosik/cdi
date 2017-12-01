/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef support_hpp
#define support_hpp

#include "common.h"
#include "vector"
#include "arrayfire.h"

class Params;

using namespace af;

class Support
{
private:
    af::array distribution;   
    float threshold;
    int sigma;
    int algorithm;
    af::array support_array;
    af::array GaussConvFft(af::array ds_image);
    
public:
    Support(const dim4 data_dim, Params *params, af::array support_array);
    void Update(const af::array ds_image);
    int GetTriggerAlgorithm();
    int GetSigma();
    float GetThreshold();
    af::array GetSupportArray(bool twin=false);
};

#endif /* support_hpp */
