[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


## 💥DESCRIPTION

A sample python package deployment utility for NINAPRO dataset.
This library aims at easing the preprocessing, amd training of the EMG signals from the NinaPro database.


## 💥QUICK START

### Dependencies
This pipeline requires the dependencies which can be installed by running `pip install -r requirements.txt`


### 💥Functions
*  _**get_data(path, file)**_

      Download the data from the NinaPro official website and save the data in a folder. 
      The get_data() requires the folder path and the file name as the input arguments.
      For example:

      `data = get_data('DB2_s1/DB2_s1','S1_E1_A1.mat')`

      <p>&nbsp;</p>

*  **_normalise(data, train_reps)_**

      normalise() scales the data using the normalise() uses the StandardScaler() from scikit-learn to normalize the data. It fits on training reps only and then transforms the       whole data (excluding stimulus and repetition ofcourse).

      `data = normalise(data, train_reps)`

      train_reps are the reps required in training set and test_reps are reps
      required in the test/validation set. According to the recent research, this permutation of numbers proved to give better results.

      `train_reps = [1,3,4,6]`
      `test_reps = [2,5]`

      <p>&nbsp;</p>


*  **_filter_data(data, f, butterworth_order=4, btype='bandpass')_**

      Sometimes, it is required that the signal is filtered with low noise or high noise frequencies. filter_data uses Butterworth filter to filter the data. It requires the           cutoff frequency, the butterworth order, and the type of filter (btype is one of lowpass, highpass, bandpass).
      The bandpass filter requires the f value to be a tuple or a list containing lower cutoff frequency and higher cutoff frequency.

      `emg_low = filter_data(data=data, f=20, butterworth_order=4, btype='lowpass')`

      `emg_band = filter_data(data=data, f=(20,40), butterworth_order=4, btype='bandpass')`

      `emg_high = filter_data(data=data, f=20, butterworth_order=4, btype='high')`

      <p>&nbsp;</p>

*  **_notch_filter(data, f0, Q, fs=2000)_**

      A Notch Filter is a bandstop filter with a very narrow stopband and two passbands, it actually highly attenuates/eliminates a particular frequency component from the input       signal while leaving the amplitude of the other frequencies more or less unchanged.

      f0 is the notch_frequency, Q is the quality factor and fs is the sampling frequency.

      `emg_notch = notch_filter(data=emg_band,f0=60,Q=30,fs=2000)`

      <p>&nbsp;</p>

*  **_windowing(data, reps, gestures, win_len, win_stride)_**

      windowing() is used to augment the data. The function requires the following arguments : data, reps, gestures, win_len, win_stride.

      data = Pandas dataframe just like returned by any of the above functions.

      reps = Repetitions that you want to use for windowing.

      gestures = The gesture movements that you wish to classify.

      win_len = (Length of window in millisecond) x 2. For example, for a window of 300ms, use 600 as the win_len since the sampling frequency of signal is 2000Hz.

      win_stride = (Length of stride in millisecond) x 2. For example, for a stride of 10ms, use 20 as the win_stride since the sampling frequency of signal is 2000Hz.

      `X_train, y_train, r_train = windowing(emg_notch, train_reps, gestures, win_len, win_stride)`

      `
      X_test, y_test, r_test = windowing(emg_notch, test_reps, gestures, win_len, win_stride)`

      <p>&nbsp;</p>

*  **_get_categorical(y)_**

    For multiclass classification, we need the labels to be represented in one-hot representation.
    get_categorical() helps in converting the integer labels to one-hot representation.

    `y_train = get_categorical(y_train)`

    `y_test = get_categorical(y_test)`

    <p>&nbsp;</p>

*  **_feature_extractor(features, shape, data)_**

    Hand crafting features could be time consuming and expensive. We extract important features:

    Time Domain (rms,hist,entropy,kurtosis,zero_cross,min,max,mean,median)

    Frequency Domain (fft,psd)

    The extractor function will take care of extracting features for each channel of input data and append it columnwise.
    The output dataframe would include all required features of all channels.

    `features = [rms,min,max,median]` Change this list according to features required.

    `feature_matrix = feature_extractor(features,(X_train.shape[0],-1),X_train)`

    `test_feature_matrix = feature_extractor(features,(X_test.shape[0],-1),X_test)`

    <p>&nbsp;</p>

*  **_pca(data, comp)_**

    PCA is a dimensionality-reduction method that is often used to reduce the dimensionality of large data sets, by transforming a large set of variables into a smaller one that     still contains most of the information in the large set.
    The function returns the reduced feature matrix with the mentioned number of components(columns).

    `reduced_feature_matrix = pca(feature_matrix,30)`. This returns 30 columns in the final matrix.

    `reduced_test_feature_matrix = pca(test_feature_matrix,30)`

    <p>&nbsp;</p>

*  **_rectify(data)_**

    This function rectifies the signals and converts all the negative values to positive values by simply using the absolute value.

    `emg_rectified = rectify(emg_notch)`

<p>&nbsp;</p>

## 💥Usage

The package could be leveraged from PyPI using 
`pip install nina-funcs`

## We have currently hit 2.5k+ package downloads

![image](https://github.com/shreyaspj20/nina_funcs/assets/56503884/837df5fb-5591-413d-860e-0ae790ca4ec8)


## 💥Meta Data

License: MIT License

Author: Shreyas P J

Requires: Python >=3.6
