//
//  parameters.hpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#ifndef support_hpp
#define support_hpp

#include "arrayfire.h"
#include "common.h"
#include "vector"

using namespace af;

class Trigger;

class Support
{
private:
    af::array support_array;
    Trigger * support_trigger;
    float threshold;
    int sigma;
public:
    Support(const dim4 data_dim, int * area, float threshold, int sigma, Trigger * support_trigger);
    void Update();
    std::vector<int> GetTriggers();
    int GetTriggerAlgorithm();
    int GetSigma();
    float GetThreshold();
    af::array GetSupportArray();
};

#endif /* support_hpp */
