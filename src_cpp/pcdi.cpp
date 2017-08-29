#include "cstdio"
#include "common.h"
#include "pcdi.hpp"
#include "util.hpp"
#include "arrayfire.h"
#include "string"
#include "sstream"

using namespace af;

af::array kernel_array;
af::array roi_amplitudes_prev;
af::array roi_data_abs;
d_type sum_roi_data;
af::dim4 roi_dims;
af::dim4 dims;

PartialCoherence::PartialCoherence(std::vector<int> roi_area, int * kernel_area,  std::vector<int> partial_coherence_trigger, int alg, bool pcdi_normalize, int pcdi_iter, bool pcdi_clip)
{
    roi= roi_area;
    triggers = partial_coherence_trigger;
    trigger_index = 0;
    algorithm = alg;
    kernel = kernel_area;
    normalize = pcdi_normalize;
    iteration_num = pcdi_iter;
    clip = pcdi_clip;
}

void PartialCoherence::Init(af::array data)
{
    roi_dims = Utils::Int2Dim4(roi);
    dims = data.dims();

    af::array data_centered = af::shift(data, dims[0]/2, dims[1]/2, dims[2]/2, dims[3]/2);
    roi_data_abs =  Utils::CropCenter(data_centered, roi_dims).copy();
    if (normalize)
    {
        sum_roi_data = sum<d_type>(pow(roi_data_abs, 2));
    } 
    kernel_array = constant(0.5, roi_dims);
}

void PartialCoherence::SetPrevious(af::array abs_amplitudes)
{
    af::array abs_amplitudes_centered = shift(abs_amplitudes, dims[0]/2, dims[1]/2, dims[2]/2, dims[3]/2);
    roi_amplitudes_prev =  Utils::CropCenter(abs_amplitudes_centered, roi_dims).copy();
}

std::vector<int> PartialCoherence::GetTriggers()
{
    return triggers;
}

int PartialCoherence::GetTriggerAlgorithm()
{
    return algorithm;
}

std::vector<int> PartialCoherence::GetRoi()
{
    return roi;
}

int * PartialCoherence::GetKernel()
{
    return kernel;
}

af::array PartialCoherence::ApplyPartialCoherence(af::array abs_amplitudes, int current_iteration)
{
    // check if trigger is set for this iteration, and if so update coherence
    if ((trigger_index < triggers.size()) && (current_iteration == triggers[trigger_index]))
    {        
//        if (trigger_index > 0)
        {
            af::array abs_amplitudes_centered = shift(abs_amplitudes, dims[0]/2, dims[1]/2, dims[2]/2, dims[3]/2);
            af::array roi_abs_amplitudes = Utils::CropCenter(abs_amplitudes_centered, roi_dims).copy();
    
            af::array roi_combined_amp = 2*roi_abs_amplitudes - roi_amplitudes_prev;
            OnTrigger(roi_combined_amp);   // use_2k_1 from matlab program
            printf("Updating coherence, current iter %i\n", current_iteration);
        }
//        else
//        {
//            //set gaussian coherence
//            printf("setting coherence to gauss\n");
//            d_type sigmas [] = {0.5, 0.5, 0.5};
//            kernel_array = Utils::GaussDistribution(dim4(11,11,11), sigmas, 1);
//        }
//        
        trigger_index++;
    }

    // apply coherence
    af::array abs_amplitudes_2 = pow(abs_amplitudes, 2);
    af::array converged_2 = af::fftConvolve(abs_amplitudes_2, kernel_array);
    af::array converged = sqrt(converged_2);
    //af::array converged = sqrt(fftConvolve(pow(abs_amplitudes, 2), kernel_array));  // implemented here, but works different than af::fftConvolve

    printf("coherence norm %f\n", sum<d_type>(pow(abs(kernel_array), 2)));
    printf("converged norm %f\n", sum<d_type>(pow(abs(converged), 2)));
    return converged;
}

void PartialCoherence::OnTrigger(af::array arr)
{
    // assume calculating coherence across all three dimensions
    af::array amplitudes = arr;
    // if symmetrize data, recalculate roi_array and roi_data - not doing it now, since default to false
    if (normalize)
    {
        af::array amplitudes_2 = pow(arr, 2);
        d_type sum_ampl = sum<d_type>(amplitudes_2);
        d_type ratio = sum_roi_data/sum_ampl;
        amplitudes = sqrt(amplitudes_2 * ratio);
        //amplitudes = sqrt((pow(arr, 2)/sum<d_type>(pow(arr, 2))) * sum_roi_data);
    }
    
    af::array coherence;
    // LUCY deconvolution
    if (algorithm == ALGORITHM_LUCY)
    {
        DeconvLucy(pow(amplitudes, 2), pow(roi_data_abs, 2), iteration_num);
    }
    else if (algorithm == ALGORITHM_LUCY_PREV)
    {
        // initialize, consider moving to init()
        if (trigger_index == 1)
        {
            coherence = pow(roi_data_abs, 2);
        }
        //coherence = DeconvLucy(coherence, pow(roi_data_abs, 2), iteration_num);
    }
    else
    {
        //prinf("only LUCY algorithm is currently supported");
    }
}

af::array PartialCoherence::fftConvolve(af::array arr, af::array kernel)
{  
    af::dim4 dims_input = arr.dims();
    af::dim4 dims_kernel = kernel.dims();    

    int dims_fft_padded [nD];

    for(unsigned int i = 0; i < nD; i++)
    {
        dim_t d = Utils::GetDimension(dims_input[i] + dims_kernel[i] - 1);
        dims_fft_padded[i] = Utils::GetDimension(dims_input[i] + dims_kernel[i] - 1);
    }
    
    d_type pad = 0;
    af::array kernel_padded = Utils::PadAround(kernel, dims_input, pad);
    
    af::array coh_padded = real( Utils::ifft( Utils::fft(arr) * Utils::fft(kernel_padded) ) ); 
    return coh_padded;

}

void PartialCoherence::DeconvLucy(af::array amplitudes, af::array data, int iterations)
{
    // implementation based on Python code: https://github.com/scikit-image/scikit-image/blob/master/skimage/restoration/deconvolution.py
    //af::array coherence = constant(0.5, amplitudes.dims());
    //set it to the last coherence instead
    af::array coherence = kernel_array;
    af::array data_mirror = af::flip(af::flip(af::flip(af::flip(data, 0),1),2),3).copy();

    for (int i = 0; i < iterations; i++)
    {
        af::array convolve = af::fftConvolve(coherence, data);
        //af::array convolve = af::convolve3(im_deconv, psf);
        convolve(convolve == 0) = 1.0;   // added to the algorithm from scikit to prevet division by 0

        af::array relative_blurr = amplitudes/convolve;
        coherence *= af::fftConvolve(relative_blurr, data_mirror);
    }
    coherence = real(coherence);
    // clip
    if (clip)
    {
        coherence(coherence > 1) = 1;
        coherence(coherence < -1) = -1;
    }
    //coherence = abs(coherence)/sum<d_type>(abs(coherence)); 
    d_type coh_sum = sum<d_type>(abs(coherence));
    coherence = abs(coherence)/coh_sum;    
    printf("coherence norm ,  %f\n", sum<d_type>(pow(abs(coherence), 2)));
    kernel_array = coherence;
}


af::array PartialCoherence::GetKernelArray()
{
    return kernel_array;
}