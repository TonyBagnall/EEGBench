"""The estimators on the leaderboard, and where each comes from.

This is metadata only. Neuroverse holds no classifier code: classifiers designed
for EEG are in aeon-neuro, ports of general multivariate classifiers are in
multiverse.classification, and the rest are in aeon.

An estimator's name here matches its column in ``results/neuroverse/<metric>.csv``
(or its directory name in Multiverse per-estimator layout). Two groupings are
recorded for every estimator:

1. ``paradigm`` (:data:`PARADIGMS`): high-level methodological family used on
   the interactive leaderboard and score matrix (General TSML, EEG Classical,
   EEG Supervised DL, EEG Foundation, Tabular).
2. ``tsml_family`` (:data:`TSML_FAMILIES`): the ``tsml-eval`` category folder
   under which raw ``testResample0.csv`` predictions are stored.
"""

from __future__ import annotations

__all__ = [
    "ESTIMATORS",
    "ESTIMATOR_METADATA",
    "BAKEOFF_ESTIMATORS",
    "FAMILIES",
    "PARADIGMS",
    "TSML_FAMILIES",
    "PAPER_ESTIMATORS",
    "family",
    "paradigm",
    "estimator_info",
    "estimator_table",
    "estimator_markdown",
]

import pandas as pd

#: Legacy family codes retained for compatibility with the 2026 DMLR paper.
FAMILIES = {
    "TSML": "General purpose time series classifier",
    "Deep": "Deep learning, not specific to EEG",
    "EEG": "Classical spatial-filtering or Riemannian EEG pipeline",
    "EEG-DL": "Supervised deep neural architecture for EEG",
    "EEG-FM": "Pretrained EEG foundation model (and random-encoder controls)",
    "Standard": "Tabular classifier with no EEG or time-series specific step",
}

#: High-level bake-off paradigms shown as filter pills and matrix banners.
PARADIGMS = {
    "TSML": "General TSML",
    "EEG-Classical": "EEG Classical",
    "EEG-DL": "EEG Supervised DL",
    "EEG-FM": "EEG Foundation",
    "Tabular": "Tabular",
}

#: ``tsml-eval`` category directories present in the extended EEG study.
TSML_FAMILIES = {
    "Hybrid": "Hybrid ensembles",
    "ConvolutionBased": "Random convolutional kernels",
    "IntervalBased": "Summary and spectral interval forests / quantiles",
    "ShapeletBased": "Phase-independent subsequences (shapelets)",
    "DictionaryBased": "Symbolic Fourier / bag-of-words representations",
    "FeatureBased": "Spatial filters, band-power and tangent-space pipelines",
    "DistanceBased": "Riemannian geometry and template-correlation classifiers",
    "DeepLearning": "End-to-end neural networks and foundation backbones",
    "Tabular": "Flattened-channel standard tabular classifiers",
}

# Tuple schema:
#   (paradigm, tsml_family, legacy_family, base_method, library, is_ablation, in_bakeoff, description)
_REGISTRY: dict[str, tuple[str, str, str, str, str, bool, bool, str]] = {
    # --- General TSML (13 active + 5 legacy paper entries) ---
    "HC2-500-pc": (
        "TSML", "Hybrid", "TSML", "HC2", "aeon", False, True,
        "HIVE-COTE v2.0 (500-tree DrCIF, per-channel hybrid configuration)",
    ),
    "HC2-noTDE-500-pc": (
        "TSML", "Hybrid", "TSML", "HC2", "aeon", False, True,
        "HIVE-COTE v2.0 without TDE (Arsenal + DrCIF-500 + STC)",
    ),
    "Arsenal": (
        "TSML", "ConvolutionBased", "TSML", "Arsenal", "aeon", False, True,
        "Ensemble of ROCKET convolutional kernel classifiers",
    ),
    "MRHydra": (
        "TSML", "ConvolutionBased", "TSML", "MRHydra", "aeon", False, True,
        "MultiROCKET combined with Hydra competing convolutional dictionary",
    ),
    "DrCIF": (
        "TSML", "IntervalBased", "TSML", "DrCIF", "aeon", False, True,
        "Diverse Representation Canonical Interval Forest (default trees)",
    ),
    "DrCIF-500": (
        "TSML", "IntervalBased", "TSML", "DrCIF", "aeon", False, True,
        "Diverse Representation Canonical Interval Forest (500 trees)",
    ),
    "QUANT": (
        "TSML", "IntervalBased", "TSML", "QUANT", "aeon", False, True,
        "Dyadic interval quantile features with ExtraTrees",
    ),
    "STC-aeon": (
        "TSML", "ShapeletBased", "TSML", "STC", "aeon", False, True,
        "Randomised Shapelet Transform Classifier with Rotation Forest",
    ),
    "RDST": (
        "TSML", "ShapeletBased", "TSML", "RDST", "aeon", False, True,
        "Random Dilated Shapelet Transform with Ridge classifier",
    ),
    "TDE": (
        "TSML", "DictionaryBased", "TSML", "TDE", "aeon", False, True,
        "Temporal Dictionary Ensemble over SFA word histograms",
    ),
    "CNN": (
        "TSML", "DeepLearning", "Deep", "CNN", "aeon", False, True,
        "Time-CNN multivariate 1D convolutional network",
    ),
    "IT": (
        "TSML", "DeepLearning", "Deep", "InceptionTime", "aeon", False, True,
        "InceptionTime ensemble of multi-scale 1D Inception networks",
    ),
    "LITETime-MV": (
        "TSML", "DeepLearning", "Deep", "LITETime", "aeon", False, True,
        "Multivariate Light Inception with Boosting and depthwise convolutions",
    ),

    # --- EEG Foundation Models & Random-Init Controls (4 active) ---
    "CBraMod": (
        "EEG-FM", "DeepLearning", "EEG-FM", "CBraMod", "aeon-neuro (Foundation)", False, True,
        "Criss-cross Brain Foundation Model (pretrained patch transformer)",
    ),
    "CBraMod-random": (
        "EEG-FM", "DeepLearning", "EEG-FM", "CBraMod", "aeon-neuro (Foundation)", True, True,
        "CBraMod architecture initialised from random weights (no pretraining control)",
    ),
    "LaBraM": (
        "EEG-FM", "DeepLearning", "EEG-FM", "LaBraM", "aeon-neuro (Foundation)", False, True,
        "Large Brain Model pretrained neural tokenizer transformer (10-20 montage)",
    ),
    "LaBraM-random": (
        "EEG-FM", "DeepLearning", "EEG-FM", "LaBraM", "aeon-neuro (Foundation)", True, True,
        "LaBraM architecture initialised from random weights (no pretraining control)",
    ),

    # --- EEG Supervised Deep Learning: Braindecode / aeon-neuro (32 active) ---
    "ATCNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "ATCNet", "aeon-neuro (Braindecode)", False, True,
        "Attention Temporal Convolutional Network for EEG decoding",
    ),
    "AttentionBaseNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "AttentionBaseNet", "aeon-neuro (Braindecode)", False, True,
        "Channel-and-temporal attention convolutional baseline network",
    ),
    "BDTCN-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "BDTCN", "aeon-neuro (Braindecode)", False, True,
        "Braindecode dilated Temporal Convolutional Network",
    ),
    "BrainModule-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "BrainModule", "aeon-neuro (Braindecode)", False, True,
        "Meta AI wav2vec-style dilated convolutional EEG encoder",
    ),
    "ContraWR-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "ContraWR", "aeon-neuro (Braindecode)", False, True,
        "Contrastive world-representation STFT spectrogram 2D ResNet",
    ),
    "CTNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "CTNet", "aeon-neuro (Braindecode)", False, True,
        "Convolutional Transformer Network for motor imagery EEG",
    ),
    "Deep4Net-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "Deep4Net", "aeon-neuro (Braindecode)", False, True,
        "Schirrmeister et al. 4-block spatio-temporal ConvNet (DeepConvNet)",
    ),
    "EEGConformer-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "EEGConformer", "aeon-neuro (Braindecode)", False, True,
        "Compact spatio-temporal CNN + self-attention Transformer (Song et al.)",
    ),
    "EEGInceptionERP-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "EEGInceptionERP", "aeon-neuro (Braindecode)", False, True,
        "Multi-scale Inception CNN tailored to event-related potentials",
    ),
    "EEGInceptionMI-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "EEGInceptionMI", "aeon-neuro (Braindecode)", False, True,
        "Multi-scale Inception CNN tailored to motor imagery rhythms",
    ),
    "EEGITNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "EEGITNet", "aeon-neuro (Braindecode)", False, True,
        "Inception + dilated Temporal Convolutional Network for EEG",
    ),
    "EEGNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "EEGNet", "aeon-neuro (Braindecode)", False, True,
        "Lawhern et al. compact depthwise-separable spatio-temporal CNN",
    ),
    "EEGNeX-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "EEGNeX", "aeon-neuro (Braindecode)", False, True,
        "Pure ConvNeXt-inspired dilated spatio-temporal ConvNet (Chen et al.)",
    ),
    "EEGSimpleConv-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "EEGSimpleConv", "aeon-neuro (Braindecode)", False, True,
        "Lightweight 1D batch-normalised ResNet baseline for EEG",
    ),
    "EEGTCNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "EEGTCNet", "aeon-neuro (Braindecode)", False, True,
        "EEGNet front-end coupled to a dilated Temporal Convolutional Network",
    ),
    "FBCNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "FBCNet", "aeon-neuro (Braindecode)", False, True,
        "Filter-Bank Convolutional Network with variance temporal pooling",
    ),
    "FBLightConvNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "FBLightConvNet", "aeon-neuro (Braindecode)", False, True,
        "Filter-bank lightweight depthwise group-convolutional network",
    ),
    "FBMSNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "FBMSNet", "aeon-neuro (Braindecode)", False, True,
        "Filter-Bank Multi-Scale spatio-temporal CNN",
    ),
    "GCNsNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "GCNsNet", "aeon-neuro (Braindecode)", False, True,
        "Spectral Graph Convolutional Network over electrode topology",
    ),
    "IFNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "IFNet", "aeon-neuro (Braindecode)", False, True,
        "Interactive Frequency Convolutional Network (low/high band interplay)",
    ),
    "MSCFormer-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "MSCFormer", "aeon-neuro (Braindecode)", False, True,
        "Multi-scale convolutional Transformer for EEG classification",
    ),
    "MSVTNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "MSVTNet", "aeon-neuro (Braindecode)", False, True,
        "Multi-Scale Vision Transformer network for spatio-temporal EEG",
    ),
    "SCCNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "SCCNet", "aeon-neuro (Braindecode)", False, True,
        "Spatial-Component-wise Convolutional Network",
    ),
    "ShallowFBCSPNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "ShallowFBCSPNet", "aeon-neuro (Braindecode)", False, True,
        "Schirrmeister et al. shallow ConvNet mimicking log-bandpower FBCSP",
    ),
    "SincShallowNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "SincShallowNet", "aeon-neuro (Braindecode)", False, True,
        "Interpretable SincNet band-pass filter front-end + shallow spatial CNN",
    ),
    "SleepStagerChambon2018-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "SleepStagerChambon2018", "aeon-neuro (Braindecode)", False, True,
        "Chambon et al. spatial-temporal ConvNet originally designed for PSG staging",
    ),
    "SPARCNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "SPARCNet", "aeon-neuro (Braindecode)", False, True,
        "DenseNet-1D multi-layer dilated convolutional network (Jing et al.)",
    ),
    "SSTDPN-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "SSTDPN", "aeon-neuro (Braindecode)", False, True,
        "Spatial-Spectral-Temporal Dual-Prototype Network",
    ),
    "SyncNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "SyncNet", "aeon-neuro (Braindecode)", False, True,
        "Synchronised Gabor-wavelet filter-bank CNN for oscillatory phase/power",
    ),
    "TCFormer-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "TCFormer", "aeon-neuro (Braindecode)", False, True,
        "Temporal Convolutional Transformer hybrid network",
    ),
    "TIDNet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "TIDNet", "aeon-neuro (Braindecode)", False, True,
        "Thinker-Invariant DenseNet for cross-subject EEG decoding",
    ),
    "TMSANet-NB": (
        "EEG-DL", "DeepLearning", "EEG-DL", "TMSANet", "aeon-neuro (Braindecode)", False, True,
        "Temporal Multi-Scale Attention Network",
    ),

    # --- EEG Classical: FeatureBased (23 active) ---
    "AUG-TANG-SVM-MOABB": (
        "EEG-Classical", "FeatureBased", "EEG", "AugmentedTangentSVM", "aeon-neuro (MOABB)", False, True,
        "Augmented lag-embedded covariance tangent space + linear/RBF SVM",
    ),
    "CSP+LDA": (
        "EEG-Classical", "FeatureBased", "EEG", "CSP+LDA", "aeon-neuro (MNE + sklearn)", False, True,
        "Common Spatial Patterns (unfiltered) + Linear Discriminant Analysis",
    ),
    "CSP+LDA-BP140": (
        "EEG-Classical", "FeatureBased", "EEG", "CSP+LDA", "aeon-neuro (MNE + sklearn)", False, True,
        "1-40 Hz broadband pass + Common Spatial Patterns + LDA",
    ),
    "CSP+LDA-BP830": (
        "EEG-Classical", "FeatureBased", "EEG", "CSP+LDA", "aeon-neuro (MNE + sklearn)", False, True,
        "8-30 Hz mu/beta pass + Common Spatial Patterns + LDA",
    ),
    "CSP+SVM": (
        "EEG-Classical", "FeatureBased", "EEG", "CSP+SVM", "aeon-neuro (MNE + sklearn)", False, True,
        "Common Spatial Patterns (unfiltered) + Support Vector Machine",
    ),
    "CSP+SVM-BP140": (
        "EEG-Classical", "FeatureBased", "EEG", "CSP+SVM", "aeon-neuro (MNE + sklearn)", False, True,
        "1-40 Hz broadband pass + Common Spatial Patterns + SVM",
    ),
    "CSP+SVM-BP830": (
        "EEG-Classical", "FeatureBased", "EEG", "CSP+SVM", "aeon-neuro (MNE + sklearn)", False, True,
        "8-30 Hz mu/beta pass + Common Spatial Patterns + SVM",
    ),
    "CSP-LDA-MOABB": (
        "EEG-Classical", "FeatureBased", "EEG", "CSP+LDA", "aeon-neuro (MOABB)", False, True,
        "MOABB standard Common Spatial Patterns + shrinkage LDA pipeline",
    ),
    "CSP-SVM-MOABB": (
        "EEG-Classical", "FeatureBased", "EEG", "CSP+SVM", "aeon-neuro (MOABB)", False, True,
        "MOABB standard Common Spatial Patterns + SVM pipeline",
    ),
    "DE-LR": (
        "EEG-Classical", "FeatureBased", "EEG", "DifferentialEntropy", "aeon-neuro", False, True,
        "Canonical sub-band Differential Entropy spectral features + Logistic Regression",
    ),
    "DE-SVM": (
        "EEG-Classical", "FeatureBased", "EEG", "DifferentialEntropy", "aeon-neuro", False, True,
        "Canonical sub-band Differential Entropy spectral features + RBF SVM",
    ),
    "DLCSP-shLDA-MOABB": (
        "EEG-Classical", "FeatureBased", "EEG", "DLCSP+LDA", "aeon-neuro (MOABB)", False, True,
        "Diagonal-Loading regularised CSP + shrinkage LDA",
    ),
    "FBCSP-SVM-MOABB": (
        "EEG-Classical", "FeatureBased", "EEG", "FBCSP+SVM", "aeon-neuro (MOABB)", False, True,
        "Filter-Bank Common Spatial Patterns + mutual-information selection + SVM",
    ),
    "LogVar-LDA-MOABB": (
        "EEG-Classical", "FeatureBased", "EEG", "LogVariance", "aeon-neuro (MOABB)", False, True,
        "Per-channel log-variance features + shrinkage LDA",
    ),
    "LogVar-SVM-MOABB": (
        "EEG-Classical", "FeatureBased", "EEG", "LogVariance", "aeon-neuro (MOABB)", False, True,
        "Per-channel log-variance features + SVM",
    ),
    "TRCSP-LDA-MOABB": (
        "EEG-Classical", "FeatureBased", "EEG", "TRCSP+LDA", "aeon-neuro (MOABB)", False, True,
        "Tikhonov-Regularised Common Spatial Patterns + LDA (binary tasks)",
    ),
    "TSEN-MOABB": (
        "EEG-Classical", "FeatureBased", "EEG", "TangentSpace", "aeon-neuro (MOABB)", False, True,
        "Riemannian covariance tangent-space projection + ElasticNet logistic regression",
    ),
    "TSLR-MOABB": (
        "EEG-Classical", "FeatureBased", "EEG", "TangentSpace", "aeon-neuro (MOABB)", False, True,
        "Riemannian covariance tangent-space projection + L2 Logistic Regression",
    ),
    "TSLR-NB": (
        "EEG-Classical", "FeatureBased", "EEG", "TangentSpace", "aeon-neuro (PyRiemann)", False, True,
        "OAS-regularised SPD tangent-space projection + Logistic Regression",
    ),
    "TSSVM-MOABB": (
        "EEG-Classical", "FeatureBased", "EEG", "TangentSpace", "aeon-neuro (MOABB)", False, True,
        "Riemannian covariance tangent-space projection + linear SVM",
    ),
    "XDAWN": (
        "EEG-Classical", "FeatureBased", "EEG", "xDAWN", "aeon-neuro (MNE + sklearn)", False, True,
        "xDAWN evoked-potential spatial filtering + vectorised LDA",
    ),
    "xDAWN-LDA-MOABB": (
        "EEG-Classical", "FeatureBased", "EEG", "xDAWN", "aeon-neuro (MOABB)", False, True,
        "MOABB xDAWN spatial filtering + shrinkage LDA",
    ),
    "XdawnCov-TS-SVM-MOABB": (
        "EEG-Classical", "FeatureBased", "EEG", "xDAWNCov", "aeon-neuro (MOABB)", False, True,
        "xDAWN template-augmented block covariance + tangent-space SVM",
    ),

    # --- EEG Classical: DistanceBased (14 active) ---
    "ERPCov-MDM-MOABB": (
        "EEG-Classical", "DistanceBased", "EEG", "ERPCov+MDM", "aeon-neuro (MOABB)", False, True,
        "Class-prototype super-trial ERP covariance + Riemannian MDM",
    ),
    "FgMDM-MOABB": (
        "EEG-Classical", "DistanceBased", "EEG", "FgMDM", "aeon-neuro (MOABB)", False, True,
        "Fisher geodesic discriminant filtering in tangent space + Riemannian MDM",
    ),
    "MDM-MOABB": (
        "EEG-Classical", "DistanceBased", "EEG", "RiemannianMDM", "aeon-neuro (MOABB)", False, True,
        "MOABB Riemannian Minimum Distance to Mean over SPD covariances",
    ),
    "RiemannianKNN": (
        "EEG-Classical", "DistanceBased", "EEG", "RiemannianKNN", "aeon-neuro (PyRiemann)", False, True,
        "k-Nearest Neighbours under affine-invariant Riemannian SPD distance",
    ),
    "RiemannianKNN-OAS": (
        "EEG-Classical", "DistanceBased", "EEG", "RiemannianKNN", "aeon-neuro (PyRiemann)", False, True,
        "Riemannian k-NN with Oracle Approximating Shrinkage covariances",
    ),
    "RiemannianKNN-OAS-BP140": (
        "EEG-Classical", "DistanceBased", "EEG", "RiemannianKNN", "aeon-neuro (PyRiemann)", False, True,
        "1-40 Hz pass + OAS covariance + Riemannian k-NN",
    ),
    "RiemannianKNN-OAS-BP830": (
        "EEG-Classical", "DistanceBased", "EEG", "RiemannianKNN", "aeon-neuro (PyRiemann)", False, True,
        "8-30 Hz mu/beta pass + OAS covariance + Riemannian k-NN",
    ),
    "RiemannianMDM": (
        "EEG-Classical", "DistanceBased", "EEG", "RiemannianMDM", "aeon-neuro (PyRiemann)", False, True,
        "Riemannian Minimum Distance to Fréchet Mean over sample covariances",
    ),
    "RiemannianMDM-OAS": (
        "EEG-Classical", "DistanceBased", "EEG", "RiemannianMDM", "aeon-neuro (PyRiemann)", False, True,
        "Riemannian MDM with Oracle Approximating Shrinkage covariances",
    ),
    "RiemannianMDM-OAS-BP140": (
        "EEG-Classical", "DistanceBased", "EEG", "RiemannianMDM", "aeon-neuro (PyRiemann)", False, True,
        "1-40 Hz pass + OAS covariance + Riemannian MDM",
    ),
    "RiemannianMDM-OAS-BP830": (
        "EEG-Classical", "DistanceBased", "EEG", "RiemannianMDM", "aeon-neuro (PyRiemann)", False, True,
        "8-30 Hz mu/beta pass + OAS covariance + Riemannian MDM",
    ),
    "TemplateCCA-BP640": (
        "EEG-Classical", "DistanceBased", "EEG", "TemplateCCA", "aeon-neuro", False, True,
        "6-40 Hz pass + Individual Template Canonical Correlation Analysis",
    ),
    "TRCA-BP640": (
        "EEG-Classical", "DistanceBased", "EEG", "TRCA", "aeon-neuro", False, True,
        "6-40 Hz pass + Task-Related Component Analysis spatial filter correlation",
    ),
    "XdawnCov-MDM-MOABB": (
        "EEG-Classical", "DistanceBased", "EEG", "xDAWNCov", "aeon-neuro (MOABB)", False, True,
        "xDAWN template-augmented block covariance + Riemannian MDM",
    ),

    # --- Tabular Baselines (4 active) ---
    "LogisticRegression": (
        "Tabular", "Tabular", "Standard", "LogisticRegression", "scikit-learn", False, True,
        "L2-regularised Logistic Regression on concatenated channel values",
    ),
    "RandomForest": (
        "Tabular", "Tabular", "Standard", "RandomForest", "scikit-learn", False, True,
        "Random Forest on concatenated channel time points",
    ),
    "RotationForest": (
        "Tabular", "Tabular", "Standard", "RotationForest", "aeon", False, True,
        "Rotation Forest (PCA feature-subset rotations + decision trees)",
    ),
    "SVM": (
        "Tabular", "Tabular", "Standard", "SVM", "scikit-learn", False, True,
        "RBF-kernel Support Vector Machine on concatenated channel values",
    ),

    # --- Legacy 2026 DMLR Paper Identifiers (retained for paper reproduction) ---
    "HC2": (
        "TSML", "Hybrid", "TSML", "HC2", "aeon", False, False,
        "HIVE-COTE v2.0 (2026 DMLR paper configuration)",
    ),
    "STC": (
        "TSML", "ShapeletBased", "TSML", "STC", "aeon", False, False,
        "Shapelet Transform Classifier, an HC2 component (2026 paper)",
    ),
    "ROCKET": (
        "TSML", "ConvolutionBased", "TSML", "ROCKET", "aeon", False, False,
        "Random convolutional kernel transform (2026 paper)",
    ),
    "MiniROCKET": (
        "TSML", "ConvolutionBased", "TSML", "MiniROCKET", "aeon", False, False,
        "Deterministic MiniROCKET kernel transform (2026 paper)",
    ),
    "FreshPRINCE": (
        "TSML", "FeatureBased", "TSML", "FreshPRINCE", "aeon", False, False,
        "TSFresh summary features with Rotation Forest (2026 paper)",
    ),
    "EEGNet": (
        "EEG-DL", "DeepLearning", "EEG", "EEGNet", "Braindecode", False, False,
        "EEGNet (2026 DMLR paper configuration)",
    ),
    "DCN": (
        "EEG-DL", "DeepLearning", "EEG", "Deep4Net", "Braindecode", False, False,
        "DeepConvNet (2026 DMLR paper configuration)",
    ),
    "CSP-SVM": (
        "EEG-Classical", "FeatureBased", "EEG", "CSP+SVM", "MNE + scikit-learn", False, False,
        "Common Spatial Patterns then an SVM (2026 paper)",
    ),
    "R-MDM": (
        "EEG-Classical", "DistanceBased", "EEG", "RiemannianMDM", "pyriemann", False, False,
        "Riemannian minimum distance to mean (2026 paper)",
    ),
    "R-KNN": (
        "EEG-Classical", "DistanceBased", "EEG", "RiemannianKNN", "pyriemann", False, False,
        "Riemannian nearest neighbour (2026 paper)",
    ),
}

#: Structured metadata dictionary for every registered estimator.
ESTIMATOR_METADATA: dict[str, dict[str, object]] = {
    name: {
        "paradigm": par,
        "paradigm_label": PARADIGMS[par],
        "tsml_family": tsml_fam,
        "family": leg_fam,
        "base_method": base,
        "library": lib,
        "is_ablation": is_abl,
        "in_bakeoff": in_bo,
        "description": desc,
    }
    for name, (par, tsml_fam, leg_fam, base, lib, is_abl, in_bo, desc) in _REGISTRY.items()
}

#: Backwards-compatible ``name -> (family, library, description)`` mapping.
ESTIMATORS: dict[str, tuple[str, str, str]] = {
    name: (leg_fam, lib, desc)
    for name, (_, _, leg_fam, _, lib, _, _, desc) in _REGISTRY.items()
}

#: The 90 classifiers evaluated in the extended scalp EEG benchmark.
BAKEOFF_ESTIMATORS: list[str] = sorted(
    (name for name, meta in ESTIMATOR_METADATA.items() if meta["in_bakeoff"]),
    key=str.lower,
)

#: The eight classifiers compared in the 2026 DMLR paper, in the order of Table 2.
PAPER_ESTIMATORS = ["R-MDM", "CSP-SVM", "CNN", "IT", "EEGNet", "DCN", "HC2", "MRHydra"]


def family(name: str) -> str:
    """Return the legacy family code of an estimator, or ``""`` if unlisted."""
    return ESTIMATORS[name][0] if name in ESTIMATORS else ""


def paradigm(name: str) -> str:
    """Return the bake-off paradigm code of an estimator, or ``""`` if unlisted."""
    info = ESTIMATOR_METADATA.get(name)
    return str(info["paradigm"]) if info is not None else ""


def estimator_info(name: str) -> dict[str, object]:
    """Return structured metadata for ``name``, with sensible fallback for custom runs."""
    if name in ESTIMATOR_METADATA:
        return dict(ESTIMATOR_METADATA[name])
    if name == "Default":
        return {
            "paradigm": "Baseline",
            "paradigm_label": "Baseline",
            "tsml_family": "Baseline",
            "family": "Standard",
            "base_method": "Default",
            "library": "tsml-eval",
            "is_ablation": False,
            "in_bakeoff": False,
            "description": "Constant majority-class test floor",
        }
    return {
        "paradigm": "Other",
        "paradigm_label": "Other",
        "tsml_family": "Custom",
        "family": "",
        "base_method": name,
        "library": "custom",
        "is_ablation": name.endswith("-random"),
        "in_bakeoff": False,
        "description": name,
    }


def estimator_table(active_only: bool = False) -> pd.DataFrame:
    """Return the estimator metadata, one row per estimator."""
    records = {
        name: meta
        for name, meta in ESTIMATOR_METADATA.items()
        if not active_only or bool(meta["in_bakeoff"])
    }
    frame = pd.DataFrame.from_dict(records, orient="index")
    frame.index.name = "estimator"
    return frame


def estimator_markdown(active_only: bool = True) -> str:
    """Return the estimator metadata as a Markdown table, for the documentation."""
    header = ["Estimator", "Paradigm", "tsml-eval Family", "Library", "Description"]
    rows = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    names = BAKEOFF_ESTIMATORS if active_only else list(ESTIMATOR_METADATA)
    for name in names:
        meta = ESTIMATOR_METADATA[name]
        rows.append(
            f"| `{name}` | {meta['paradigm_label']} | {meta['tsml_family']} "
            f"| {meta['library']} | {meta['description']} |"
        )
    return "\n".join(rows)
