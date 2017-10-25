/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#include "stdio.h"
#include "vector"
#include "map"
#include "state.hpp"
#include "parameters.hpp"
#include "support.hpp"
#include "algorithm.hpp"
#include "pcdi.hpp"
#include "arrayfire.h"

using namespace af;

// a reference to params object
Params *params;

// current iteration
int current_iter = -1;
// number of configured iterations for reconstruction
int total_iter_num = 0;

// The vector of errors indexed by iteration
std::vector<d_type>  errors;

// current algorithm
Algorithm * current_alg = NULL;
// current index of index switches vector
int alg_switch_index = 0;

// mapping of algorithm id to an Algorithm object
std::map<int, Algorithm*> algorithm_map;

// a flag indicating whether to update support
bool update_support = false;
// current index in support_triggers vector
int support_triggers_index = 0;

// partial coherence state
// a flag indicating whether to update partial coherence
bool run_convolution = false;
bool update_kernel = false;
// current index in support_partial_coherence vector
int partial_coherence_triggers_index = 0;

bool averaging = false;

bool apply_twin = false;


State::State(Params* parameters)
{
    params = parameters;
}

void State::Init()
{
    total_iter_num = params->GetNumberIterations();
    // create algorithms that are used in algorithm sequence
    // and load the objects into a map
    for (int i = 0; i < params->GetAlgSwitches().size(); i++)
    {
        int alg_id = params->GetAlgSwitches()[i].algorithm_id;
        if (algorithm_map[alg_id] == 0)
        {
            MapAlgorithmObject(alg_id);
        }
    }
    current_alg = algorithm_map[params->GetAlgSwitches()[0].algorithm_id];
}

State::~State()
{
}

void State::MapAlgorithmObject(int alg_id)
{
    // TODO consider refactoring if there are many subclasses
    // this method is called only during initialization, so it might be ok
    if (alg_id == ALGORITHM_HIO)
    {
        algorithm_map[alg_id] = new Hio;
    }
    else if(alg_id == ALGORITHM_ER)
    {
        algorithm_map[alg_id] = new Er;
    }
}

int State::Next()
{
    if (current_iter++ == total_iter_num - 1)
    {
        return false;
    }
    // figure out current alg
    if (params->GetAlgSwitches()[alg_switch_index].iterations == current_iter)
    // switch to the next algorithm
    {
        alg_switch_index++;
        current_alg = algorithm_map[params->GetAlgSwitches()[alg_switch_index].algorithm_id];
    }
 
    // check if update support this iteration
    if ((params->GetSupport()->GetTriggers().size() > 0) && (params->GetSupport()->GetTriggers()[support_triggers_index] == current_iter))
    {
        update_support = true;
        support_triggers_index++;
    }
    else
    {
        update_support = false;
    }

    // calculate if during the iteration should do averaging.
    averaging = ( current_iter >= (total_iter_num - params->GetAvgIterations()) );

    if (current_iter == params->GetTwin())
    {
        apply_twin = true;
    }
    else
    {
        apply_twin = false;
    }

    return true;
}

Algorithm * State::GetCurrentAlg()
{
    return current_alg;
}

void State::RecordError(d_type error)
{
    errors.push_back(error);
    printf("iter, error %i %fl\n", current_iter, error);
}

int State::GetCurrentIteration()
{
    return current_iter;
}

bool State::IsUpdateSupport()
{
    return update_support;
}

bool State::IsUpdatePartialCoherence()
{
    return update_kernel;
}

bool State::IsApplyTwin()
{
    return apply_twin;
}

bool State::IsAveragingIteration()
{
    return averaging;
}

std::vector<d_type>  State::GetErrors()
{
    return errors;
}


