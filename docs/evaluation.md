# Evaluation

## Protocol

- **Fixed split (`resample 0`)**: Every classifier is fitted once on the supplied `TRAIN` partition and evaluated once on the supplied `TEST` partition (`testResample0.csv` in `tsml-eval`). Because EEG trials from a single recording or subject correlate strongly, random stratified resamples across `TRAIN + TEST` would leak subject/session identity.
- **Default hyperparameters**: Classifiers run with their standard benchmark configurations and fixed preprocessing tags (for example `-BP830` for 8–30 Hz motor-rhythm band-pass, `-BP140` for 1–40 Hz broadband pass, `-BP640` for 6–40 Hz SSVEP pass, `-MOABB` for canonical MOABB pipelines, and `-NB` for Braindecode neural architectures in `aeon-neuro`).
- **Explicit foundation controls**: Pretrained EEG foundation models (`CBraMod`, `LaBraM`) are accompanied by random-weight architectural controls (`CBraMod-random`, `LaBraM-random`) to separate pretraining transfer from backbone inductive bias.

## Metrics

Primary benchmark ranking uses **test balanced accuracy** (`balacc`) so class-imbalanced paradigms (such as P300 target detection, seizure detection, and sleep staging) cannot be gamed by majority-class prediction.

| File / Column key | Metric | Direction | Notes |
|---|---|---|---|
| `balacc` | Balanced accuracy | Higher is better | Unweighted mean recall across classes (primary ranking metric) |
| `accuracy` | Accuracy | Higher is better | Proportion of exact test matches |
| `auroc` | AUROC | Higher is better | Binary ROC AUC or macro one-vs-rest multi-class ROC AUC |
| `logloss` | Log loss | Lower is better | Cross-entropy with probabilities clipped to $[10^{-15}, 1]$ |

*(In the archived 2026 DMLR Multiverse layout under `results/eegbench_paper_2026/`, `f1`, `sensitivity`, and `specificity` are also stored.)*

Estimators that emit hard $0/1$ vote proportions (such as `Arsenal` or `MRHydra`) incur larger clipped `logloss` values; this reflects uncalibrated vote probabilities rather than a scoring error. Fit and predict wall-clock times are not ranked because neural models run on GPUs while CPU ensembles run single-threaded across heterogeneous cluster nodes.

## The Default Baseline

`Default` predicts the most frequent class in the **test** split for every test instance, using empirical test class proportions as probability estimates:
- `balacc` equals $1 / C$ for $C$ present classes;
- `auroc` equals $0.5$;
- `accuracy` equals the largest class proportion;
- `logloss` equals the empirical Shannon entropy of the test label distribution.

It serves on `datasets.html` and `matrix.html` as a strict no-skill floor (`Gain over Floor`).

## Where the Classifiers Live

EEGBench stores metadata and benchmark scores only—never classifier code:

| Paradigm | Home Repository |
|---|---|
| Classical EEG (CSP, xDAWN, CCA, TRCA, Riemannian), Braindecode wrappers (`*-NB`), and EEG foundation models (`CBraMod`, `LaBraM`) | [`aeon-neuro`](https://github.com/aeon-toolkit/aeon-neuro) (`aeon_neuro.classification`) |
| General multivariate TSC ports outside `aeon` | [`multiverse`](https://github.com/aeon-toolkit/multiverse) (`multiverse.classification`) |
| General TSML ensembles, convolutions, intervals, shapelets, dictionaries, and deep learners | [`aeon`](https://github.com/aeon-toolkit/aeon) (`aeon.classification`) |

## Result File Formats

`eegbench.experiments.tables` transparently reads two layouts:

1. **Wide summary CSVs** (active benchmark in `results/eegbench/`):
   - `accuracy.csv`, `balacc.csv`, `auroc.csv`, `logloss.csv` (`76` dataset rows &times; `90` classifier columns)
   - `datasets.csv` (`dataset,family,bci_type`) and `classifiers.csv` (`classifier,family`)
   - `Default/Default_<metric>.csv` for the constant test-majority floor
2. **Multiverse per-estimator CSVs** (archived 2026 paper results in `results/eegbench_paper_2026/` and `aeon-toolkit/multiverse`):
   - `<results_dir>/<estimator>/<estimator>_<metric>.csv` with `Resamples:` index header.

Convert or refresh between raw `tsml-eval` predictions, wide snapshots, and Multiverse directories with `eegbench.experiments.ingest`:

```bash
# Export wide summary CSVs directly from a tsml-eval category tree
python -m eegbench.experiments.ingest --wide-from D:/Results/EEG --out results/eegbench

# Sync from a dated wide snapshot directory
python -m eegbench.experiments.ingest --sync-from results/tsml-eval-20261111 --out results/eegbench

# Export Multiverse per-estimator directories from wide CSVs
python -m eegbench.experiments.ingest --out results/eegbench --to-multiverse results/multiverse_export

# Rebuild all HTML pages and Markdown tables
python -m eegbench.experiments.tables
```

## Registered Benchmark Estimators (90 Active)

<!-- ESTIMATORS:START -->
| Estimator | Paradigm | tsml-eval Family | Library | Description |
|---|---|---|---|---|
| `Arsenal` | General TSML | ConvolutionBased | aeon | Ensemble of ROCKET convolutional kernel classifiers |
| `ATCNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Attention Temporal Convolutional Network for EEG decoding |
| `AttentionBaseNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Channel-and-temporal attention convolutional baseline network |
| `AUG-TANG-SVM-MOABB` | EEG Classical | FeatureBased | aeon-neuro (MOABB) | Augmented lag-embedded covariance tangent space + linear/RBF SVM |
| `BDTCN-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Braindecode dilated Temporal Convolutional Network |
| `BrainModule-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Meta AI wav2vec-style dilated convolutional EEG encoder |
| `CBraMod` | EEG Foundation | DeepLearning | aeon-neuro (Foundation) | Criss-cross Brain Foundation Model (pretrained patch transformer) |
| `CBraMod-random` | EEG Foundation | DeepLearning | aeon-neuro (Foundation) | CBraMod architecture initialised from random weights (no pretraining control) |
| `CNN` | General TSML | DeepLearning | aeon | Time-CNN multivariate 1D convolutional network |
| `ContraWR-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Contrastive world-representation STFT spectrogram 2D ResNet |
| `CSP+LDA` | EEG Classical | FeatureBased | aeon-neuro (MNE + sklearn) | Common Spatial Patterns (unfiltered) + Linear Discriminant Analysis |
| `CSP+LDA-BP140` | EEG Classical | FeatureBased | aeon-neuro (MNE + sklearn) | 1-40 Hz broadband pass + Common Spatial Patterns + LDA |
| `CSP+LDA-BP830` | EEG Classical | FeatureBased | aeon-neuro (MNE + sklearn) | 8-30 Hz mu/beta pass + Common Spatial Patterns + LDA |
| `CSP+SVM` | EEG Classical | FeatureBased | aeon-neuro (MNE + sklearn) | Common Spatial Patterns (unfiltered) + Support Vector Machine |
| `CSP+SVM-BP140` | EEG Classical | FeatureBased | aeon-neuro (MNE + sklearn) | 1-40 Hz broadband pass + Common Spatial Patterns + SVM |
| `CSP+SVM-BP830` | EEG Classical | FeatureBased | aeon-neuro (MNE + sklearn) | 8-30 Hz mu/beta pass + Common Spatial Patterns + SVM |
| `CSP-LDA-MOABB` | EEG Classical | FeatureBased | aeon-neuro (MOABB) | MOABB standard Common Spatial Patterns + shrinkage LDA pipeline |
| `CSP-SVM-MOABB` | EEG Classical | FeatureBased | aeon-neuro (MOABB) | MOABB standard Common Spatial Patterns + SVM pipeline |
| `CTNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Convolutional Transformer Network for motor imagery EEG |
| `DE-LR` | EEG Classical | FeatureBased | aeon-neuro | Canonical sub-band Differential Entropy spectral features + Logistic Regression |
| `DE-SVM` | EEG Classical | FeatureBased | aeon-neuro | Canonical sub-band Differential Entropy spectral features + RBF SVM |
| `Deep4Net-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Schirrmeister et al. 4-block spatio-temporal ConvNet (DeepConvNet) |
| `DLCSP-shLDA-MOABB` | EEG Classical | FeatureBased | aeon-neuro (MOABB) | Diagonal-Loading regularised CSP + shrinkage LDA |
| `DrCIF` | General TSML | IntervalBased | aeon | Diverse Representation Canonical Interval Forest (default trees) |
| `DrCIF-500` | General TSML | IntervalBased | aeon | Diverse Representation Canonical Interval Forest (500 trees) |
| `EEGConformer-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Compact spatio-temporal CNN + self-attention Transformer (Song et al.) |
| `EEGInceptionERP-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Multi-scale Inception CNN tailored to event-related potentials |
| `EEGInceptionMI-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Multi-scale Inception CNN tailored to motor imagery rhythms |
| `EEGITNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Inception + dilated Temporal Convolutional Network for EEG |
| `EEGNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Lawhern et al. compact depthwise-separable spatio-temporal CNN |
| `EEGNeX-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Pure ConvNeXt-inspired dilated spatio-temporal ConvNet (Chen et al.) |
| `EEGSimpleConv-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Lightweight 1D batch-normalised ResNet baseline for EEG |
| `EEGTCNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | EEGNet front-end coupled to a dilated Temporal Convolutional Network |
| `ERPCov-MDM-MOABB` | EEG Classical | DistanceBased | aeon-neuro (MOABB) | Class-prototype super-trial ERP covariance + Riemannian MDM |
| `FBCNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Filter-Bank Convolutional Network with variance temporal pooling |
| `FBCSP-SVM-MOABB` | EEG Classical | FeatureBased | aeon-neuro (MOABB) | Filter-Bank Common Spatial Patterns + mutual-information selection + SVM |
| `FBLightConvNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Filter-bank lightweight depthwise group-convolutional network |
| `FBMSNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Filter-Bank Multi-Scale spatio-temporal CNN |
| `FgMDM-MOABB` | EEG Classical | DistanceBased | aeon-neuro (MOABB) | Fisher geodesic discriminant filtering in tangent space + Riemannian MDM |
| `GCNsNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Spectral Graph Convolutional Network over electrode topology |
| `HC2-500-pc` | General TSML | Hybrid | aeon | HIVE-COTE v2.0 (500-tree DrCIF, per-channel hybrid configuration) |
| `HC2-noTDE-500-pc` | General TSML | Hybrid | aeon | HIVE-COTE v2.0 without TDE (Arsenal + DrCIF-500 + STC) |
| `IFNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Interactive Frequency Convolutional Network (low/high band interplay) |
| `IT` | General TSML | DeepLearning | aeon | InceptionTime ensemble of multi-scale 1D Inception networks |
| `LaBraM` | EEG Foundation | DeepLearning | aeon-neuro (Foundation) | Large Brain Model pretrained neural tokenizer transformer (10-20 montage) |
| `LaBraM-random` | EEG Foundation | DeepLearning | aeon-neuro (Foundation) | LaBraM architecture initialised from random weights (no pretraining control) |
| `LITETime-MV` | General TSML | DeepLearning | aeon | Multivariate Light Inception with Boosting and depthwise convolutions |
| `LogisticRegression` | Tabular | Tabular | scikit-learn | L2-regularised Logistic Regression on concatenated channel values |
| `LogVar-LDA-MOABB` | EEG Classical | FeatureBased | aeon-neuro (MOABB) | Per-channel log-variance features + shrinkage LDA |
| `LogVar-SVM-MOABB` | EEG Classical | FeatureBased | aeon-neuro (MOABB) | Per-channel log-variance features + SVM |
| `MDM-MOABB` | EEG Classical | DistanceBased | aeon-neuro (MOABB) | MOABB Riemannian Minimum Distance to Mean over SPD covariances |
| `MRHydra` | General TSML | ConvolutionBased | aeon | MultiROCKET combined with Hydra competing convolutional dictionary |
| `MSCFormer-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Multi-scale convolutional Transformer for EEG classification |
| `MSVTNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Multi-Scale Vision Transformer network for spatio-temporal EEG |
| `QUANT` | General TSML | IntervalBased | aeon | Dyadic interval quantile features with ExtraTrees |
| `RandomForest` | Tabular | Tabular | scikit-learn | Random Forest on concatenated channel time points |
| `RDST` | General TSML | ShapeletBased | aeon | Random Dilated Shapelet Transform with Ridge classifier |
| `RiemannianKNN` | EEG Classical | DistanceBased | aeon-neuro (PyRiemann) | k-Nearest Neighbours under affine-invariant Riemannian SPD distance |
| `RiemannianKNN-OAS` | EEG Classical | DistanceBased | aeon-neuro (PyRiemann) | Riemannian k-NN with Oracle Approximating Shrinkage covariances |
| `RiemannianKNN-OAS-BP140` | EEG Classical | DistanceBased | aeon-neuro (PyRiemann) | 1-40 Hz pass + OAS covariance + Riemannian k-NN |
| `RiemannianKNN-OAS-BP830` | EEG Classical | DistanceBased | aeon-neuro (PyRiemann) | 8-30 Hz mu/beta pass + OAS covariance + Riemannian k-NN |
| `RiemannianMDM` | EEG Classical | DistanceBased | aeon-neuro (PyRiemann) | Riemannian Minimum Distance to Fréchet Mean over sample covariances |
| `RiemannianMDM-OAS` | EEG Classical | DistanceBased | aeon-neuro (PyRiemann) | Riemannian MDM with Oracle Approximating Shrinkage covariances |
| `RiemannianMDM-OAS-BP140` | EEG Classical | DistanceBased | aeon-neuro (PyRiemann) | 1-40 Hz pass + OAS covariance + Riemannian MDM |
| `RiemannianMDM-OAS-BP830` | EEG Classical | DistanceBased | aeon-neuro (PyRiemann) | 8-30 Hz mu/beta pass + OAS covariance + Riemannian MDM |
| `RotationForest` | Tabular | Tabular | aeon | Rotation Forest (PCA feature-subset rotations + decision trees) |
| `SCCNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Spatial-Component-wise Convolutional Network |
| `ShallowFBCSPNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Schirrmeister et al. shallow ConvNet mimicking log-bandpower FBCSP |
| `SincShallowNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Interpretable SincNet band-pass filter front-end + shallow spatial CNN |
| `SleepStagerChambon2018-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Chambon et al. spatial-temporal ConvNet originally designed for PSG staging |
| `SPARCNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | DenseNet-1D multi-layer dilated convolutional network (Jing et al.) |
| `SSTDPN-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Spatial-Spectral-Temporal Dual-Prototype Network |
| `STC-aeon` | General TSML | ShapeletBased | aeon | Randomised Shapelet Transform Classifier with Rotation Forest |
| `SVM` | Tabular | Tabular | scikit-learn | RBF-kernel Support Vector Machine on concatenated channel values |
| `SyncNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Synchronised Gabor-wavelet filter-bank CNN for oscillatory phase/power |
| `TCFormer-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Temporal Convolutional Transformer hybrid network |
| `TDE` | General TSML | DictionaryBased | aeon | Temporal Dictionary Ensemble over SFA word histograms |
| `TemplateCCA-BP640` | EEG Classical | DistanceBased | aeon-neuro | 6-40 Hz pass + Individual Template Canonical Correlation Analysis |
| `TIDNet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Thinker-Invariant DenseNet for cross-subject EEG decoding |
| `TMSANet-NB` | EEG Supervised DL | DeepLearning | aeon-neuro (Braindecode) | Temporal Multi-Scale Attention Network |
| `TRCA-BP640` | EEG Classical | DistanceBased | aeon-neuro | 6-40 Hz pass + Task-Related Component Analysis spatial filter correlation |
| `TRCSP-LDA-MOABB` | EEG Classical | FeatureBased | aeon-neuro (MOABB) | Tikhonov-Regularised Common Spatial Patterns + LDA (binary tasks) |
| `TSEN-MOABB` | EEG Classical | FeatureBased | aeon-neuro (MOABB) | Riemannian covariance tangent-space projection + ElasticNet logistic regression |
| `TSLR-MOABB` | EEG Classical | FeatureBased | aeon-neuro (MOABB) | Riemannian covariance tangent-space projection + L2 Logistic Regression |
| `TSLR-NB` | EEG Classical | FeatureBased | aeon-neuro (PyRiemann) | OAS-regularised SPD tangent-space projection + Logistic Regression |
| `TSSVM-MOABB` | EEG Classical | FeatureBased | aeon-neuro (MOABB) | Riemannian covariance tangent-space projection + linear SVM |
| `XDAWN` | EEG Classical | FeatureBased | aeon-neuro (MNE + sklearn) | xDAWN evoked-potential spatial filtering + vectorised LDA |
| `xDAWN-LDA-MOABB` | EEG Classical | FeatureBased | aeon-neuro (MOABB) | MOABB xDAWN spatial filtering + shrinkage LDA |
| `XdawnCov-MDM-MOABB` | EEG Classical | DistanceBased | aeon-neuro (MOABB) | xDAWN template-augmented block covariance + Riemannian MDM |
| `XdawnCov-TS-SVM-MOABB` | EEG Classical | FeatureBased | aeon-neuro (MOABB) | xDAWN template-augmented block covariance + tangent-space SVM |
<!-- ESTIMATORS:END -->
