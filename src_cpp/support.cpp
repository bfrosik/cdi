//
//  support.cpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#include "stdio.h"
#include "support.hpp"
#include "parameters.hpp"


Support::Support(const dim4 data_dim, int * support_area, float th, int sgma, Trigger * support_trig)
{
    threshold = th;
    sigma = sgma;
    support_trigger = support_trig;
    support_array = constant(0, data_dim, u32);
    support_array( seq(0, support_area[0]-1), seq(0, support_area[1]-1), seq(0, support_area[2]-1) ) = 1;
}

void Support::Update()
{

}

std::vector<int> Support::GetTriggers()
{
    return support_trigger->GetTriggers();
}

int Support::GetTriggerAlgorithm()
{
    return support_trigger->GetTriggerAlgorithm();
}

int Support::GetSigma()
{
    return sigma;
}

float Support::GetThreshold()
{
    return threshold;
}

af::array Support::GetSupportArray()
{
    return support_array;
}

