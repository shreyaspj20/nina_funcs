import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from scipy import signal
from scipy.io import loadmat
from sklearn.metrics import confusion_matrix
import os
from tensorflow.keras.models import Sequential, Model, load_model
import datetime
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow import keras as K
from tqdm import tqdm
from sklearn.decomposition import PCA
import scipy as sp


def rms(data):
    return np.sqrt(np.mean(data ** 2))


def hist(data, nbins=20):
    histsig, bin_edges = np.histogram(data, bins=nbins)
    return tuple(histsig)


def entropy(data):
    pk = sp.stats.rv_histogram(np.histogram(data, bins=20)).pdf(data)
    return sp.stats.entropy(pk)


def kurtosis(data):
    return sp.stats.kurtosis(data)


def zero_cross(data):
    return len(np.where(np.diff(np.sign(data)))[0]) / len(data)


def min(data):
    return np.min(data)


def max(data):
    return np.max(data)


def mean(data):
    return np.mean(data)


def median(data):
    return np.median(data)


def fft(data):
    return np.fft.fft(data)


def psd(data):
    return np.abs(np.fft.fft(data)) ** 2


def get_data(path, file):
    mat = loadmat(os.path.join(path, file))
    data = pd.DataFrame(mat['emg'])
    data['stimulus'] = mat['restimulus']
    data['repetition'] = mat['repetition']

    return data


def normalise(data, train_reps):
    x = [np.where(data.values[:, 13] == rep) for rep in train_reps]
    indices = np.squeeze(np.concatenate(x, axis=-1))
    train_data = data.iloc[indices, :]
    train_data = data.reset_index(drop=True)

    scaler = StandardScaler(with_mean=True,
                            with_std=True,
                            copy=False).fit(train_data.iloc[:, :12])

    scaled = scaler.transform(data.iloc[:, :12])
    normalised = pd.DataFrame(scaled)
    normalised['stimulus'] = data['stimulus']
    normalised['repetition'] = data['repetition']
    return normalised


def filter_data(data, f, butterworth_order=4, btype='lowpass'):
    emg_data = data.values[:, :12]

    f_sampling = 2000
    nyquist = f_sampling / 2
    if isinstance(f, int):
        fc = f / nyquist
    else:
        fc = list(f)
        for i in range(len(f)):
            fc[i] = fc[i] / nyquist

    b, a = signal.butter(butterworth_order, fc, btype=btype)
    transpose = emg_data.T.copy()

    for i in range(len(transpose)):
        transpose[i] = (signal.lfilter(b, a, transpose[i]))

    filtered = pd.DataFrame(transpose.T)
    filtered['stimulus'] = data['stimulus']
    filtered['repetition'] = data['repetition']

    return filtered


def rectify(data):
    return abs(data)


def windowing(data, reps, gestures, win_len, win_stride):
    if reps:
        x = [np.where(data.values[:, 13] == rep) for rep in reps]
        indices = np.squeeze(np.concatenate(x, axis=-1))
        data = data.iloc[indices, :]
        data = data.reset_index(drop=True)

    if gestures:
        x = [np.where(data.values[:, 12] == move) for move in gestures]
        indices = np.squeeze(np.concatenate(x, axis=-1))
        data = data.iloc[indices, :]
        data = data.reset_index(drop=True)

    idx = [i for i in range(win_len, len(data), win_stride)]

    X = np.zeros([len(idx), win_len, len(data.columns) - 2])
    y = np.zeros([len(idx), ])
    reps = np.zeros([len(idx), ])

    for i, end in enumerate(idx):
        start = end - win_len
        X[i] = data.iloc[start:end, 0:12].values
        y[i] = data.iloc[end, 12]
        reps[i] = data.iloc[end, 13]

    return X, y, reps


def train_model(model, X_train_wind, y_train_wind, X_test_wind, y_test_wind, save_to, epoch=300):
    from tensorflow import keras as K
    opt_adam = K.optimizers.Adam(lr=0.0001, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=0.0)
    model.compile(loss='categorical_crossentropy', optimizer=opt_adam, metrics=['categorical_accuracy'])

    #         log_dir="logs/fit/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=30)
    mc = ModelCheckpoint(save_to + '_best_model.h5', monitor='val_categorical_accuracy', mode='max', verbose=1,
                         save_best_only=True)

    history = model.fit(x=X_train_wind, y=y_train_wind, epochs=epoch, shuffle=True,
                        verbose=1,
                        validation_data=(X_test_wind, y_test_wind), callbacks=[es, mc])

    saved_model = load_model(save_to + '_best_model.h5')
    # evaluate the model
    _, train_acc = saved_model.evaluate(X_train_wind, y_train_wind, verbose=0)
    _, test_acc = saved_model.evaluate(X_test_wind, y_test_wind, verbose=0)
    print('Train: %.3f, Test: %.3f' % (train_acc, test_acc))

    return history, saved_model


def get_categorical(y):
    return pd.get_dummies(pd.Series(y)).values


def plot_cnf_matrix(saved_model, X_valid_cv, target):
    y_pred = saved_model.predict(X_valid_cv)
    model_predictions = [list(y_pred[i]).index(y_pred[i].max()) + 1 for i in range(len(y_pred))]

    conf_mx = confusion_matrix(target, model_predictions)
    plt.matshow(conf_mx)
    plt.show()


def feature_extractor(features, shape, data):
    l = pd.DataFrame()
    for i, function in enumerate(tqdm(features)):
        feature = []
        print("Extracting feature....{}".format(str(function)))
        for i in range(data.shape[0]):
            for j in range(data.shape[2]):
                feature.append(function(data[i][:, j]))
        feature = np.reshape(feature, shape)
        l = pd.concat([l, pd.DataFrame(feature)], axis=1)
        print("Done extracting feature....{}".format(str(function)))
        print()
    return l


def pca(data, comp):
    l = PCA(n_components=comp)
    l.fit(data)
    x_pca = l.transform(data)
    return pd.DataFrame(x_pca)


def get_validation_curve(classifier, parameter, param_range, X,
                         y):  # A generalized function to plot validation curve for all 3 classifiers.
    train_scores, test_scores = validation_curve(
        classifier, X, y, param_name=parameter, param_range=param_range,
        scoring="accuracy", n_jobs=1)
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)

    plt.title("Validation Curve with {}".format(classifier.__class__.__name__))
    plt.xlabel(str(parameter))
    plt.ylabel("Score")
    plt.ylim(0.0, 1.1)
    lw = 2
    plt.semilogx(param_range, train_scores_mean, label="Training score",
                 color="darkorange", lw=lw)
    plt.fill_between(param_range, train_scores_mean - train_scores_std,
                     train_scores_mean + train_scores_std, alpha=0.2,
                     color="darkorange", lw=lw)
    plt.semilogx(param_range, test_scores_mean, label="Cross-validation score",
                 color="navy", lw=lw)
    plt.fill_between(param_range, test_scores_mean - test_scores_std,
                     test_scores_mean + test_scores_std, alpha=0.2,
                     color="navy", lw=lw)
    plt.legend(loc="best")

    return plt


def plot_learning_curve(estimator, title, X, y, axes=None, ylim=None, cv=None,
                        n_jobs=None, train_sizes=np.linspace(.1, 1.0, 5)):
    """
    Generate 3 plots: the test and training learning curve, the training
    samples vs fit times curve, the fit times vs score curve.

    Parameters
    ----------
    estimator : estimator instance
        An estimator instance implementing `fit` and `predict` methods which
        will be cloned for each validation.

    title : str
        Title for the chart.

    X : array-like of shape (n_samples, n_features)
        Training vector, where ``n_samples`` is the number of samples and
        ``n_features`` is the number of features.

    y : array-like of shape (n_samples) or (n_samples, n_features)
        Target relative to ``X`` for classification or regression;
        None for unsupervised learning.

    axes : array-like of shape (3,), default=None
        Axes to use for plotting the curves.

    ylim : tuple of shape (2,), default=None
        Defines minimum and maximum y-values plotted, e.g. (ymin, ymax).

    cv : int, cross-validation generator or an iterable, default=None
        Determines the cross-validation splitting strategy.
        Possible inputs for cv are:

          - None, to use the default 5-fold cross-validation,
          - integer, to specify the number of folds.
          - :term:`CV splitter`,
          - An iterable yielding (train, test) splits as arrays of indices.

        For integer/None inputs, if ``y`` is binary or multiclass,
        :class:`StratifiedKFold` used. If the estimator is not a classifier
        or if ``y`` is neither binary nor multiclass, :class:`KFold` is used.

        Refer :ref:`User Guide <cross_validation>` for the various
        cross-validators that can be used here.

    n_jobs : int or None, default=None
        Number of jobs to run in parallel.
        ``None`` means 1 unless in a :obj:`joblib.parallel_backend` context.
        ``-1`` means using all processors. See :term:`Glossary <n_jobs>`
        for more details.

    train_sizes : array-like of shape (n_ticks,)
        Relative or absolute numbers of training examples that will be used to
        generate the learning curve. If the ``dtype`` is float, it is regarded
        as a fraction of the maximum size of the training set (that is
        determined by the selected validation method), i.e. it has to be within
        (0, 1]. Otherwise it is interpreted as absolute sizes of the training
        sets. Note that for classification the number of samples usually have
        to be big enough to contain at least one sample from each class.
        (default: np.linspace(0.1, 1.0, 5))
    """
    if axes is None:
        _, axes = plt.subplots(1, 3, figsize=(20, 5))

    axes[0].set_title(title)
    if ylim is not None:
        axes[0].set_ylim(*ylim)
    axes[0].set_xlabel("Training examples")
    axes[0].set_ylabel("Score")

    train_sizes, train_scores, test_scores, fit_times, _ = \
        learning_curve(estimator, X, y, cv=cv, n_jobs=n_jobs,
                       train_sizes=train_sizes,
                       return_times=True)
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)
    fit_times_mean = np.mean(fit_times, axis=1)
    fit_times_std = np.std(fit_times, axis=1)

    # Plot learning curve
    axes[0].grid()
    axes[0].fill_between(train_sizes, train_scores_mean - train_scores_std,
                         train_scores_mean + train_scores_std, alpha=0.1,
                         color="r")
    axes[0].fill_between(train_sizes, test_scores_mean - test_scores_std,
                         test_scores_mean + test_scores_std, alpha=0.1,
                         color="g")
    axes[0].plot(train_sizes, train_scores_mean, 'o-', color="r",
                 label="Training score")
    axes[0].plot(train_sizes, test_scores_mean, 'o-', color="g",
                 label="Cross-validation score")
    axes[0].legend(loc="best")

    # Plot n_samples vs fit_times
    axes[1].grid()
    axes[1].plot(train_sizes, fit_times_mean, 'o-')
    axes[1].fill_between(train_sizes, fit_times_mean - fit_times_std,
                         fit_times_mean + fit_times_std, alpha=0.1)
    axes[1].set_xlabel("Training examples")
    axes[1].set_ylabel("fit_times")
    axes[1].set_title("Scalability of the model")

    # Plot fit_time vs score
    axes[2].grid()
    axes[2].plot(fit_times_mean, test_scores_mean, 'o-')
    axes[2].fill_between(fit_times_mean, test_scores_mean - test_scores_std,
                         test_scores_mean + test_scores_std, alpha=0.1)
    axes[2].set_xlabel("fit_times")
    axes[2].set_ylabel("Score")
    axes[2].set_title("Performance of the model")

    return plt


def notch_filter(data, f0, Q, fs=2000):
    emg_data = data.values[:, :14]

    b, a = signal.iirnotch(f0, Q, fs)
    transpose = emg_data.T.copy()

    for i in range(len(transpose)):
        transpose[i] = (signal.lfilter(b, a, transpose[i]))

    filtered = pd.DataFrame(transpose.T)

    return filtered
