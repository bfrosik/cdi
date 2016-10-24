//
//  manager.hpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#ifndef manager_hpp
#define manager_hpp

#include "vector"
#include "string"
#include "common.h"

class Reconstruction;

class Manager
{
private:
Reconstruction *rec;

public:
void StartCalc(std::vector<d_type> data_buffer_r, std::vector<d_type> guess_buffer_r, std::vector<d_type> guess_buffer_i, std::vector<int> dim, const std::string & config);

void StartCalc(std::vector<d_type> data_buffer_r, std::vector<int> dim, std::string const & config);
void StartCalc(std::vector<d_type> data_buffer_r, std::vector<int> dim, std::string const & config, int nu_threads);

std::vector<d_type> GetImageR();
std::vector<d_type> GetImageI();
std::vector<d_type> GetErrors();
 
};


#endif /* manager_hpp */
