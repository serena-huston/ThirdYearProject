from create_segmentation_array import create_segmentation_array
from scipy.signal import butter, filtfilt, hilbert, spectrogram
import statistics
from schmidt_spike_removal import schmidt_spike_removal
from librosa import resample 
import numpy as np 
import pywt
from utils import get_wavs_and_tsvs
from getDWT import * 

from PlotSignals import PlotSignals

class DataPreprocessing: 

    SAMPLING_FREQUENCY = 4000 
    DOWNSAMPLE_FREQUENCY = 50 
    PATCH_SIZE = 256
    STRIDE = int(PATCH_SIZE / 8)

    def __init__(self, wav, tsv, fs, filename):
        self.wav = wav
        self.tsv = tsv
        self.filename = filename 
        self.sample_rate = fs

        self.segmentation_processing()
        if len(self.wav) >0  and len(self.segmentation_array) >0:
            self.set_envelopes()
            self.normalise_envelopes()
            self.create_envelope_signal()
        
    def set_envelopes(self):
        filtered_signal = self.filter_signal(self.wav)
        spike_rem_signal = self.spike_removal(filtered_signal)

        self.homo_env = self.get_homomorphic_envelope(spike_rem_signal)
        self.hilb_env = self.get_hilbert_envelope(spike_rem_signal)
        self.wave_env = self.get_wavelet_envelope(spike_rem_signal)
        self.power_spec_env = self.get_power_spectral_density_envelope(spike_rem_signal)
        

    def normalise_envelopes(self):
        self.homo_env = self.normalise_envelope(
                                self.downsample_envelope(self.homo_env, self.SAMPLING_FREQUENCY, self.DOWNSAMPLE_FREQUENCY))
        
        self.hilb_env = self.normalise_envelope(
                                self.downsample_envelope(self.hilb_env, self.SAMPLING_FREQUENCY, self.DOWNSAMPLE_FREQUENCY))
                            
        self.wave_env = self.normalise_envelope(
                                self.downsample_envelope(self.wave_env, self.SAMPLING_FREQUENCY, self.DOWNSAMPLE_FREQUENCY))

        self.power_spec_env = self.normalise_envelope(
                                self.downsample_envelope(self.power_spec_env, (1+1e-9), self.homo_env.shape[0]/len(self.power_spec_env)))

        self.segmentation_array = self.downsample_segmentation_array()
        # ps = PlotSignals()
        # ps.plot_envelopes([self.homo_env, self.hilb_env, self.wave_env, self.power_spec_env], self.filename)

        
    def create_envelope_signal(self):
        self.combined_envs = np.vstack((self.homo_env, self.hilb_env, self.wave_env, self.power_spec_env))


    def filter_signal(self, signal):
        # Apply high pass and low pass buttherworth filters of 25 and 400 hz 
        low_filtered = self.get_butterworth_low_pass_filter(signal, 2, 400, self.SAMPLING_FREQUENCY)
        high_filtered = self.get_butterworth_high_pass_filter(low_filtered, 2, 25, self.SAMPLING_FREQUENCY)
        return high_filtered


    def spike_removal(self, signal):
        return schmidt_spike_removal(signal, self.SAMPLING_FREQUENCY)

    
    def get_homomorphic_envelope(self, signal, lpf_frequency=8):
        B_low, A_low = butter(1, 2 * lpf_frequency / self.SAMPLING_FREQUENCY, btype="low")
        homomorphic_envelope = np.exp(filtfilt(B_low, A_low, np.log(np.abs(hilbert(signal))), padlen=3*(max(len(B_low),len(A_low))-1)))

        # Remove spurious spikes in first sample
        homomorphic_envelope[0] = homomorphic_envelope[1]
        return homomorphic_envelope

    # Output still in time domain 
    def get_hilbert_envelope(self, signal):
        return np.abs(hilbert(signal))

    
    def get_wavelet_envelope(self, signal):
        wavelet_level = 3
        wavelet_name = "rbio3.9"

        if len(signal) < self.SAMPLING_FREQUENCY * 1.025:
            signal = np.concatenate((signal, np.zeros((round(0.025 * self.SAMPLING_FREQUENCY)))))

        # audio needs to be longer than 1 second for getDWT to work
        cD, cA = getDWT(signal, wavelet_level, wavelet_name)

        wavelet_feature = abs(cD[wavelet_level - 1, :])
        wavelet_feature = wavelet_feature[:len(self.homo_env)]

        return wavelet_feature 


    # From Danny's extract_features.py
    def get_power_spectral_density_envelope(self, signal):
        f, t, Sxx = spectrogram(signal, self.SAMPLING_FREQUENCY, window=('hamming'), nperseg=int(self.SAMPLING_FREQUENCY / 41),
                                       noverlap=int(self.SAMPLING_FREQUENCY / 81), nfft=self.SAMPLING_FREQUENCY)
        # ignore the DC component - springer does this by returning freqs from 1 to round(sampling_frequency/2). We do the same by removing the first row.
        Sxx = Sxx[1:, :]
        low_limit_position = np.where(f == 40)
        high_limit_position = np.where(f == 60)

        # Find the mean PSD over the frequency range of interest:
        psd = np.mean(Sxx[low_limit_position[0][0]:high_limit_position[0][0]+1, :], axis=0)

        return psd


    def downsample_envelope(self, envelope, og_freq, new_freq):
        return resample(envelope, orig_sr=og_freq, target_sr=new_freq)

    
    def normalise_envelope(self, envelope):
        mean = np.mean(envelope)
        std = np.std(envelope)
        return (envelope - mean)/std

    # From Danny's train_segmentation.py 
    def segmentation_processing(self):
        segmentation_details = create_segmentation_array(self.wav, self.tsv, 
                                         recording_frequency=self.SAMPLING_FREQUENCY, 
                                         feature_frequency=self.SAMPLING_FREQUENCY)
        try: 
            self.wav = segmentation_details[0][0]
            self.segmentation_array = segmentation_details[1][0]-1
        except: 
            self.wav = []
            self.segmentation_array =  []


    # From Danny's extract_features.py
    def get_butterworth_low_pass_filter(self, original_signal,
                                    order,
                                    cutoff,
                                    sampling_frequency):

        B_low, A_low = butter(order, 2 * cutoff / sampling_frequency, btype="lowpass")

        low_pass_filtered_signal = filtfilt(B_low, A_low, original_signal)
        return low_pass_filtered_signal


    # From Danny's extract_features.py
    def get_butterworth_high_pass_filter(self, original_signal,
                                     order,
                                     cutoff,
                                     sampling_frequency):

        B_high, A_high = butter(order, 2 * cutoff / sampling_frequency, btype="highpass")
        high_pass_filtered_signal = filtfilt(B_high, A_high, original_signal)
        return high_pass_filtered_signal

    
    def extract_env_patches(self):
        patch_list = [] 
        if self.combined_envs.shape[1] < self.PATCH_SIZE: 
            padding = self.PATCH_SIZE - self.combined_envs.shape[1]
            self.combined_envs = np.pad(self.combined_envs, [(0,0), (0, padding)], mode="constant", constant_values=(0))
        for i in range(0, self.combined_envs.shape[1], self.STRIDE):
            patch = self.combined_envs[:, i:i+self.PATCH_SIZE]
            if patch.shape[1] < self.PATCH_SIZE:
                break 
            else: 
                patch_list.append(patch)
        return patch_list 

    def extract_segmentation_patches(self):
        patch_list = [] 
        if len(self.segmentation_array) < self.PATCH_SIZE: 
            padding = self.PATCH_SIZE - len(self.segmentation_array)
            self.segmentation_array = np.pad(self.segmentation_array, pad_width=padding, mode="constant", constant_values=(0))
        for i in range(0, len(self.segmentation_array), self.STRIDE):
            patch = self.segmentation_array[i:i+self.PATCH_SIZE]
            if len(patch) < self.PATCH_SIZE:
                break 
            else: 
                patch_list.append(patch)
        return patch_list 

    def downsample_segmentation_array(self):
        labels_per_sample = int(self.sample_rate / self.DOWNSAMPLE_FREQUENCY)
        downsample_segment = [] 
        for i in range(0, self.segmentation_array.shape[0], labels_per_sample):
            modal_val = statistics.mode(self.segmentation_array[i:i+labels_per_sample])
            downsample_segment.append(modal_val)
        return downsample_segment
