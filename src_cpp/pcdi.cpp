#include "cstdio"
#include "common.h"
#include "pcdi.hpp"
#include "parameters.hpp"
#include "worker.hpp"
#include "util.hpp"
#include "arrayfire.h"

using namespace af;

af::array coherence;
af::array abs_amplitudes_roi_prev;

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

void PartialCoherence::Init(af::array abs_amplitudes)
{
    abs_amplitudes_roi_prev = abs_amplitudes(seq(0, roi[0]-1), seq(0, roi[1]-1), seq(0, roi[2]-1));
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

af::array PartialCoherence::ApplyPartialCoherence(af::array abs_amplitudes, af::array abs_data, Reconstruction *rec)
{
    // crop roi
    af::array abs_amplitudes_roi = abs_amplitudes(seq(0, roi[0]-1), seq(0, roi[1]-1), seq(0, roi[2]-1));

    // check if trigger is set for this iteration, and if so update coherence
    if ((trigger_index < triggers.size()) && (rec->GetCurrentIteration() == triggers[trigger_index]))
    {
        trigger_index++;
        af::array abs_data_roi = abs_data(seq(0, roi[0]-1), seq(0, roi[1]-1), seq(0, roi[2]-1));
        OnTrigger(2*abs_amplitudes_roi-abs_amplitudes_roi_prev, abs_data_roi, rec);   // params.use_2k_1 from matlab program
        printf("Updating coherence, current iter %i\n", rec->GetCurrentIteration());
    }

    // save the amplitudes as previous for the next trigger
    abs_amplitudes_roi_prev = abs_amplitudes_roi;

    // apply coherence
    af_print(pow(abs_amplitudes_roi, 2));
    af_print(coherence);

    af::array abs_amplitudes_roi_coh = sqrt(af::fftConvolve(pow(abs_amplitudes_roi, 2), coherence));
    af_print(abs_amplitudes_roi_coh);

    return abs_amplitudes_roi_coh;
}

void PartialCoherence::OnTrigger(af::array abs_amplitudes, af::array abs_data, Reconstruction *rec)
{
    // assume calculating coherence across all three dimentions
    af::array abs_amplitudes_roi = abs_amplitudes;
    af::array abs_data_roi = abs_data;
    if (normalize)
    {
        abs_amplitudes_roi = sqrt(pow(abs_amplitudes_roi, 2)/sum<d_type>(pow(abs_amplitudes_roi, 2)) * sum<d_type>(pow(abs_data_roi, 2)));
    }
    // if symmetrize data, recalculate abs_amplitudes_roi and abs_data_roi - not doing it now, since default to false

    // LUCY deconvolution
    if (algorithm == ALGORITHM_LUCY)
    {
        coherence = DeconvLucy(pow(abs_amplitudes_roi, 2), pow(abs_data_roi, 2), iteration_num);
        af_print(coherence);
        TuneLucyCoherence();
    }
    else if (algorithm == ALGORITHM_LUCY_PREV)
    {
        // initialize, consider moving to init()
        if (trigger_index == 1)
        {
            coherence = pow(abs_data_roi, 2);
        }
        coherence = DeconvLucy(coherence, pow(abs_data_roi, 2), iteration_num);
        TuneLucyCoherence();
    }
    else
    {
        //prinf("only LUCY algorithm is currently supported");
    }
}

af::array PartialCoherence::DeconvLucy(af::array amplitudes, af::array psf, int iterations)
{
    // implementation based on Python code: https://github.com/scikit-image/scikit-image/blob/master/skimage/restoration/deconvolution.py
    af::array im_deconv = constant(0.5, amplitudes.dims());  // investigate whether this should be at init TODO
    af::array psf_mirror = af::flip(af::flip(af::flip(psf, 0),1),2);

    for (int i = 0; i < iterations; i++)
    {
        af::array convolve = af::fftConvolve(im_deconv, psf);
        convolve(convolve == 0) = 1.0;   // added to the algorithm from scikit to prevet division by 0

        af::array relative_blurr = amplitudes/convolve;
        im_deconv *= af::fftConvolve(relative_blurr, psf_mirror);
    }
    return im_deconv;
}

void PartialCoherence::TuneLucyCoherence()
{
//    coherence = Utils::CenterMax(abs(coherence), kernel);
    coherence = Utils::ShiftMax(abs(coherence), kernel);
    printf("norm , 1/norm %f %f\n", sqrt(sum<d_type>(abs(coherence))), 1/sqrt(sum<d_type>(abs(coherence))));
    // if symmetrize kernel, recalculate coherence - ask Ross if needed
    printf("adjusting coherence\n");
//    coherence = coherence/sum<d_type>(coherence);
    af_print(coherence);
}
