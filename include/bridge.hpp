/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef bridge_hpp
#define bridge_hpp

#include "vector"
#include "string"
#include "common.h"

class Bridge
{
public:
void StartCalcWithGuess(std::vector<float> data_buffer_r, std::vector<float> guess_buffer_r, std::vector<float> guess_buffer_i, std::vector<int> dim, const std::string & config, int stage);

void StartCalc(std::vector<float> data_buffer_r, std::vector<int> dim, std::string const & config, int stage);
void StartCalcMultiple(std::vector<float> data_buffer_r, std::vector<int> dim, std::string const & config, int nu_threads, int stage);

std::vector<float> GetSupportV();
std::vector<d_type> GetCoherenceV();
std::vector<d_type> GetImageR();
std::vector<d_type> GetImageI();
std::vector<d_type> GetErrors();
 
};


#endif /* bridge_hpp */
