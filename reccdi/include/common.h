/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef common_h
#define common_h

// defines the type of the data; can be float or double. The double will get replaced when running initializing script.
typedef double d_type;

const int nD = 3;


// a pair that defines an algorithm, and an iteration at which the algorithm is replaced by another or the process ends
struct Alg_switch 
{
    int algorithm_id;
    int iterations;
    Alg_switch(int alg, int iter)
    {
        algorithm_id = alg;
        iterations = iter;
    }
};
typedef struct Alg_switch alg_switch;

const int ALGORITHM_ER = 2;
const int ALGORITHM_HIO = 3;

const int ALGORITHM_LUCY = 13;
const int ALGORITHM_LUCY_PREV = 14;
const int ALGORITHM_GAUSS = 15;
const int ALGORITHM_BOX = 16;
const int ALGORITHM_PERCENT = 17;
const int ALGORITHM_GAUSS_FILL = 18;
const int ALGORITHM_GAUSS_PERCENT = 19;
const int ALGORITHM_PERCENT_AUTO = 20;
const int ALGORITHM_GAUSS_MINAREA = 21;

const int REGULARIZED_AMPLITUDE_NONE = 0;
const int REGULARIZED_AMPLITUDE_GAUSS = 1;
const int REGULARIZED_AMPLITUDE_POISSON = 2;
const int REGULARIZED_AMPLITUDE_UNIFORM = 3;

const int NOT_TRIGGER = 0;
const int FIRST_RUN_ONLY = 1;
const int FOR_ALL_RUNS = 2;
const int MODIFIED_AFTER_FIRST = 3;
const int CUSTOM = 4;

typedef struct flow_item_def { char* item_name;
                           int type;
                           char* func_name;
                           flow_item_def(char* item, int t, char* func) : item_name(item), type(t), func_name(func){}
                  } flow_item_def;

// The table below defines general iteration sequence. Each item defines a function with the reconstruction algorithm,
// and is called flow_item_def. It is defined by a name, type, and function name. The name is an identifier, also for
// trigger it should match the name in configuration file. The type defines what kind of instruction it is.
// The NO_TRIGGER indicates that the corresponding function will be executed for all iterations.
// FIRST_RUN_ONLY means that the configured triggers apply only if it is an initial run.
// MODIFIED_AFTER_FIRST means that after initial run the trigger gets modified. The start trigger will be equal to step.
// FOR_ALL_RUNS means that the same triggers apply for all runs.
// CUSTOM means that parsing of the triggers is different from the generic (as described in config_rec file) and it
// requires extra code.
// The flow_item_def func_name is a name of the function in worker that implements the flow item.
//
// To add a new trigger/function do the following:
// 1. Insert a new definition for the flow_item in the correct order in the flow_def array.
// 2. Update the flow_seq_len below.
// 3. Add the new function to the worker.hh and worker.cc, and add the pair (func_name, fp) to the flow_ptr_map in worker.cpp.
const flow_item_def flow_def[] = {
  flow_item_def((char *)"next",                  NOT_TRIGGER,          (char *)"NextIter"),
  flow_item_def((char *)"resolution_trigger",    FIRST_RUN_ONLY,       (char *)"ResolutionTrigger"),
  flow_item_def((char *)"amp_support_trigger",   MODIFIED_AFTER_FIRST, (char *)"SupportTrigger"),
  flow_item_def((char *)"phase_support_trigger", FIRST_RUN_ONLY,       (char *)"PhaseTrigger"),
  flow_item_def((char *)"to_reciprocal_space",   NOT_TRIGGER,          (char *)"ToReciprocal"),
  flow_item_def((char *)"pcdi_trigger",          MODIFIED_AFTER_FIRST, (char *)"PcdiTrigger"),
  flow_item_def((char *)"pcdi",                  CUSTOM,               (char *)"Pcdi"),
  flow_item_def((char *)"no_pcdi",               CUSTOM,               (char *)"NoPcdi"),
  flow_item_def((char *)"garbage_trigger",       FOR_ALL_RUNS,         (char *)"Gc"),
  flow_item_def((char *)"set_prev_pcdi_trigger", CUSTOM,               (char *)"SetPcdiPrevious"),
  flow_item_def((char *)"to_direct_space",       NOT_TRIGGER,          (char *)"ToDirect"),
  flow_item_def((char *)"algorithm",             CUSTOM,               (char *)"RunAlg"),
  flow_item_def((char *)"twin_trigger",          FIRST_RUN_ONLY,       (char *)"Twin"),
  flow_item_def((char *)"average_trigger",       FOR_ALL_RUNS,         (char *)"Average"),
  flow_item_def((char *)"progress_trigger",      FOR_ALL_RUNS,         (char *)"Prog")
};

const int flow_seq_len = 15;

#endif /* common_h */
