#include "cstdio"
#include "common.h"
#include "pcdi.hpp"
#include "parameters.hpp"
#include "worker.hpp"
#include "util.hpp"
#include "arrayfire.h"

using namespace af;

PartialCoherence::PartialCoherence(Params * params, int * roi_area, int * kernel_area,  std::vector<int> partial_coherence_trigger, int alg,
                                   bool pcdi_normalize, int pcdi_iter)
{
    params = params;
    triggers = partial_coherence_trigger;
    algorithm = alg;
    roi= roi_area;
    kernel = kernel_area;
    normalize = pcdi_normalize;
    iteration_num = pcdi_iter;
}

std::vector<int> PartialCoherence::GetTriggers()
{
    return triggers;
}

int PartialCoherence::GetTriggerAlgorithm()
{
    return algorithm;
}

int * PartialCoherence::GetRoi()
{
    return roi;
}

int * PartialCoherence::GetKernel()
{
    return kernel;
}

void PartialCoherence::OnTrigger(af::array abs_image, af::array abs_data, Reconstruction *rec)
{
    // determine coherence
    // assume calculating coherence across all three dimentions
    af::array abs_image_roi = Utils::CropCenter(abs_image, roi[0], roi[1], roi[2]);
    af::array abs_data_roi = Utils::CropCenter(abs_data, roi[0], roi[1], roi[2]);
    if (normalize)
    {
        abs_image_roi = sqrt(abs_image_roi/sum<d_type>(pow(abs_image_roi, 2)) * sum<d_type>(pow(abs_data_roi, 2)));
    }

    // if symmetrize data, recalculate abs_image_roi and abs_data_roi - ask Ross if needed

    // LUCY deconvolution
    if (algorithm == ALGORITHM_LUCY)
    {
        // seems that in matlab determine_coh the params to deconvlucy are (data, image, iter). Should it be (image, data, itr)?
        // ask Ross
        af::array coherence = DeconvLucy(pow(abs_data_roi, 2), pow(abs_image_roi, 2), iteration_num);
    }
    else if (algorithm == ALGORITHM_LUCY_PREV)
    {
//        if (! prev_coherence)
//        {
//            prev_coherence = pow(abs_data_roi, 2);
//        }
//        else
//        {
//            prev_coherence = DeconvLucy(prev_coherence, pow(abs_image_roi, 2), iteration_num);
//        }
        //coherence =
    }
    else
    {
        //prinf("only LUCY algorithm is currently supported");
    }
}

af::array PartialCoherence::DeconvLucy(af::array image, af::array filter, int iter_num)
{
    // need to implement, for now return image
    return image;
}
