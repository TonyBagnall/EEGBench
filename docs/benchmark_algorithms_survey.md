# External EEG Benchmark Algorithms & Pipelines Survey

*Survey date: April 2026 — compiled by inspecting live benchmark APIs, model registries, configuration directories, and source implementations across external EEG benchmarks, compared against `C:\Code\aeon-neuro`.*

---

## Executive Summary & Scope

This document inventories every EEG classification/decoding algorithm and pipeline evaluated across eight external EEG benchmark platforms and libraries, normalises naming aliases across sites, maps hard input constraints (sampling frequency, electrode names/3D coordinates, stimulation frequencies, window length), and identifies gaps relative to `aeon-neuro`.

### Benchmarks Surveyed

| # | Benchmark / Library | Primary Reference | Upstream Repository & Live Site | Scope & Evaluated Model Count |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **MOABB** | Jayaram & Barachant (2018); Chevallier et al. (2024) | [`NeuroTechX/moabb`](https://github.com/NeuroTechX/moabb) · [`moabb.neurotechx.com`](https://moabb.neurotechx.com/) | **27** pipeline configs (`moabb/pipelines/configs/`) + **6** retired deep-learning baselines in published MI/ERP/SSVEP benchmark CSVs; c-VEP paradigm added in v1.0+ |
| **2a** | **Braindecode** | Schirrmeister et al. (2017); Aristimunha et al. (2025/2026) | [`braindecode/braindecode`](https://github.com/braindecode/braindecode) · [`braindecode.org`](https://braindecode.org/) | **84** neural classes in `braindecode.models` (`summary.csv` / `__init__.py`): **69** EEG-capable classes (**39** supervised architectures + **30** foundation/tokenizer classes) and **15** iEEG/MEG/sEMG-only classes across **9** official categories |
| **2b** | **OpenEEGBench** | Braindecode team (2026) | [`braindecode/OpenEEGBench`](https://github.com/braindecode/OpenEEGBench) · [HF Space API](https://braindecode-openeegbench.hf.space/api/leaderboard) | **7** built-in foundation-model backbones (`ALL_BACKBONES`) across **9** adaptation strategies; **5** foundation models (**10** probe + full-finetune entries) currently live on the leaderboard; **0** classical/supervised baselines |
| **3** | **EEG-Arena / EEG.FM** | Chen et al. (2026), `arXiv:2609.32743` | [`OrangeP0P/eeg-arena`](https://github.com/OrangeP0P/eeg-arena) · [`eeg.fm`](https://eeg.fm/benchmarks/overall-performance/) | **55** evaluated configurations across 29 datasets / 74 tasks: **30** EEG foundation-model variants (**20** distinct FM families) + **25** task-specific supervised baselines |
| **4** | **NeuralBench** | Banville et al. (2026), `arXiv:2605.08495` | [`facebookresearch/neuroai`](https://github.com/facebookresearch/neuroai/tree/main/neuralbench-repo) | **14** core trainable EEG architectures (**8** task-specific deep learners + **6** foundation models) + **6** classical/constant baselines (`chance`, `dummy`, `CovTsLR`, `XdawnTsLR`, `CoSpectraLogLR`, `CovTsRidge`), plus extra repo YAML configs (`EEGNeX`, `SimpleConv`, `MaeEncoder`) |
| **5** | **AdaBrain-Bench** | Wang et al. (2025), `arXiv:2505.17099` | [`Jamine-W/AdaBrain-Bench`](https://github.com/Jamine-W/AdaBrain-Bench) | **8** models across multi-task BCI transfers: **4** supervised baselines + **4** EEG foundation models |
| **6** | **ETH-DISCO EEG-Bench** | ETH-DISCO (2024/2025) | [`ETH-DISCO/EEG-Bench`](https://github.com/ETH-DISCO/EEG-Bench) | **7** distinct pipelines (**3** foundation models + **4** classical LDA/SVM pipelines on CSP or `brainfeatures`); **0** supervised deep baselines |
| **7a** | **OmniEEG-Bench** | Lu et al. (2026) | [`ncclab-sustech/omni-eegbench`](https://github.com/ncclab-sustech/omni-eegbench) | **12** active EEG models across Type-I to Type-VI task categories: **10** EEG foundation models + **2** supervised deep baselines (`EEGNet`, `EEGConformer`), plus **1** iEEG adapter (`Brant`) in `models/factory.py` |
| **7b** | **EEGDash** | Delorme, Aristimunha et al. (2025/2026) | [`eegdash/EEGDash`](https://github.com/eegdash/EEGDash) · [`eegdash.org`](https://eegdash.org/) | Data archive (>700 BIDS/Zarr datasets) + hand-crafted feature bank (`eegdash.features`), **not** a multi-algorithm leaderboard; ships starter baselines (`EEGNeX`, `LogisticRegression` on `eegdash.features`) |

### `aeon-neuro` Baseline Reference Layers (`C:\Code\aeon-neuro\aeon_neuro\classification\`)

To make status comparisons unambiguous in Parts 2 and 3, each algorithm's current coverage in `aeon-neuro` is classified into one of six states:

1. **`Standalone`** — First-class `BaseClassifier` in `aeon_neuro.classification`:
   - *Feature-based*: `CSPClassifier`, `XDAWNClassifier`, `DifferentialEntropyClassifier`
   - *Distance / template-based*: `RiemannianMDMClassifier`, `RiemannianKNNClassifier`, `TRCAClassifier`, `TemplateCCAClassifier`
   - *Supervised deep learning*: `EEGNetClassifier`, `DeepConvNetClassifier`, `EEGConformerClassifier`
   - *Pretrained foundation models (frozen linear probe via `RidgeClassifierCV`)*: `CBraModClassifier`, `LabramClassifier`
   - *Re-exported `aeon` general multivariate TSC baselines*: `HIVECOTEV2`, `MultiRocketHydraClassifier`, `InceptionTimeClassifier`, `TimeCNNClassifier`
2. **`BraindecodeClassifier (tested)`** — Wrapped by `BraindecodeClassifier` (`deep_learning/_braindecode.py`) and explicitly validated in `SUPPORTED_MODELS` (**36** architectures, trained end-to-end from random initialisation).
3. **`BraindecodeClassifier (untested in BD)`** — Present in `braindecode.models` (an existing dependency) and instantiable via `BraindecodeClassifier` if it emits 2D `(batch, n_classes)` logits, or requiring minor output/checkpoint handling, but **not** yet in `SUPPORTED_MODELS`.
4. **`MOABBPipelineClassifier`** — Available in `classification/experimental/_neuralbench.py` (`MOABBPipelineClassifier` / `MOABBTSLRClassifier`, **17** classical MI and ERP/P300 pipelines).
5. **`NeuralBench*`** — Available in `classification/experimental/_neuralbench.py` (`NeuralBenchTSLRClassifier`, `NeuralBenchDeepClassifier`, `NeuralBenchCTNetClassifier`).
6. **`Missing`** — Not implemented or wrapped anywhere in `aeon-neuro`.

---

## Part 1 — Per-Benchmark Inventory

Each subsection preserves the upstream benchmark's own organisation and naming while mapping benchmark-specific aliases to canonical method names and primary citations.

---

### 1.1 MOABB (`NeuroTechX/moabb` & `moabb.neurotechx.com`)

MOABB (*Mother of All BCI Benchmarks*; Jayaram & Barachant, 2018; Chevallier et al., 2024, *J. Neural Eng.*) organises pipelines along two axes: **BCI Paradigm** (`MotorImagery` / `LeftRightImagery`, `P300` / `ERP`, `SSVEP` / `FilterBankSSVEP`, `CVEP`) and **Pipeline Family** (`Riemannian`, `CSP / Spatial Filtering`, `Template / CCA / TRCA`, `Log-Variance`, `Deep Learning`). Inspection of `moabb/pipelines/configs/` (**27** config files), `moabb/pipelines/`, and `results/*.csv` yields the complete inventory below.

#### 1.1.1 Motor Imagery (`LeftRightImagery`, `MotorImagery`)

| MOABB Config / CSV Alias | Canonical Method Name | Pipeline Type | Pipeline Steps & Key Details |
| :--- | :--- | :--- | :--- |
| `CSP + LDA` (`CSP.yml`, `CSP+LDA`) | Common Spatial Patterns + Shrinkage LDA (Ramoser et al., 2000; Blankertz et al., 2008) | CSP / Spatial Filtering | `Covariances('scm')` → `CSP(nfilter=8)` → `LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')` (8–32 Hz) |
| `CSP + SVM Grid` (`CSP_SVM_grid.yml`, `CSP+SVM`) | CSP + Tuned Kernel/Linear SVM | CSP / Spatial Filtering | `Covariances('scm')` → `CSP(nfilter=8)` → `GridSearchCV(SVC)` |
| `RegCSP + shLDA` (`regCSP+shLDA.yml`, `DLCSPauto+shLDA`) | Diagonal-Loading Regularised CSP + Shrinkage LDA (Lotte & Guan, 2011) | CSP / Spatial Filtering | `mne.decoding.CSP(n_components=8, reg='oas')` → `LDA(solver='lsqr', shrinkage='auto')` |
| `TRCSP + LDA` (`WTRCSP.py`, `TRCSP+LDA`) | Weighted Tikhonov-Regularised CSP + LDA (Lotte & Guan, 2011) | CSP / Spatial Filtering | `TRCSP(nfilter=6)` → shrinkage `LDA` (**binary 2-class only**; excluded from multi-class MI CSVs) |
| `FilterBank + SVM` (`FBCSP.py`, `FilterBank+SVM`) | Filter-Bank CSP + Mutual-Information Feature Selection + SVM (Ang et al., 2008) | CSP / Spatial Filtering | `FilterBank` (6× 4 Hz bands across 8–36 Hz) → `CSP(n_components=4)` per band → `SelectKBest(mutual_info_classif, k=10)` → linear `SVC` |
| `MDM` (`MDM.yml`) | Minimum Distance to Riemannian Mean (Barachant et al., 2012) | Riemannian | `Covariances('scm')` → `pyriemann.classification.MDM(metric='riemann')` |
| `FgMDM` (`FgMDM.yml`) | Fisher Geodesic Discriminant Analysis + MDM (Barachant et al., 2010) | Riemannian | `Covariances('scm')` → `FgMDM(metric='riemann')` (tangent-space Fisher geodesic filtering prior to MDM) |
| `Tangent Space LR` (`TSLR.yml`, `TS+LR`) | Riemannian Tangent Space + Logistic Regression (Barachant et al., 2013) | Riemannian | `Covariances('oas')` → `TangentSpace(metric='riemann')` → `LogisticRegression(penalty='l2')` |
| `Tangent Space SVM Grid` (`TSSVM_grid.yml`, `TS+SVM`) | Riemannian Tangent Space + Grid-Search SVM | Riemannian | `Covariances('oas')` → `TangentSpace(metric='riemann')` → `GridSearchCV(SVC)` |
| `Tangent Space ElasticNet` (`EN_grid.yml`, `TS+EL`) | Riemannian Tangent Space + Elastic-Net Logistic Regression | Riemannian | `Covariances('oas')` → `TangentSpace(metric='riemann')` → `GridSearchCV(LogisticRegression(penalty='elasticnet', solver='saga'))` |
| `ACM + TS + SVM` (`AUG_TANG_SVM_grid.yml`, `ACM+TS+SVM`) | Augmented Covariance Matrix + Tangent Space + SVM (Carrara & Papadopoulo, 2023) | Riemannian | `AugmentedDataset` (lag-embedded multi-delay channels, `order`, `lag`) → `Covariances('scm')` → `TangentSpace` → `SVC` (grid-searched) |
| `Log Variance LDA` (`LogVar.yml`, `LogVariance+LDA`) | Channel Log-Variance + Shrinkage LDA | Log-Variance / Spectral | `LogVariance()` ($\log \operatorname{diag}(\Sigma)$) → `LDA(solver='lsqr', shrinkage='auto')` |
| `Log Variance SVM Grid` (`LogVar_grid.yml`, `LogVariance+SVM`) | Channel Log-Variance + Grid-Search SVM | Log-Variance / Spectral | `LogVariance()` → `GridSearchCV(SVC)` |
| `ShallowConvNet` (`KerasShallowConvNet`, retired to Braindecode) | ShallowFBCSPNet (Schirrmeister et al., 2017) | Deep Learning | Evaluated in Chevallier et al. (2024) `results/*MI*.csv`; MOABB v1.1+ delegates DL pipelines to `braindecode` via skorch |
| `DeepConvNet` (`KerasDeepConvNet`, retired to Braindecode) | Deep4Net (Schirrmeister et al., 2017) | Deep Learning | Evaluated in Chevallier et al. (2024) `results/*MI*.csv`; delegated to `braindecode` |
| `EEGNet_8_2` (`KerasEEGNet_8_2`, retired to Braindecode) | EEGNet-8,2 (Lawhern et al., 2018) | Deep Learning | Evaluated in Chevallier et al. (2024) `results/*MI*.csv`; delegated to `braindecode` |
| `EEGITNet` (`KerasEEGITNet`, retired to Braindecode) | EEG-ITNet (Salami et al., 2022) | Deep Learning | Inception + dilated TCN; evaluated in Chevallier et al. (2024) `results/*MI*.csv`; delegated to `braindecode` |
| `EEGNeX` (`KerasEEGNeX`, retired to Braindecode) | EEGNeX-8,32 (Chen et al., 2024) | Deep Learning | ConvNeXt-inspired pure CNN; evaluated in Chevallier et al. (2024) `results/*MI*.csv`; delegated to `braindecode` |
| `EEGTCNet` (`KerasEEGTCNet`, retired to Braindecode) | EEG-TCNet (Ingolfsson et al., 2020) | Deep Learning | EEGNet + temporal convolutional network; evaluated in Chevallier et al. (2024) `results/*MI*.csv`; delegated to `braindecode` |

*Note on MOABB transfer-learning tutorials*: MOABB examples also demonstrate cross-subject/session Riemannian alignment pipelines (`RPA` — Riemannian Procrustes Analysis via `pyriemann.transfer`, `MDM` with `TLCenter`/`TLStretch`/`TLRotate`), though these are not standalone entries in `pipelines/configs/`.

#### 1.1.2 ERP / P300 (`P300`)

| MOABB Config / CSV Alias | Canonical Method Name | Pipeline Type | Pipeline Steps & Key Details |
| :--- | :--- | :--- | :--- |
| `xDAWN + LDA` (`xDAWN_LDA.yml`, `XDAWN+LDA`) | xDAWN Spatial Filtering + Vectorised Shrinkage LDA (Rivet et al., 2009) | CSP / Spatial Filtering (ERP) | `Xdawn(nfilter=2, estimator='scm')` → `Vectorizer()` → `LDA(solver='lsqr', shrinkage='auto')` (1–24 Hz) |
| `XdawnCovariances + MDM` (`XdawnCov_MDM.yml`, `XDAWNCov+MDM`) | xDAWN Augmented ERP Covariance + MDM (Barachant & Congedo, 2014) | Riemannian (ERP) | `XdawnCovariances(nfilter=5, estimator='lwf', xdawn_estimator='scm')` → `MDM(metric='riemann')` |
| `XdawnCovariances + TangentSpace + SVM` (`XdawnCov_TS_SVM.yml`, `XDAWNCov+TS+SVM`) | xDAWN Covariance + Tangent Space + Linear/RBF SVM (Barachant & Congedo, 2014) | Riemannian (ERP) | `XdawnCovariances(nfilter=5, estimator='lwf', xdawn_estimator='scm')` → `TangentSpace` → `SVC` |
| `ERPCovariances + MDM` (`ERPCov_MDM.yml`, `ERPCov+MDM`) | Prototype-Concatenated ERP Covariance + MDM (Barachant & Congedo, 2014) | Riemannian (ERP) | `ERPCovariances(estimator='scm')` → `MDM(metric='riemann')` |
| `ERPCov(svd_n=4)+MDM` (in `results_P300.csv`) | SVD-Reduced ERP Covariance + MDM | Riemannian (ERP) | `ERPCovariances(estimator='scm', svd=4)` → `MDM(metric='riemann')` |

#### 1.1.3 SSVEP (`SSVEP`, `FilterBankSSVEP`)

| MOABB Config / CSV Alias | Canonical Method Name | Pipeline Type | Pipeline Steps & Key Details |
| :--- | :--- | :--- | :--- |
| `SSVEP CCA` (`CCA-SSVEP.yml`) | Standard Sinusoidal-Reference Canonical Correlation Analysis (Lin et al., 2006) | Template / CCA / TRCA | `SSVEP_CCA(n_harmonics=3)` — requires known per-class flicker frequencies `freqs` (training-free) |
| `itCCA-SSVEP` (`itCCA-SSVEP.yml`) | Individual Template CCA (Bin et al., 2011; Wang et al., 2014) | Template / CCA / TRCA | `SSVEP_itCCA()` — replaces synthetic sinusoids with subject-averaged class EEG templates |
| `eCCA-SSVEP` (`eCCA-SSVEP.yml`) | Extended CCA (Chen et al., 2015) | Template / CCA / TRCA | `SSVEP_eCCA(n_harmonics=3)` — combines sinusoidal reference CCA and individual class templates across 4 projections; requires `freqs` |
| `MsetCCA-SSVEP` (`MsetCCA-SSVEP.yml`) | Multiset CCA (Zhang et al., 2014) | Template / CCA / TRCA | `SSVEP_MsetCCA(n_filters=2)` — learns common reference signals jointly across training trials per frequency class |
| `SSCOR-SSVEP` (`SSCOR-SSVEP.yml`) | Sum of Squared Correlations (Kumar & Reddy, 2019) | Template / CCA / TRCA | `SSVEP_SSCOR(n_filters=1)` — maximises sum of squared inter-trial correlations against class average template |
| `TRCA-SSVEP` (`TRCA-SSVEP.yml`) | Task-Related Component Analysis (Nakanishi et al., 2018) | Template / CCA / TRCA | `SSVEP_TRCA(n_fbands=5, ensemble=True, estimator='scm')` — filter-bank ensemble TRCA; uses harmonic sub-bands (`freqs`) |
| `TRCA-R-SSVEP` (`TRCA_R-SSVEP.yml`) | Reference-Projected TRCA (Wong et al., 2020) | Template / CCA / TRCA | `SSVEP_TRCA_R(n_fbands=5, n_harmonics=3)` — orthogonal reference projection + filter-bank TRCA; requires `freqs` |
| `TDCA-SSVEP` (`TDCA-SSVEP.yml`) | Task-Discriminant Component Analysis (Liu et al., 2021) | Template / CCA / TRCA | `SSVEP_TDCA(n_fbands=5, n_harmonics=3, l=5)` — delay-augmented + sinusoidal-projected 2D discriminant spatial filtering; requires `freqs` |
| `MDM-SSVEP` (`MDM-SSVEP.yml`) | Filter-Bank Extended SSVEP Covariance + MDM (Kalunga et al., 2016) | Riemannian (SSVEP) | `ExtendedSSVEPSignal` (stacks `FilterBankSSVEP` sub-bands around target `freqs`) → `Covariances('lwf')` → `MDM` |
| `SSVEP Tangent Space LR` (`TSLR-SSVEP.yml`, `TSLR-SSVEP`) | Filter-Bank Extended SSVEP Covariance + Tangent Space + LR (Kalunga et al., 2016) | Riemannian (SSVEP) | `ExtendedSSVEPSignal` → `Covariances('lwf')` → `TangentSpace` → `LogisticRegression` |
| `SSVEP Tangent Space SVM` (`TSSVM-SSVEP.yml`, `TSSVM-SSVEP`) | Filter-Bank Extended SSVEP Covariance + Tangent Space + SVM | Riemannian (SSVEP) | `ExtendedSSVEPSignal` → `Covariances('lwf')` → `TangentSpace` → `SVC` |

#### 1.1.4 c-VEP (`CVEP`, `FilterBankCVEP`)

- **Paradigm & Dataset Support**: MOABB v1.0+ implements `BaseCVEP`, `CVEP`, `FilterBankCVEP`, `FakeCVEPDataset`, and `MartinezCagigal2023Checker` / `MartinezCagigal2023Pary` (`moabb/paradigms/cvep.py`, `moabb/datasets/summary_cvep.csv`) formulated as epoch-level bit/intensity decoding (`0.0` vs `1.0` flash events).
- **Pipeline Status**: Unlike MI, P300, and SSVEP, **no dedicated `*-CVEP.yml` benchmark configuration files are shipped in `moabb/pipelines/configs/`** and no published `results_CVEP.csv` exists yet in `results/`. Epoch-level c-VEP bit decoding in MOABB tutorials reuses ERP/Riemannian classifiers (`XdawnCovariances`, `ERPCovariances`, `TSLR`, `LDA`) or external reconvolution CCA (`pyntbci`).

---

### 1.2 Braindecode Model Zoo & OpenEEGBench (`braindecode.org` & `braindecode/OpenEEGBench`)

#### 1.2.1 Braindecode v1.x Model Zoo Categorisation

Braindecode (`braindecode/models/summary.csv` and `docs/models/models_categorization.rst`) assigns non-mutually-exclusive architectural tags from **9 official categories**:
1. `Convolution`
2. `Filterbank`
3. `Interpretability`
4. `Recurrent` *(explicitly includes dilated Temporal Convolutional Networks as well as RNN/LSTM hybrids)*
5. `Attention/Transformer`
6. `Symmetric Positive-Definite` (`SPD` — delegated externally to the companion [`spd_learn`](https://github.com/spdlearn/spd_learn) library: `SPDNet`, `TensorCSPNet`, `TSMNet`, `EEGSPDNet`, `PhaseSPDNet`, `Green`)
7. `Graph Neural Network`
8. `Channel` *(montage-, hemisphere-, or 3D-coordinate-conditioned spatial layers)*
9. `Foundation Model` *(large self-supervised pretrained encoders and neural tokenizers)*

Across `braindecode/models/__init__.py` and `summary.csv`, there are **84 neural model/tokenizer classes** (**69 EEG-capable** and **15 non-EEG iEEG/MEG/sEMG-only**). Below are all **69 EEG-capable classes** grouped by their primary architectural/application category (with all official Braindecode multi-tags noted), followed by a reconciliation list of the 15 non-EEG classes.

##### A. Convolutional Networks (`Convolution` — general & MI-focused)
- **`ShallowFBCSPNet`** *(alias: `ShallowConvNet`; Schirrmeister et al., 2017)* — Tags: `Convolution`. Temporal conv + spatial conv + squaring + log-mean pooling mimicking FBCSP.
- **`Deep4Net`** *(alias: `DeepConvNet`; Schirrmeister et al., 2017)* — Tags: `Convolution`. Four conv-maxpool blocks after temporal-spatial split first block.
- **`EEGNet`** *(aliases: `EEGNetv4`, `EEGNet_8_2`; Lawhern et al., 2018)* — Tags: `Convolution`. Temporal conv + depthwise spatial conv + separable conv.
- **`EEGNeX`** *(Chen et al., 2024)* — Tags: `Convolution`. Pure ConvNeXt-inspired depthwise-separable dilated 1D CNN.
- **`EEGInceptionMI`** *(Zhang et al., 2021)* — Tags: `Convolution`. Multi-scale inception temporal kernels for motor imagery.
- **`EEGSimpleConv`** *(El Ouahidi et al., 2023)* — Tags: `Convolution`. Simple 1D residual CNN with optional resampling (`sfreq`).
- **`SCCNet`** *(Wei et al., 2019)* — Tags: `Convolution`. Spatial-component-wise CNN + log-power pooling.
- **`TIDNet`** *(Kostas & Rudzicz, 2020)* — Tags: `Convolution`. Thinker-Invariant DenseNet with dilated temporal convolutions for cross-subject MI.

##### B. Filter-Bank Networks (`Filterbank`)
- **`FBCNet`** *(Mane et al., 2021)* — Tags: `Convolution, FilterBank`. Multi-band Chebyshev filter bank + spatial depthwise conv + temporal variance layer (`VarLayer`). Requires `sfreq`.
- **`FBMSNet`** *(Liu et al., 2022)* — Tags: `Convolution, FilterBank`. Filter-bank multi-scale temporal conv + temporal log-variance + centre loss. Requires `sfreq`.
- **`FBLightConvNet`** *(Ma et al., 2023)* — Tags: `Convolution, FilterBank`. Filter-bank lightweight depthwise separable conv + attention-weighted temporal variance. Requires `sfreq`.
- **`IFNet`** *(Wang et al., 2023)* — Tags: `Convolution, FilterBank`. Interactive Frequency CNN (low/high frequency band interaction). Requires `sfreq`.

##### C. Interpretability-by-Design (`Interpretability`)
- **`SincShallowNet`** *(Borra et al., 2020)* — Tags: `Convolution, Interpretability`. Parametric band-pass `SincConv` first layer learning explicit cut-off frequencies (`sfreq`).
- **`EEGMiner`** *(Ludwig et al., 2024)* — Tags: `Convolution, Interpretability`. Learnable generalised Gaussian frequency filters estimating band power & magnituded connectivity (`sfreq`).
- **`SyncNet`** *(Li et al., 2017)* — Tags: `Interpretability`. Morlet-like parameterised oscillatory wavelet filters capturing cross-channel phase synchrony.

##### D. Attention & Transformer Supervised Networks (`Attention/Transformer`)
- **`EEGConformer`** *(Song et al., 2022)* — Tags: `Convolution, Attention/Transformer`. ShallowFBCSP-style conv patch stem + multi-head self-attention encoder.
- **`CTNet`** *(Zhao et al., 2024)* — Tags: `Convolution, Attention/Transformer`. EEGNet convolutional stem + Transformer encoder for MI.
- **`ATCNet`** *(Altaheri et al., 2022)* — Tags: `Convolution, Recurrent, Attention/Transformer`. Conv stem + sliding-window multi-head self-attention + dilated TCN.
- **`MSVTNet`** *(Liu et al., 2024)* — Tags: `Convolution, Recurrent, Attention/Transformer`. Multi-Scale Vision Transformer with multi-branch spatio-temporal convs.
- **`MSCFormer`** *(Zhao et al., 2025)* — Tags: `Convolution, Attention/Transformer`. Multi-scale convolutional branch + Transformer encoder.
- **`TMSANet`** *(Zhao et al., 2025)* — Tags: `Convolution, Attention/Transformer`. Temporal Multi-Scale Attention Network.
- **`AttentionBaseNet`** *(Wimpff et al., 2023)* — Tags: `Convolution, Attention/Transformer`. Compact CNN + squeeze-and-excitation / channel-temporal attention blocks.
- **`SSTDPN`** *(Cantero-Atienza et al. / Li et al., 2023)* — Tags: `Convolution, Attention/Transformer`. Spatial-Spectral-Temporal Dual-Prototype Network.
- **`TCFormer`** *(Altaheri et al., 2025)* — Tags: `Convolution, Attention/Transformer`. Temporal Convolutional Transformer combining grouped multi-kernel convs, RoPE attention, and TCN head.

##### E. Recurrent, Dilated TCN & Hybrid Networks (`Recurrent`)
- **`BDTCN` & `TCN`** *(Bai et al., 2018; Gemein et al., 2020)* — Tags: `Convolution, Recurrent`. Dilated causal Temporal Convolutional Network (`BDTCN` adds global time pooling for trial classification; originally benchmarked on TUAB pathology).
- **`EEGTCNet`** *(Ingolfsson et al., 2020)* — Tags: `Convolution, Recurrent`. EEGNet front-end + dilated TCN residual blocks.
- **`EEGITNet`** *(Salami et al., 2022)* — Tags: `Convolution, Recurrent`. Multi-scale Inception temporal stem + depthwise spatial conv + dilated TCN.
- **`HybridNet`** *(Schirrmeister et al., 2017)* — Tags: `Convolution` (hybrid branch). Concatenates `Deep4Net` and `ShallowFBCSPNet` feature maps before linear readout (in `__init__.py`, omitted from `summary.csv`).

##### F. Graph Neural Networks & Channel-Domain Supervised Networks (`Graph Neural Network`, `Channel`)
- **`DGCNN`** *(Song et al., 2018)* — Tags: `Graph Neural Network, Channel`. Dynamical Graph Convolutional Neural Network learning a Chebyshev spectral adjacency matrix across `chs_info` electrodes (originally emotion recognition).
- **`GCNsNet`** *(Lun et al., 2020)* — Tags: `Graph Neural Network, Channel`. Pearson-correlation electrode graph + multi-scale Chebyshev GCN for MI.
- **`EEGSym`** *(Pérez-Velasco et al., 2022)* — Tags: `Convolution, Channel`. Hemispheric-symmetric 3D inception/residual CNN exploiting left/right/midline 10-20 electrode pairings (`chs_info`, `sfreq`).

##### G. Task-Specific Sleep, Pathology/Epilepsy, ERP, Emotion, Visual & Speech Supervised Networks
- *Sleep Staging*:
  - **`SleepStagerChambon2018`** *(Chambon et al., 2018)* — Tags: `Convolution`. Spatial linear projection + per-channel 2D temporal CNN for 30 s PSG epochs.
  - **`SleepStagerBlanco2020`** *(Blanco et al., 2020)* — Tags: `Convolution`. Depthwise separable multi-group CNN for single/few-channel sleep staging.
  - **`AttnSleep`** *(Eldele et al., 2021)* — Tags: `Convolution, Attention/Transformer`. Multi-resolution CNN + adaptive feature recalibration + causal multi-head self-attention.
  - **`DeepSleepNet`** *(Supratak et al., 2017)* — Tags: `Convolution, Recurrent`. Dual-branch small/large filter CNN + bidirectional LSTM.
  - **`USleep`** *(Perslev et al., 2021)* — Tags: `Convolution`. Deep 12-stage 1D U-Net encoder-decoder for high-frequency/multi-epoch sleep staging (`sfreq`).
  - **`ContraWR`** *(Yang et al., 2023)* — Tags: `Convolution`. STFT spectrogram + 2D ResNet trained with contrastive world representation or supervised loss (`sfreq`).
- *Epilepsy / Pathology / Dense Event Detection*:
  - **`SPARCNet`** *(Jing et al., 2023)* — Tags: `Convolution`. 1D DenseNet designed for IIIC seizure/ictal-interictal continuum classification.
  - **`SeizureTransformer`** *(Wu et al., 2025)* — Tags: `Convolution, Attention/Transformer`. ResCNN + U-Net + Transformer producing **sample-level event-detection probabilities** (`Type: Event Detection`, 60 s @ 256 Hz).
  - **`DANCE`** *(2025/2026)* — Tags: `Convolution, Attention/Transformer, Channel`. Montage-conditioned multi-scale event detector (`Type: Event Detection`, requires `chs_info` & `sfreq`).
- *ERP, Emotion, Visual & Speech Decoding*:
  - **`EEGInceptionERP`** *(Santamaría-Vázquez et al., 2020)* — Tags: `Convolution`. Inception temporal-spatial CNN tailored to ERP/P300.
  - **`TSception`** *(Ding et al., 2022)* — Tags: `Convolution`. Multi-scale temporal + hemispheric-asymmetric spatial kernels for emotion/asymmetry (`sfreq`).
  - **`BrainModule`** *(Défossez et al., 2023)* — Tags: `Convolution` (`EEG, MEG`). Spatial attention + dilated ConvNet with GLU blocks for speech/audio decoding (`sfreq`, `chs_info` optional).
  - **`NICE`** *(Song et al., 2024)* — Tags: `Convolution` (`EEG, MEG`). Natural Image Contrastive EEG spatial-temporal projector for visual decoding.

##### H. Symmetric Positive-Definite (`SPD` / `spd_learn`)
Braindecode's categorisation page defines `SPD` as one of its 9 core model families (`BiMap`, `ReEig`, `LogEig` manifold layers; Huang & Van Gool, 2017) and delegates PyTorch implementations to [`spd_learn`](https://github.com/spdlearn/spd_learn) (Aristimunha et al., 2026) rather than duplicating classes inside `braindecode.models`.

##### I. EEG Foundation Models & Neural Tokenizers (`Foundation Model` — 30 EEG-capable classes across 24 families)
- **`BENDR`** *(Kostas et al., 2021)* — wav2vec 2.0-style conv feature extractor + Transformer context network (`Foundation Model, Convolution`).
- **`BIOT`** *(Yang et al., 2023)* — Per-channel STFT spectral patch + linear Transformer (`Foundation Model`).
- **`Labram`** *(Jiang et al., 2024)* — Neural tokenizer VQ-SNP + masked EEG patch Transformer (`Convolution, Foundation Model`).
- **`CBraMod`** *(Wang et al., 2025)* — Criss-cross spatial-temporal Transformer with asymmetric conditional positional encoding (`Foundation Model`).
- **`EEGPT`** *(Wang et al., 2024)* — Dual-self-supervised masked spatio-temporal alignment + reconstruction Transformer (`Foundation Model, Attention/Transformer`).
- **`REVE`** *(El Ouahidi et al., 2025)* — 4D Fourier positional encoding (`(x, y, z, t)`) + MAE Transformer (`Foundation Model, Attention/Transformer`).
- **`LUNA`** *(Döner et al., 2025)* — Learned cross-attention channel queries + 3D Fourier coordinate embeddings + RoPE Transformer (`Convolution, Channel, Foundation Model`).
- **`SignalJEPA`**, **`SignalJEPA_Contextual`**, **`SignalJEPA_PreLocal`**, **`SignalJEPA_PostLocal`** *(Guetschel et al., 2024)* — Joint-Embedding Predictive Architecture over 3D channel coordinates + downstream spatial-filtering variants (`Convolution, Channel, Foundation Model`).
- **`BrainOmni`** & **`BrainTokenizer`** *(Xiao et al., 2025)* — Sensor-geometry SEANet RVQ tokenizer + criss-cross EEG/MEG foundation model (`EEG, MEG`).
- **`CodeBrain`** *(Ma et al., 2025)* — Dual decoupled temporal/frequency tokenizers + structured state-space/sliding-window attention (`Foundation Model, Attention/Transformer`).
- **`CSBrain`** *(Zhou et al., 2025)* — Cross-scale spatio-temporal tokenization + anatomically structured sparse attention (`Foundation Model, Attention/Transformer`).
- **`STEEGFormer`** *(2025)* — Spatio-temporal MAE Transformer (`Small`/`Base`/`Large`; `Attention/Transformer, Foundation Model`).
- **`NeuroRVQ`** & **`NeuroRVQTokenizer`** *(2025/2026)* — Multi-scale residual vector-quantised EEG tokenizer + Transformer (`Convolution, Attention/Transformer, Foundation Model, Channel`).
- **`SleepFM`** & **`SleepFMStager`** *(Thapa et al., 2024/2026)* — Multimodal PSG/EEG sleep & disease-prediction foundation model (`Convolution, [Recurrent], Attention/Transformer, Foundation Model`).
- **`TFMTokenizer`** *(Pradeepkumar et al., 2026)* — Time-frequency discrete neural tokenizer (`Foundation Model, Attention/Transformer`).
- **`PBT`** *(Patched Brain Transformer; Klein et al., 2025)* — Montage-adaptive patched Transformer (`Foundation Model`).
- **`MEDFormer`** *(Wang et al., 2024)* — Multi-granularity cross-channel patching Transformer for medical EEG (`Foundation Model, Convolution`).
- **`MIRepNet`** *(2025)* — Motor-imagery representation pretraining network (`Convolution, Attention/Transformer, Foundation Model`).
- **`MVPFormer`** *(2025)* — Multi-view pretrained EEG Transformer (`Foundation Model, Attention/Transformer`).
- **`EEGDINO`** *(2025)* — Self-distillation (DINO-style) EEG foundation model (`Foundation Model, Attention/Transformer`).
- **`EEGCLIP`** *(2025)* — Contrastive EEG-clinical-text alignment encoder (`Foundation Model, Convolution`).
- **`AXON`** *(2026)* — Channel-coordinate-conditioned 118M-parameter foundation model (`Foundation Model, Channel, Attention/Transformer`).
- **`ZUNA`** *(2026)* — 172M-parameter 3D-coordinate-conditioned EEG foundation model (`Foundation Model, Channel, Attention/Transformer`).
- **`EpiNT`** *(2025/2026)* — Scalp EEG + iEEG epilepsy foundation Transformer (`EEG, iEEG`).
- **`Guetschel2026`** *(Guetschel et al., 2026)* — Montage-aware self-supervised EEG foundation architecture (`Foundation Model, Attention/Transformer, Channel`).

*(Reconciliation of the remaining **15 non-EEG classes** in `braindecode.models`: **7 iEEG-only** FMs — `BaRISTA`, `BrainBERT`, `Brant`, `CORTEG`, `DIVER1`, `DuIN`, `MAPA`, `PopulationTransformer` [8 iEEG total]; **3 MEG-only** FMs — `BBL`, `MEGGPT`, `MEGXL`; and **5 sEMG** sequence/CTC models — `EMG2QwertyNet`, `MetaNeuromotorHand`, `NeuroPose`, `SensingDynamics`, `VEMG2Pose`; note `HybridNet` and `TCN` are in `__init__.py` without separate `summary.csv` rows, bringing `__init__.py` model classes to 84.)*

#### 1.2.2 OpenEEGBench (`braindecode/OpenEEGBench` & Live HF Leaderboard)

OpenEEGBench is Braindecode's standardised foundation-model evaluation suite across **10 downstream EEG datasets** (`PhysioNet-MI`, `BCIC-IV-2a`, `BCIC2020-Track3`, `TUEV`, `TUAB`, `ISRUC-Sleep`, `FACED`, `MDD Mumtaz2016`, `Arithmetic Zyma2019`, `SEED-V`).

- **Registered Backbones in Code (`open_eeg_bench/default_configs/backbones.py` — 7 models)**:
  1. `biot` (`BIOT`, `braindecode/biot-pretrained-six-datasets-18chs`)
  2. `labram` (`InterpolatedLaBraM`, `braindecode/labram-pretrained`)
  3. `bendr` (`InterpolatedBENDR`, `braindecode/braindecode-bendr`)
  4. `cbramod` (`CBraMod`, `braindecode/cbramod-pretrained`)
  5. `signal_jepa` (`InterpolatedSignalJEPA`, `braindecode/signal-jepa_without-chans`)
  6. `reve` (`REVE`, `brain-bzh/reve-base`)
  7. `eegpt` (`InterpolatedEEGPT`, `braindecode/eegpt-pretrained`)
  *(Note: Models with fixed pretraining channel sets are wrapped in spatial `Interpolated*` MNE/spline channel-projection adapters.)*
- **Supported Adaptation Strategies (`experiments.py` — 9 modes × 3 heads)**:
  - Strategies: `frozen` (linear/MLP SGD probe), `ridge_probe` (closed-form Ridge), `lora`, `ia3`, `adalora`, `dora`, `oft` (PEFT adapters), `full_finetune`, `two_stages` (linear probe warmup → full fine-tune).
  - Readout heads: `linear_head`, `mlp_head`, `original_head`.
- **Actively Benchmarked on Live Leaderboard (`https://braindecode-openeegbench.hf.space/api/leaderboard`)**:
  - Exactly **5 foundation models** × **2 adaptation modes** (`probe` and `full_finetune`) = **10 live entries**: **`BIOT`**, **`LaBraM`**, **`EEGPT`**, **`CBraMod`**, and **`REVE`** (`BENDR` and `SignalJEPA` have backbone configs in the repo but do not yet have populated leaderboard rows).
  - **No classical pipelines or from-scratch supervised deep learners** are benchmarked in OpenEEGBench.

---

### 1.3 EEG-Arena / EEG.FM (`eeg.fm` & `OrangeP0P/eeg-arena`)

EEG-Arena (*Benchmarking EEG Foundation Models at Scale: Lessons from 20,000 Evaluations*; Chen et al., 2026, `arXiv:2609.32743`) evaluates **55 model configurations** across **29 datasets / 74 tasks** under within-subject (`ws`) and cross-subject (`cs`) splits. Both `OrangeP0P/eeg-arena/configs/protocol_i/` and the live JSON snapshot `https://eeg.fm/benchmarks-data/overall-performance.json` divide models into two primary categories (`modelTypeBadge` on `eeg.fm`): **`Foundation model`** (`type=1`, **30** variants across **20** model families) and **`Task-specific baseline`** / **`Conventional supervised baselines`** (`type=0`, **25** models), further annotated in the repository by input format (`raw` vs `patched`) and spatial metadata conditioning.

#### 1.3.1 EEG Foundation Models (`Foundation model`, 30 configurations / 20 families)

| Live `eeg.fm` Display Name | Registry / Config Key | Canonical Method & Citation | Input Format & Spatial Conditioning (`ch_names` / `ch_positions` / `ch_idx`) | Live Task Coverage (`overall-performance.json`) |
| :--- | :--- | :--- | :--- | :--- |
| `BENDR` | `bendr` | BENDR (Kostas et al., 2021) | `raw` · `ch_names` (19/20-ch 10-20) | 80.8% |
| `BIOT · Prest 16ch` | `biot__prest-16ch` | BIOT (Yang et al., 2023) — PREST 16-ch | `raw` · `ch_names` (16 bipolar/montage chs) | 7.7% *(bipolar subset)* |
| `BIOT · SHHS Prest 18ch` | `biot__shhs-prest-18ch` | BIOT (Yang et al., 2023) — SHHS+PREST 18-ch | `raw` · `ch_names` (18 chs) | 15.4% *(bipolar subset)* |
| `BIOT · Six Datasets 18ch` | `biot__six-datasets-18ch` | BIOT (Yang et al., 2023) — 6-dataset 18-ch | `raw` · `ch_names` (18 chs) | 15.4% *(bipolar subset)* |
| `CBraMod` | `cbramod_ft` (`cbramod`) | CBraMod (Wang et al., 2025) | `patched` · channel-agnostic (no names/coords) | 100% |
| `CodeBrain` | `codebrain` | CodeBrain (Ma et al., 2025) | `patched` · channel-agnostic | 100% |
| `CSBrain` | `csbrain` | CSBrain (Zhou et al., 2025) | `patched` · `ch_names` (region/scale ordering) | 100% |
| `EEGMamba` | `eegmamba` | EEGMamba (Wang et al., 2025) | `patched` · channel-agnostic | 100% |
| `EEGPT` | `eegpt` | EEGPT (Wang et al., 2024) | `patched` · `ch_names` (58-ch 10-20 lookup) | 80.8% |
| `HEAR · Base` | `hear__base` | HEAR Base (2025/2026) | `patched` · `ch_names` + 3D `ch_positions` | 100% |
| `HEAR · Large` | `hear__large` | HEAR Large (2025/2026) | `patched` · `ch_names` + 3D `ch_positions` | 100% |
| `LaBraM` | `labram` (`base`) | LaBraM-Base (Jiang et al., 2024) | `patched` · `ch_names` + `model_channel_indices` | 80.8% |
| `LEAD` | `lead` (`base`) | LEAD-Base (Wang et al., 2025; AD/clinical SSL) | `raw` · `ch_names` | 80.8% |
| `LUNA · Base` | `luna__base` | LUNA-Base (Döner et al., 2025) | `raw` · `ch_names` + 3D `ch_positions` | 100% |
| `LUNA · Large` | `luna__large` | LUNA-Large (Döner et al., 2025) | `raw` · `ch_names` + 3D `ch_positions` | 100% |
| `LUNA · Huge` | `luna__huge` | LUNA-Huge (Döner et al., 2025) | `raw` · `ch_names` + 3D `ch_positions` | 100% |
| `mdJPT` | `mdjpt` | mdJPT (Multi-dataset Joint Pretrained Transformer, 2025) | `patched` · `ch_names` | 80.8% |
| `NeuroGPT` | `neurogpt` | Neuro-GPT (Cui et al., 2024) | `patched` · `ch_names` (22-ch 10-20 projection) | 80.8% |
| `NeuroRVQ` | `neurorvq` | NeuroRVQ (2025/2026) | `patched` · `ch_names` + `model_channel_indices` | 87.5% |
| `REVE · Base` | `reve__base` | REVE-Base (El Ouahidi et al., 2025) | `raw` · 3D `ch_positions` | 96.2% |
| `REVE · Large` | `reve__large` | REVE-Large (El Ouahidi et al., 2025) | `raw` · 3D `ch_positions` | 96.2% |
| `SleepFM · Upstream` | `sleepfmclinical_base_upstream` | SleepFM Base Upstream (Thapa et al., 2024/2026) | `raw` · channel-agnostic pooling | 100% |
| `SleepFM · Sleep Staging` | `sleepfmclinical_sleep_staging` | SleepFM Sleep-Staging Checkpoint | `raw` · channel-agnostic pooling | 100% |
| `SleepFM · Diagnosis` | `sleepfmclinical_diagnosis` | SleepFM Disease-Diagnosis Checkpoint | `raw` · channel-agnostic pooling | 100% |
| `SleepGPT · Large` | `sleepgpt_large_pretrained` | SleepGPT-Large (2025) | `raw` · `ch_names` | 100% |
| `ST-EEGFormer · Small` | `steegformer__small` | ST-EEGFormer-Small (2025) | `raw` · `ch_names` + `model_channel_indices` | 80.8% |
| `ST-EEGFormer · Base` | `steegformer__base` | ST-EEGFormer-Base (2025) | `raw` · `ch_names` + `model_channel_indices` | 80.8% |
| `ST-EEGFormer · Large` | `steegformer__large` | ST-EEGFormer-Large (2025) | `raw` · `ch_names` + `model_channel_indices` | 74.0% |
| `TFM · CHB-MIT` | `tfmtokenizer_single_chbmit` | TFM-Tokenizer (Pradeepkumar et al., 2026) | `raw` · channel-agnostic | 96.2% |
| `Uni-DMFM · Base` | `unidmfm_base` | Uni-DMFM Base (Unified Diffusion/Masked FM, 2025/2026) | `patched` · channel-agnostic | 100% |

*(Note: Sub-100% coverage on models such as `BENDR`, `EEGPT`, `LaBraM`, `NeuroGPT`, `LEAD`, `mdJPT`, and `BIOT` reflects strict montage/bipolar compatibility rules (`Non-Bipolar` vs `Bipolar` tabs on `eeg.fm`); the website also tracks per-dataset pretraining overlap flags in client bundle `264-6b39b4e5c290cc46.js`.)*

#### 1.3.2 Task-Specific / Conventional Supervised Baselines (`Task-specific baseline`, 25 models)

All 25 baselines take `raw` `(B, C, T)` input without requiring `ch_names` (only `BiDANN` and `HSLT` optionally accept `ch_positions` to partition left/right/regional electrodes, falling back to deterministic index splits otherwise):

1. **`EEGNet`** (`eegnet`) — Lawhern et al. (2018)
2. **`ShallowConvNet`** (`shallowconvnet`) — `ShallowFBCSPNet` (Schirrmeister et al., 2017)
3. **`DeepConvNet`** (`deepconvnet`) — `Deep4Net` (Schirrmeister et al., 2017)
4. **`EEGNeX`** (`eegnex`) — Chen et al. (2024)
5. **`EEGWaveNet`** (`eegwavenet`) — Multi-scale depthwise WaveNet-style CNN for seizure/BCI (Thuwajit et al., 2022)
6. **`FBCNet`** (`fbcnet`) — Filter-Bank Convolutional Network (Mane et al., 2021)
7. **`IFNet`** (`ifnet`) — Interactive Frequency CNN (Wang et al., 2023)
8. **`ADFCNN`** (`adfcnn`) — Attention-based Dual-scale Fusion Filter-Bank CNN (Tao et al., 2023)
9. **`EEGConformer`** (`eegconformer`) — Song et al. (2022)
10. **`DBConformer`** (`dbconformer`) — Dual-Branch (parallel temporal & spatial Transformer) Conformer (Wang et al., 2023/2024)
11. **`ATCNet`** (`atcnet`) — Altaheri et al. (2022)
12. **`CTNet`** (`ctnet`) — Convolutional Transformer Network (Zhao et al., 2024)
13. **`MSVTNet`** (`msvtnet`) — Multi-Scale Vision Transformer (Liu et al., 2024)
14. **`MSCFormer`** (`mscformer`) — Multi-Scale Convolutional Transformer (Zhao et al., 2025)
15. **`TMSA-Net`** (`tmsanet`) — Temporal Multi-Scale Attention Network (Zhao et al., 2025)
16. **`EEGInceptionERP`** (`eeginception_erp`) — Santamaría-Vázquez et al. (2020)
17. **`TSception`** (`tsception`) — Asymmetric hemispheric-temporal CNN (Ding et al., 2022)
18. **`BiDANN`** (`bidann`) — Bi-Hemisphere Domain/Regional LSTM Attention Network for emotion EEG (Li et al., 2018; backbone in `baseline_zoo.py`)
19. **`HSLT`** (`hslt`) — Hierarchical Spatial-Local-Global Transformer over scalp regions (Wang et al., 2022)
20. **`SlimSeiz`** (`slimseiz`) — Lightweight 1D CNN + BiGRU/attention seizure detector (ca. 2023/2024; `SlimSeizBackbone` in `baseline_zoo.py`)
21. **`DeepSleepNet`** (`deepsleepnet`) — Dual-scale CNN + BiLSTM sleep stager (Supratak et al., 2017)
22. **`SleepEEGNet`** (`sleepeegnet`) — DeepSleepNet-style CNN + BiRNN seq-to-seq attention stager (Mousavi et al., 2019)
23. **`SleepTransformer`** (`sleeptransformer`) — Two-level intra-epoch / inter-frame Transformer sleep stager (Phan et al., 2022)
24. **`U-Sleep`** (`usleep`) — 1D U-Net sleep stager (Perslev et al., 2021)
25. **`YASA` / `YASA-style baseline`** (`yasa`) — **Source-verified note**: Rather than calling Vallat & Walker's (2021) LightGBM package directly, `models/_shared/baseline_zoo.py` implements `YASABackbone` as an end-to-end PyTorch module extracting 6 per-channel time-domain summary statistics (`std`, `rms`, `line_length`, `zero_cross`, `peak`, `kurtosis`) + 6 relative spectral band-powers (`0.5–4`, `4–8`, `8–12`, `12–16`, `16–30`, `30–45` Hz), summarising across channels via `(mean, std)` (24 features) into a 2-layer GELU MLP + `LinearClassifierHead`. **No Riemannian or CSP baselines are included in EEG-Arena.**

---

### 1.4 NeuralBench (`facebookresearch/neuroai`, `arXiv:2605.08495`)

NeuralBench (Banville et al., 2026) benchmarks neural decoding across 30+ EEG/MEG/fMRI/EMG/ECG tasks. For **EEG** (standardised by default to 120 Hz via `defaults/eeg/config.yaml` unless overridden by an FM checkpoint), `neuralbench/registry.py` and `neuralbench/plots/_models.py` group models into three official CLI tiers (`all_baseline`, `all_classic`, `all_fm`):

#### 1.4.1 Classical / Non-Deep Baselines (`BASELINE_MODELS` / `all_baseline`)
- **Constant / Sanity Predictors**:
  - **`chance`** (`chance.yaml`) — Uniform random / analytical chance baseline.
  - **`dummy`** (`dummy.yaml`, `DummyPredictor`) — Majority-class / empirical training-mean predictor.
- **Task-Dispatched Handcrafted Pipelines (`SKLEARN_BASELINE_MODELS` in `baselines.py`)** *(collapsed into a single `"Handcrafted"` bar per task via `FEATURE_BASED_BY_TASK`)*:
  - **`CovTsLR`** (`cov_ts_lr.yaml`) — `Covariances('oas')` → `Shrinkage(0.1)` → `TangentSpace('riemann')` → `StandardScaler` → `LogisticRegressionCV`. Dispatched for oscillatory BCI (`motor_imagery`, `motor_execution`, `motor_preparation`, `cvep`, `mental_imagery`, `mental_arithmetic`, `mental_workload`, `emotion`) and clinical/state tasks (`pathology`, `seizure`, `clinical_event`, `artifact` [via `OneVsRestClassifier`], `sleep_stage`, `sleep_arousal`, `sex`, `asd`/`dementia`/`depression`/`parkinsons`/`schizophrenia` diagnosis).
  - **`XdawnTsLR`** (`xdawn_ts_lr.yaml`) — `XdawnCovariances(nfilter=4)` → `TangentSpace` → `StandardScaler` → `LogisticRegressionCV`. Dispatched for all 12 event-locked ERP tasks (`p3`, `ern`, `lrp`, `n170`, `n2pc`, `n400`, `mismatch_negativity`, `acoustic_change`, etc.).
  - **`CoSpectraLogLR`** (`cospectra_log_lr.yaml`) — Welch real cross-spectral matrices (`pyriemann.estimation.CoSpectra`, `window=128`, `overlap=0.75`, `2–40 Hz`) → upper-triangular flattening with `log1p` on diagonal PSDs (`_UpperTriLog1p`) → `StandardScaler` → `LogisticRegressionCV`. Dispatched for `ssvep`.
  - **`CovTsRidge`** (`cov_ts_ridge.yaml`) — `Covariances('oas')` → `TangentSpace` → `StandardScaler` → `RidgeCV`. Dispatched for regression (`age`, `reaction_time`, `psychopathology`) and multi-output retrieval (`image`, `speech`, `word`, `sentence`, `video`, `typing`).

#### 1.4.2 Task-Specific ("Classic") Supervised EEG Deep Learners (`CLASSIC_MODELS` / `all_classic` — 8 core models + 2 extra YAMLs)
1. **`ShallowFBCSPNet`** (`shallow_fbcsp_net.yaml`, Schirrmeister et al., 2017) — Braindecode class.
2. **`Deep4Net`** (`deep4net.yaml`, Schirrmeister et al., 2017) — Braindecode class.
3. **`EEGNet`** (`eegnet.yaml`, Lawhern et al., 2018) — Braindecode class.
4. **`BDTCN`** (`bdtcn.yaml`, Gemein et al., 2020) — Braindecode class.
5. **`EEGConformer`** (`eegconformer.yaml`, Song et al., 2022) — Braindecode class.
6. **`ATCNet`** (`atcnet.yaml`, Altaheri et al., 2022) — Braindecode class.
7. **`SimpleConvTimeAgg`** (`simpleconv_time_agg.yaml`, adapted from El Ouahidi et al., 2023 / Défossez et al., 2023) — `neuraltrain` architecture combining a **3D Fourier positional `ChannelMerger`** (`n_virtual_channels=270` from 3D electrode coordinates) + 4-block dilated ConvNet with GLU gating + linear time aggregation.
8. **`CTNet`** (`ctnet.yaml`, Zhao et al., 2024) — Braindecode class.
- *Additional YAML configs shipped in `neuralbench/models/` (outside the 8-model headline table)*: **`EEGNeX`** (`eegnex.yaml`), sequence-level **`SimpleConv`** (`simpleconv.yaml`), and unpretrained reference **`MaeEncoder`** (`mae.yaml`), plus non-EEG models (`EMG2QwertyNet`, `VEMG2Pose`, `NeuroPose`, `SensingDynamics`, `FmriLinear`, `FmriMlp`).

#### 1.4.3 EEG Foundation Models (`FM_MODELS` / `all_fm` — 6 core models)
Evaluated across downstream wrappers (`linear` probe, `mlp` probe, `lora`, `full_finetune`) with explicit pretraining-dataset overlap hatching (`PRETRAINING_OVERLAP`):
1. **`BENDR`** (`bendr.yaml`, `NtBendr`; Kostas et al., 2021) — Contrastive wav2vec 2.0-style on TUEG.
2. **`BIOT`** (`biot.yaml`; Yang et al., 2023) — `braindecode/biot-pretrained-six-datasets-18chs`.
3. **`LaBraM`** (`labram.yaml`, `NtLabram`, Base; Jiang et al., 2024) — `braindecode/labram-pretrained`.
4. **`CBraMod`** (`cbramod.yaml`; Wang et al., 2025) — `braindecode/cbramod-pretrained`.
5. **`LUNA`** (`luna.yaml`, `NtLunaLarge`, Large; Döner et al., 2025) — Contrastive + MAE on TUEG + Siena.
6. **`REVE`** (`reve.yaml`, `NtReve`, Base; El Ouahidi et al., 2025) — `brain-bzh/reve-base` (MAE on 92 datasets, ~60k hours).

---

### 1.5 AdaBrain-Bench (`Jamine-W/AdaBrain-Bench`, `arXiv:2505.17099`)

AdaBrain-Bench (Wang et al., 2025) evaluates multi-task adaptation across motor imagery, emotion, ERP, and cognitive workload datasets (`models/` and `run_finetuning.py`), grouping its **8 models** into two categories:

1. **Supervised Baselines (Trained from Scratch — 4 models)**:
   - **`EEGNet`** (`models/EEGNet.py`) — Lawhern et al. (2018).
   - **`LMDA` / `LDMA`** (`models/LMDA.py`; spelled `LDMA` in README table) — **LMDA-Net** (*Lightweight Multi-Dimensional Attention Network*; Miao et al., 2023, *NeuroImage*), combining channel-tensor projection, depth-attention over feature maps, and channel-attention with EEGNet-style separable convs.
   - **`ST-Tran`** (`models/EEGTransformer.py`) — **S&T-Transformer / Spatial-Temporal Tiny Transformer** (Song et al., 2021, *IEEE TNSRE*), applying spatial attention across channels followed by temporal convolution and multi-head temporal self-attention.
   - **`Conformer`** (`models/EEGConformer.py`) — **EEGConformer** (Song et al., 2022).
2. **EEG Foundation Models (Pretrained — 4 models)**:
   - **`BIOT`** (`models/BIOT.py`; Yang et al., 2023)
   - **`EEGPT`** (`models/EEGPT.py`; Wang et al., 2024)
   - **`LaBraM`** (`models/LaBraM.py`; Jiang et al., 2024)
   - **`CBraMod`** (`models/CBraMod.py`; Wang et al., 2025)

---

### 1.6 ETH-DISCO EEG-Bench (`ETH-DISCO/EEG-Bench`)

ETH-DISCO's `EEG-Bench` (`benchmark_console.py`, `eeg_bench/models/bci/`, `eeg_bench/models/clinical/`) organises baselines strictly by **task domain** (`BCI` vs `Clinical`), comparing classical feature-engineering pipelines directly against foundation models (**0 supervised-from-scratch deep networks**):

1. **BCI Paradigm Baselines (`bci_models_map` — 4 motor imagery tasks, within- & multi-subject)**:
   - *Classical*:
     - **`CSPLDA`** (`lda`, `csp_lda_model.py`) — Band-pass + `mne.decoding.CSP` + `LinearDiscriminantAnalysis`.
     - **`CSPSVM`** (`svm`, `csp_svm_model.py`) — Band-pass + `mne.decoding.CSP` + `SVC`.
   - *Foundation Models*:
     - **`LaBraMBci`** (`labram`) — LaBraM-Base (Jiang et al., 2024).
     - **`BENDRBci`** (`bendr`) — BENDR (Kostas et al., 2021).
     - **`NeuroGPTBci`** (`neurogpt`) — Neuro-GPT (Cui et al., 2024).
2. **Clinical Paradigm Baselines (`clinical_models_map` — 10 pathology, epilepsy, artefact, Parkinson's & sleep tasks)**:
   - *Classical*:
     - **`BrainfeaturesLDA`** (`lda`, `brainfeatures_lda_model.py`) — Multi-domain hand-crafted EEG summary features from Schirrmeister/Gemein's Freiburg `brainfeatures` pipeline (time-domain statistics, Welch spectral band powers, discrete wavelet coefficients, phase-locking/connectivity summaries aggregated across windows) + `LinearDiscriminantAnalysis`.
     - **`BrainfeaturesSVM`** (`svm`, `brainfeatures_svm_model.py`) — Same `brainfeatures` feature vector + `SVC`.
   - *Foundation Models*:
     - **`LaBraMClinical`** (`labram`) — LaBraM-Base.
     - **`BENDRClinical`** (`bendr`) — BENDR.
     - **`NeuroGPTClinical`** (`neurogpt`) — Neuro-GPT.

---

### 1.7 OmniEEG-Bench (`ncclab-sustech/omni-eegbench`) & EEGDash (`eegdash/EEGDash`)

#### 1.7.1 OmniEEG-Bench (Lu et al., 2026)

OmniEEG-Bench (`models/factory.py`, `configs/linear_downsample_cross.yaml`, `configs/finetune_cross.yaml`, `configs/basemodel_downsample.yaml`) evaluates models across up to 60 Zarr/HDF5 datasets spanning **6 cognitive/clinical task categories** (Type-I through Type-VI) under `linear_probing`, `full_finetune`, and `zero_shot` protocols, using a unified `DownstreamModel(feature_extractor, ProbeHead)` interface:

- **EEG Foundation Models (10 active cross-benchmark models + 1 iEEG adapter)**:
  1. **`BrainOmni`** (`brainomni`; Xiao et al., 2025) — Geometry-aware SEANet RVQ tokenizer + criss-cross EEG/MEG foundation model (256 Hz).
  2. **`LaBraM`** (`labram`; Jiang et al., 2024) — `labram-base.pth` (200 Hz).
  3. **`BIOT`** (`biot`; Yang et al., 2023) — `EEG-six-datasets-18-channels.ckpt` with `zero_fill_adapter` (200 Hz).
  4. **`FEMBA`** (`femba`; Tegon et al., 2025) — **Foundational EEG Mamba** (`femba_weights.safetensors`), bidirectional Mamba state-space autoencoder for lightweight EEG representation learning (256 Hz).
  5. **`NeuroLM`** (`neurolm`; Jiang et al., 2024/2025, ICLR 2025) — Multi-task LLM-aligned EEG foundation model (`NeuroLM-VQ` + `NeuroLM-B` GPT-2 backbone enabling open-ended/zero-shot instruction decoding as well as linear/FT probing, 200 Hz).
  6. **`CBraMod`** (`cbramod`; Wang et al., 2025) — `pretrained_weights.pth` (200 Hz).
  7. **`NeuroGPT`** (`neurogpt`; Cui et al., 2024) — EEGConformer encoder + GPT-2 causal decoder (`encoder_adapter`, 250 Hz).
  8. **`REVE`** (`reve`; El Ouahidi et al., 2025) — `reve-base` with 3D `reve-positions` lookup (200 Hz).
  9. **`EEGMamba`** (`eegmamba`; Wang et al., 2025) — Bidirectional Mamba SSM foundation model (`19ch_adapter`, 200 Hz).
  10. **`BENDR`** (`bendr`; Kostas et al., 2021) — Wrapped with a `learned_channel_adapter` to project arbitrary channel counts into BENDR's 19/20-channel input space (256 Hz).
  - *(Also wired in `models/factory.py` as `brant`: **`Brant`** [Zhang et al., 2023, NeurIPS], an intracranial iEEG/SEEG foundation model via `BrantPretrainFeatureExtractor`, excluded from the 10-model scalp-EEG YAML suites.)*
- **Supervised Deep Learning Baselines (`configs/basemodel_downsample.yaml` — 2 models)**:
  1. **`EEGNet`** (`eegnet`; Lawhern et al., 2018)
  2. **`EEGConformer`** (`eegconformer`; Song et al., 2022)

#### 1.7.2 EEGDash (`eegdash.org` & `eegdash/EEGDash`)

Inspection of `eegdash/EEGDash` confirms that **EEGDash is a data-access archive (>700 BIDS/NEMAR/OpenNeuro datasets) and hand-crafted feature-extraction library, not a comparative algorithm leaderboard**:
- **Feature Bank (`eegdash/features/feature_bank/`)**: Ships modular NumPy/SciPy extractors across five modules:
  1. `spectral.py` (Welch PSD, band powers, spectral entropy/edge/slope/centroid)
  2. `connectivity.py` (coherence, imaginary coherence, PLV)
  3. `complexity.py` (sample/approximate/permutation/SVD entropy, Hjorth mobility/complexity, Lempel-Ziv)
  4. `dimensionality.py` (Higuchi/Petrosian/Katz fractal dimensions, Hurst exponent, DFA)
  5. `csp.py` (`CommonSpatialPattern` trainable feature extractor)
- **Starter Baselines in Tutorials & NeurIPS 2025 EEG Foundation Challenge**: Tutorial scripts (`examples/`) demonstrate two reference pipelines — end-to-end **`EEGNeX`** (via `braindecode.models.EEGNeX`) and **`LogisticRegression`** over `eegdash.features` band-power/Hjorth features — rather than maintaining a multi-model benchmark matrix.

---

## Part 2 — Unified Cross-Benchmark Matrix

Benchmark abbreviations used in the **Benchmarks** column:
- **`MOABB`** = MOABB (`pipelines/configs/` + published CSVs)
- **`BD`** = Braindecode Model Zoo *(library reference; not counted as an empirical benchmark leaderboard in `Ext. Bench Count`)*
- **`OEB`** = OpenEEGBench *(marked `OEB` for live leaderboard, `OEB(cfg)` for repo-configured only)*
- **`Arena`** = EEG-Arena / EEG.FM (`55` live configurations)
- **`NB`** = NeuralBench *(marked `NB` for core paper models/baselines, `NB(yaml)` for extra YAML configs)*
- **`Ada`** = AdaBrain-Bench
- **`ETH`** = ETH-DISCO EEG-Bench
- **`Omni`** = OmniEEG-Bench
- *(`EEGDash` starter tutorial models `EEGNeX` and `CSP` are noted where relevant.)*

---

### Family 1: Classical EEG Pipelines

| Sub-family | Canonical Algorithm & Aliases | Benchmarks (`Ext. Count`) | Hard Input Requirements (`sfreq`, `ch_names`/3D, `freqs`, min length) | Current `aeon-neuro` Status |
| :--- | :--- | :--- | :--- | :--- |
| **1A. Spatial Filtering / CSP** | **CSP + LDA** (`CSP+LDA`, `CSPLDA`, `CSP_LDA`) | `MOABB`, `ETH` **(2)** *(+ `EEGDash` CSP feature)* | $C \ge 2$; `sfreq` only if internal band-pass used (MOABB uses 8–32 Hz); $T > C$ for full-rank SCM | **`Standalone`** (`CSPClassifier`, default `LDA`) + **`MOABBPipelineClassifier("CSP_LDA")`** |
| **1A. Spatial Filtering / CSP** | **CSP + SVM** (`CSP+SVM`, `CSPSVM`, `CSP_SVM`) | `MOABB`, `ETH` **(2)** | $C \ge 2$; `sfreq` only if band-passed; $T > C$ | **`Standalone`** (`CSPClassifier(estimator=SVC(...))`) + **`MOABBPipelineClassifier("CSP_SVM")`** |
| **1A. Spatial Filtering / CSP** | **Regularised / Diagonal-Loading CSP + Shrinkage LDA** (`DLCSPauto+shLDA`, `regCSP+shLDA`) | `MOABB` **(1)** | $C \ge 2$; OAS shrinkage handles $T \le C$; `sfreq` if band-passed | **`MOABBPipelineClassifier("DLCSPauto_shLDA")`** *(not exposed on standalone `CSPClassifier`)* |
| **1A. Spatial Filtering / CSP** | **Weighted Tikhonov-Regularised CSP + LDA** (`TRCSP+LDA`, `WTRCSP`) | `MOABB` **(1)** | **Binary (2-class) only**; $C \ge 2$; `sfreq` if band-passed | **`MOABBPipelineClassifier("TRCSP_LDA")`** |
| **1A. Spatial Filtering / CSP** | **Filter-Bank CSP + MI Selection + SVM** (`FilterBank+SVM`, `FBCSP`, `FBCSP_SVM`) | `MOABB` **(1)** | **Requires `sfreq` > 72 Hz** (MOABB default 6× 4 Hz bands across 8–32/36 Hz; filter padlen typically needs $T \ge 64$); $C \ge 2$ | **`MOABBPipelineClassifier("FBCSP_SVM")`** *(no standalone `FilterBankCSPClassifier` yet)* |
| **1B. xDAWN / ERP Covariance** | **xDAWN + Shrinkage LDA** (`xDAWN+LDA`, `XDAWN+LDA`, `xDAWN_LDA`) | `MOABB` **(1)** | $C \ge 2$; time-locked ERP epochs; `sfreq` only if band-passed (1–24 Hz in MOABB) | **`Standalone`** (`XDAWNClassifier`) + **`MOABBPipelineClassifier("xDAWN_LDA")`** |
| **1B. xDAWN / ERP Covariance** | **xDAWN Covariance + MDM** (`XdawnCov+MDM`, `XDAWNCov+MDM`) | `MOABB` **(1)** | $C \ge 2$; time-locked epochs; SPD augmented covariance of size $(2 K n_{\text{classes}}) \times (2 K n_{\text{classes}})$ | **`MOABBPipelineClassifier("XdawnCov_MDM")`** |
| **1B. xDAWN / ERP Covariance** | **xDAWN Covariance + Tangent Space + Linear Classifier** (`XdawnTsLR` [LR], `XdawnCov+TS+SVM` [SVM]) | `MOABB`, `NB` **(2)** | $C \ge 2$; time-locked ERP epochs; SPD regularisation (`lwf`/`oas`) required to avoid rank-deficient `logm` | **`MOABBPipelineClassifier("XdawnCov_TS_SVM")`** *(SVM variant; LR variant `XdawnTsLR` not yet wrapped)* |
| **1B. xDAWN / ERP Covariance** | **ERP Covariance + MDM** (`ERPCov+MDM`, `ERPCov(svd_n=4)+MDM`) | `MOABB` **(1)** | $C \ge 2$; concatenates class-prototype channels ($C(1 + n_{\text{classes}})$ SPD matrix) | **`MOABBPipelineClassifier("ERPCov_MDM")`** |
| **1C. Riemannian Distance & TS** | **Riemannian MDM** (`MDM`) | `MOABB` **(1)** | $C \ge 1$; SPD trial covariances ($T > C$ for `scm`, or shrinkage `oas`/`lwf`) | **`Standalone`** (`RiemannianMDMClassifier`) + **`MOABBPipelineClassifier("MDM")`** *(note: `aeon-neuro` also adds `RiemannianKNNClassifier`)* |
| **1C. Riemannian Distance & TS** | **Fisher Geodesic MDM** (`FgMDM`) | `MOABB` **(1)** | $C \ge 2$; SPD trial covariances | **`MOABBPipelineClassifier("FgMDM")`** |
| **1C. Riemannian Distance & TS** | **Riemannian Tangent Space + Logistic Regression** (`TSLR`, `TS+LR`, `CovTsLR`) | `MOABB`, `NB` **(2)** *(+ `CovTsRidge` for regression in `NB`)* | $C \ge 1$ ($C(C+1)/2$ features; high-density $C \ge 128$ yields >8k features, needing `oas` shrinkage + L2 regularisation) | **`MOABBPipelineClassifier("TSLR")`** / **`MOABBTSLRClassifier`** + **`NeuralBenchTSLRClassifier`** *(experimental; no non-experimental `TangentSpaceClassifier` yet)* |
| **1C. Riemannian Distance & TS** | **Riemannian Tangent Space + SVM / ElasticNet** (`TSSVM` / `TS+SVM`, `TSEN` / `TS+EL`) | `MOABB` **(1)** | Same as `TSLR` | **`MOABBPipelineClassifier("TSSVM" / "TSEN")`** |
| **1C. Riemannian Distance & TS** | **Augmented Covariance Matrix + Tangent Space + SVM** (`ACM+TS+SVM`, `AUG_TANG_SVM`) | `MOABB` **(1)** | Delay-embeds `order` lags separated by `lag` samples → $(C \cdot \text{order})$ SPD matrix; requires $T > \text{order} \cdot \text{lag}$ | **`MOABBPipelineClassifier("AUG_TANG_SVM")`** |
| **1C. Riemannian Distance & TS** | **Filter-Bank Extended SSVEP Covariance + MDM / TSLR / TSSVM** (`MDM-SSVEP`, `TSLR-SSVEP`, `TSSVM-SSVEP`) | `MOABB` **(1)** | **Requires `sfreq` AND per-class stimulus frequencies `freqs`** to construct narrowband sub-bands per target frequency | **`Missing`** *(excluded from `MOABBPipelineClassifier` due to `freqs` requirement)* |
| **1D. SSVEP / c-VEP Template & CCA/TRCA** | **Standard Sinusoidal CCA** (`SSVEP CCA`, `CCA-SSVEP`) | `MOABB` **(1)** | **Requires `sfreq` AND per-class stimulus `freqs`** (synthesises $\sin/\cos$ harmonics); $T > C$ | **`Missing`** *(note: `TemplateCCAClassifier` in `aeon-neuro` is **data-driven class-mean template CCA** = `itCCA`, which needs no `freqs`)* |
| **1D. SSVEP / c-VEP Template & CCA/TRCA** | **Individual Template CCA** (`itCCA-SSVEP`, `TemplateCCA`) | `MOABB` **(1)** | Time-locked trials; **requires $T > C$** for sample covariance whitening; no `freqs` or `sfreq` required | **`Standalone`** (`TemplateCCAClassifier`) |
| **1D. SSVEP / c-VEP Template & CCA/TRCA** | **Extended CCA** (`eCCA-SSVEP`) | `MOABB` **(1)** | **Requires `sfreq` AND per-class stimulus `freqs`** + training trials; $T > C$ | **`Missing`** |
| **1D. SSVEP / c-VEP Template & CCA/TRCA** | **Multiset CCA & Sum-of-Squared-Correlations** (`MsetCCA-SSVEP`, `SSCOR-SSVEP`) | `MOABB` **(1)** | Multi-trial per class at fit time; time-locked epochs; no `freqs` required mathematically (though MOABB paradigm passes SSVEP metadata) | **`Missing`** |
| **1D. SSVEP / c-VEP Template & CCA/TRCA** | **Task-Related Component Analysis** (`TRCA-SSVEP`, ensemble/filter-bank TRCA) | `MOABB` **(1)** | Time-locked trials ($\ge 2$ trials/class); single-band TRCA needs no `sfreq`/`freqs`; **filter-bank `FBTRCA` requires `sfreq`** | **`Standalone`** (`TRCAClassifier` — single-band & ensemble; filter-bank `FBTRCA` sub-banding not yet built in) |
| **1D. SSVEP / c-VEP Template & CCA/TRCA** | **Reference-Projected TRCA & Task-Discriminant Component Analysis** (`TRCA-R-SSVEP`, `TDCA-SSVEP`) | `MOABB` **(1)** | **Requires `sfreq` AND per-class stimulus `freqs`** for orthogonal sinusoidal projection (`TDCA` also augments $l$ delayed samples) | **`Missing`** |
| **1E. Spectral / Band-Power / Hand-Crafted** | **Channel Log-Variance + LDA / SVM** (`LogVariance+LDA`, `LogVariance+SVM`) | `MOABB` **(1)** | `sfreq` only if pre-bandpassed; works for any $C \ge 1, T \ge 2$ | **`MOABBPipelineClassifier("LogVar_LDA" / "LogVar_SVM")`** |
| **1E. Spectral / Band-Power / Hand-Crafted** | **Differential Entropy + Logistic Regression** (`DE + LR`, 5-band $\delta/\theta/\alpha/\beta/\gamma$) | *(Standard SEED emotion baseline; standalone in `aeon-neuro`)* **(0 in surveyed 7, canonical in emotion lit.)** | **Requires `sfreq` > 90 Hz** for default $\gamma$ band (30–45 Hz) or custom `bands` < Nyquist; $T$ > filter `padlen` ($\ge 28$) | **`Standalone`** (`DifferentialEntropyClassifier`) |
| **1E. Spectral / Band-Power / Hand-Crafted** | **Welch Co-Spectra + Log1p + Logistic Regression** (`CoSpectraLogLR`) | `NB` **(1)** | **Requires `sfreq`** (`fmin=2, fmax=40` Hz) and $T \ge 128$ (`window=128`) | **`Missing`** *(easy `pyriemann.estimation.CoSpectra` pipeline)* |
| **1E. Spectral / Band-Power / Hand-Crafted** | **Multi-Domain Hand-Crafted Summary Features + LDA / SVM / MLP** (`BrainfeaturesLDA`, `BrainfeaturesSVM` in ETH; `YASA` PyTorch stats+bandpower MLP in Arena) | `Arena` (`YASA`), `ETH` (`brainfeatures`) **(2)** *(+ `EEGDash` feature bank)* | **Requires `sfreq`** (for spectral bands up to 45 Hz); channel-count invariant (`YASA` pools channel mean/std) | **`Missing`** |

---

### Family 2: Supervised EEG Deep Learners

| Sub-family | Canonical Algorithm & Aliases | Benchmarks (`Ext. Count`) | Hard Input Requirements (`sfreq`, `ch_names`/3D, min window $T$) | Current `aeon-neuro` Status |
| :--- | :--- | :--- | :--- | :--- |
| **2A. CNN** | **EEGNet** (`EEGNet`, `EEGNetv4`, `EEGNet_8_2`) | `MOABB`, `Arena`, `NB`, `Ada`, `Omni` + `BD` **(5)** | Fixed $(C, T)$ per fit; default kernel/pooling requires $T \ge 64$ (at ~128 Hz); no `ch_names` | **`Standalone`** (`EEGNetClassifier`) + **`BraindecodeClassifier (tested)`** + **`NeuralBenchDeepClassifier`** |
| **2A. CNN** | **ShallowFBCSPNet** (`ShallowConvNet`, `shallow_fbcsp_net`) | `MOABB`, `Arena`, `NB` + `BD` **(3)** | $C \ge 2$ (Braindecode `CombinedConv` fails on $C=1$); pool size 75 / stride 15 requires $T \ge 100$ (designed for ~250 Hz) | **`BraindecodeClassifier (tested)`** + **`NeuralBenchDeepClassifier`** |
| **2A. CNN** | **Deep4Net** (`DeepConvNet`, `deep4net`) | `MOABB`, `Arena`, `NB` + `BD` **(3)** | $C \ge 2$ in Braindecode (`CombinedConv`); 4× stride-3 max-pools require $T \ge 200$ (`aeon-neuro` standalone works for $C \ge 1$ and adapts short $T$) | **`Standalone`** (`DeepConvNetClassifier`) + **`BraindecodeClassifier (tested)`** + **`NeuralBenchDeepClassifier`** |
| **2A. CNN** | **EEGNeX** (`EEGNeX`, `EEGNeX-8,32`) | `MOABB`, `Arena`, `NB(yaml)` + `BD`, `EEGDash` **(2 + 1 yaml)** | Fixed $(C, T)$; dilated convs + pooling require $T \ge 128$; no `ch_names` | **`BraindecodeClassifier (tested)`** |
| **2A. CNN** | **EEGSimpleConv** (`SimpleConv`) | `NB(yaml)` + `BD` **(0 + 1 yaml)** | Requires `sfreq` for internal resampling step; $T \ge 64$ | **`BraindecodeClassifier (tested)`** |
| **2A. CNN** | **SimpleConvTimeAgg** *(3D-position ChannelMerger + dilated GLU ConvNet)* | `NB` **(1)** | **Requires 3D `ch_positions` (`channel_names` mapped to standard 10-20 3D coords)** | **`Missing`** *(implemented in `neuraltrain`, distinct from Braindecode's `EEGSimpleConv`)* |
| **2A. CNN** | **LMDA-Net** (`LMDA`, `LDMA`) | `Ada` **(1)** | Fixed $(C, T)$; $T \ge 64$; no `ch_names` | **`Missing`** |
| **2A. CNN** | **EEGWaveNet** (`eegwavenet`) | `Arena` **(1)** | Fixed $(C, T)$; multi-scale depthwise convs ($T \ge 64$); no `ch_names` | **`Missing`** |
| **2A. CNN** | **EEGInceptionMI**, **SCCNet**, **TIDNet** | `BD` only **(0)** | Fixed $(C, T)$ (`SCCNet` also takes `sfreq`); $T \ge 128$ | **`BraindecodeClassifier (tested)`** |
| **2A. CNN** | **EEGSym** | `BD` only **(0)** | **Requires `sfreq` AND `channel_names`** matching 8–16 symmetric 10-20 pairs | **`BraindecodeClassifier (tested)`** |
| **2A. CNN** | **SincShallowNet** | `BD` only **(0)** | **Requires `sfreq`**; $T \ge 100$ | **`BraindecodeClassifier (tested)`** |
| **2B. Filter-Bank CNN** | **FBCNet** (`fbcnet`) | `Arena` + `BD` **(1)** | **Requires `sfreq` > 76 Hz** (default 9 Chebyshev bands 4–40 Hz) and $T$ divisible by `stride_factor` (typically $T \ge 200$) | **`BraindecodeClassifier (tested)`** |
| **2B. Filter-Bank CNN** | **IFNet** (`ifnet`) | `Arena` + `BD` **(1)** | **Requires `sfreq`**; $T \ge 128$ | **`BraindecodeClassifier (tested)`** |
| **2B. Filter-Bank CNN** | **ADFCNN** (`adfcnn`) | `Arena` **(1)** | Dual-scale temporal filter-bank + spatial conv + self-attention; $T \ge 128$; no `ch_names` | **`Missing`** |
| **2B. Filter-Bank CNN** | **FBMSNet**, **FBLightConvNet** | `BD` only **(0)** | **Require `sfreq` > 76 Hz**; $T \ge 200$ | **`BraindecodeClassifier (tested)`** |
| **2C. CNN + Attention / Transformer** | **EEGConformer** (`Conformer`, `eegconformer`) | `Arena`, `NB`, `Ada`, `Omni` + `BD` **(4)** | Fixed $(C, T)$; conv patch stride 15 / pool 75 expects $T \ge 100$ (`aeon-neuro` standalone adapts pooling cleanly) | **`Standalone`** (`EEGConformerClassifier`) + **`BraindecodeClassifier (tested)`** + **`NeuralBenchDeepClassifier`** |
| **2C. CNN + Attention / Transformer** | **ATCNet** (`atcnet`) | `Arena`, `NB` + `BD` **(2)** | Fixed $(C, T)$; sliding-window + dilated TCN requires $T \ge 250$ under default kernel/pool sizes | **`BraindecodeClassifier (tested)`** *(also works with `NeuralBenchDeepClassifier`)* |
| **2C. CNN + Attention / Transformer** | **CTNet** (`ctnet`) | `Arena`, `NB` + `BD` **(2)** | Fixed $(C, T)$; pool sizes 8×8 require $T \ge 128$ | **`BraindecodeClassifier (tested)`** + **`NeuralBenchCTNetClassifier`** |
| **2C. CNN + Attention / Transformer** | **MSVTNet** (`msvtnet`) | `Arena` + `BD` **(1)** | Fixed $(C, T)$; multi-branch conv pooling requires $T \ge 128$ | **`BraindecodeClassifier (tested)`** |
| **2C. CNN + Attention / Transformer** | **MSCFormer** (`mscformer`) | `Arena` + `BD` **(1)** | Fixed $(C, T)$; $T \ge 128$ | **`BraindecodeClassifier (tested)`** |
| **2C. CNN + Attention / Transformer** | **TMSA-Net** (`TMSANet`, `tmsanet`) | `Arena` + `BD` **(1)** | Fixed $(C, T)$; $T \ge 128$ | **`BraindecodeClassifier (tested)`** |
| **2C. CNN + Attention / Transformer** | **DBConformer** (`dbconformer`) | `Arena` **(1)** | Dual-branch temporal + spatial Conformer; fixed $(C, T)$, $T \ge 100$; no `ch_names` | **`Missing`** |
| **2C. CNN + Attention / Transformer** | **ST-Tran** (`S&T-Transformer`, `EEGTransformer`) | `Ada` **(1)** | Spatial channel self-attention + temporal conv + temporal Transformer; fixed $(C, T)$, $T \ge 64$ | **`Missing`** |
| **2C. CNN + Attention / Transformer** | **AttentionBaseNet**, **SSTDPN**, **TCFormer** | `BD` only **(0)** | Fixed $(C, T)$; $T \ge 128$ | **`BraindecodeClassifier (tested)`** |
| **2D. GNN** | **DGCNN** | `BD` only **(0)** | **Requires `channel_names` / `chs_info`**; $T \ge 64$ | **`BraindecodeClassifier (tested)`** |
| **2D. GNN** | **GCNsNet** | `BD` only **(0)** | Computes Pearson correlation graph directly from input channels (no `channel_names` needed); $C \ge 2, T \ge 64$ | **`BraindecodeClassifier (tested)`** |
| **2E. TCN / RNN / Hybrid** | **BDTCN / TCN** (`bdtcn`) | `NB` + `BD` **(1)** | Dilated causal conv blocks; receptive field typically expects $T \ge 128$; works on $C \ge 1$ | **`BraindecodeClassifier (tested)`** *(also works with `NeuralBenchDeepClassifier`)* |
| **2E. TCN / RNN / Hybrid** | **EEGTCNet** (`KerasEEGTCNet`) | `MOABB` + `BD` **(1)** | Fixed $(C, T)$; $T \ge 128$ | **`BraindecodeClassifier (tested)`** |
| **2E. TCN / RNN / Hybrid** | **EEGITNet** (`KerasEEGITNet`) | `MOABB` + `BD` **(1)** | Fixed $(C, T)$; $T \ge 128$ | **`BraindecodeClassifier (tested)`** |
| **2E. TCN / RNN / Hybrid** | **HybridNet** (`Deep4Net` + `ShallowFBCSPNet`) | `BD` only **(0)** | $C \ge 2, T \ge 200$ | **`BraindecodeClassifier (untested in BD)`** |
| **2F. Task-Specific (ERP / Emotion / Sleep / Seizure)** | **EEGInceptionERP** (`eeginception_erp`) | `Arena` + `BD` **(1)** | Requires `sfreq` (default 128 Hz); $T \ge 64$ | **`BraindecodeClassifier (tested)`** |
| **2F. Task-Specific** | **TSception** (`tsception`) | `Arena` + `BD` **(1)** | **Requires `sfreq`**, **even `n_channels`** (splits channels into symmetric left/right halves!), and $T \ge sfreq / 2$ | **`BraindecodeClassifier (tested)`** |
| **2F. Task-Specific** | **BiDANN** (`bidann`) | `Arena` **(1)** | Left/right hemisphere BiLSTM + domain/attention head; optional `ch_positions` (or index half-split) | **`Missing`** |
| **2F. Task-Specific** | **HSLT** (`hslt`) | `Arena` **(1)** | Hierarchical spatial-region Transformer (frontal/central/parietal/occipital/temporal); optional `ch_positions` | **`Missing`** |
| **2F. Task-Specific** | **DeepSleepNet** (`deepsleepnet`) | `Arena` + `BD` **(1)** | Designed for 30 s PSG epochs (`n_times ≈ 3000–7680`); Braindecode version hard-codes large conv strides expecting long $T \ge 1024$ | **`BraindecodeClassifier (untested in BD)`** |
| **2F. Task-Specific** | **U-Sleep** (`usleep`, `USleep`) | `Arena` + `BD` **(1)** | **Requires `sfreq`**; 12-stage 1D U-Net requires long $T$ (or padding) and emits `(batch, n_classes, n_epochs)` if $T$ spans multiple epochs | **`BraindecodeClassifier (untested in BD)`** *(needs single-epoch window alignment)* |
| **2F. Task-Specific** | **SleepEEGNet** (`sleepeegnet`) | `Arena` **(1)** | Dual-scale CNN + BiRNN attention; designed for multi-second epochs ($T \ge 256$) | **`Missing`** |
| **2F. Task-Specific** | **SleepTransformer** (`sleeptransformer`) | `Arena` **(1)** | Frame-level + epoch-level Transformer; pads short $T < 128$ automatically in Arena implementation | **`Missing`** |
| **2F. Task-Specific** | **SleepStagerChambon2018**, **ContraWR**, **SPARCNet**, **EEGMiner**, **SyncNet**, **BrainModule** | `BD` only **(0)** | `Chambon2018`, `ContraWR`, `EEGMiner`, `BrainModule` require `sfreq`; `Chambon2018`/`ContraWR` expect multi-second $T$ | **`BraindecodeClassifier (tested)`** |
| **2F. Task-Specific** | **AttnSleep**, **SleepStagerBlanco2020**, **NICE** | `BD` only **(0)** | `AttnSleep` expects ~30 s @ 100 Hz ($T \approx 3000$); `Blanco2020` expects $T \ge 500$ | **`BraindecodeClassifier (untested in BD)`** |
| **2F. Task-Specific** | **SlimSeiz** (`slimseiz`) | `Arena` **(1)** | Multi-block 1D CNN + BiGRU seizure detector; arbitrary $(C, T)$ with $T \ge 64$ | **`Missing`** |
| **2F. Task-Specific** | **SeizureTransformer**, **DANCE** | `BD` only **(0)** | Emit dense sample/event-level outputs rather than single trial logits (`DANCE` also requires `chs_info` & `sfreq`) | **`Missing`** *(incompatible with trial-level `_coerce_logits` without temporal pooling)* |

---

### Family 3: EEG Foundation Models

Grouped into **3A (Topology-Aware / Montage-Conditioned)** — models requiring 3D sensor coordinates (`ch_positions`), canonical 10-20/10-5 electrode names (`ch_names`), or fixed pretraining channel orderings (unless bypassed via external MNE spatial interpolation or a learned linear channel adapter) — versus **3B (Channel-Agnostic / Montage-Free)** — models whose spatial attention or pooling operates natively on arbitrary channel counts without electrode-identity lookup.

| Sub-family | Canonical Foundation Model & Variants | Benchmarks (`Ext. Count`) | Pretraining Paradigm & Corpus | Hard Input Requirements (`sfreq`, `ch_names` / 3D coords, patch length) | Current `aeon-neuro` Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **3A. Topology-Aware / Montage-Conditioned** | **LaBraM** (`Base` / `Large` / `Huge`) | `OEB`, `Arena`, `NB`, `Ada`, `ETH`, `Omni` + `BD` **(6)** | Neural discrete VQ-SNP tokenizer + masked patch code prediction (~2,500 h, 16–20 datasets) | **200 Hz**; 1 s patches (`patch_size=200`, max 16 patches = 16 s in Base); **requires `ch_names` in 128-electrode 10-20 vocabulary** (or `InterpolatedLaBraM` spline adapter) | **`Standalone`** (`LabramClassifier` — frozen `RidgeClassifierCV` probe; requires `ch_names`) |
| **3A. Topology-Aware / Montage-Conditioned** | **BIOT** (`prest-16ch`, `shhs-prest-18ch`, `six-datasets-18ch`) | `OEB`, `Arena`, `NB`, `Ada`, `Omni` + `BD` **(5)** | Contrastive + masked STFT-token reconstruction (SHHS, PREST, TUAB, TUEV, CHB-MIT, IIIC) | **200 Hz** (`patch/fft=200`, `hop=100`); **pretrained checkpoints bind 16 or 18 fixed channels** (`ch_names` matching / zero-fill / `InterpolatedBIOT` required when $C \ne 18$) | **`BraindecodeClassifier (untested in BD)`** *(class in `braindecode.models.BIOT`, **no** pretrained wrapper in `aeon-neuro`)* |
| **3A. Topology-Aware / Montage-Conditioned** | **BENDR** (`NtBendr`) | `OEB(cfg)`, `Arena`, `NB`, `ETH`, `Omni` + `BD` **(4 + 1 cfg)** | wav2vec 2.0 contrastive masked latent prediction over TUEG (~10,000+ h) | **256 Hz** (or 250 Hz); **pretrained conv stem expects 19 or 20 standard 10-20 channels** (requires channel selection, `InterpolatedBENDR`, or learned $C \to 19$ conv adapter); $T \ge 256$ | **`BraindecodeClassifier (untested in BD)`** *(class in `braindecode.models.BENDR`, **no** pretrained wrapper)* |
| **3A. Topology-Aware / Montage-Conditioned** | **REVE** (`Base`, `Large`) | `OEB`, `Arena`, `NB`, `Omni` + `BD` **(4)** | Masked autoencoding with 4D Fourier `(x, y, z, t)` positional embeddings (92 datasets, ~60,000 h, 25k subjects) | **200 Hz**; **requires 3D electrode coordinates `ch_positions`** (or `ch_names` resolvable against REVE's 3D electrode bank); arbitrary channel count $C$ | **`BraindecodeClassifier (untested in BD)`** *(class in `braindecode.models.REVE`, **no** pretrained wrapper)* |
| **3A. Topology-Aware / Montage-Conditioned** | **EEGPT** (25M params) | `OEB`, `Arena`, `Ada` + `BD` **(3)** | Dual self-supervised spatio-temporal representation alignment + masked reconstruction (multi-dataset BCI/sleep/clinical) | **256 Hz** (`T` padded/cropped to e.g. 1024); **requires `ch_names` in 58-electrode 10-20 codebook** (or `InterpolatedEEGPT` / trainable spatial conv adapter) | **`BraindecodeClassifier (untested in BD)`** *(class in `braindecode.models.EEGPT`, **no** pretrained wrapper)* |
| **3A. Topology-Aware / Montage-Conditioned** | **Neuro-GPT** (`NeuroGPT`) | `Arena`, `ETH`, `Omni` **(3)** | EEGConformer chunk encoder + causal GPT-2 next-chunk latent prediction on TUEG | **250 Hz** (`2 s` chunks = 500 samples); **projects/interpolates to fixed 22 standard 10-20 channels** via `ch_names` / MNE interpolation | **`Missing`** *(not in `braindecode.models`)* |
| **3A. Topology-Aware / Montage-Conditioned** | **LUNA** (`Base`, `Large`, `Huge`) | `Arena`, `NB` + `BD` **(2)** | Channel-unification cross-attention queries + contrastive + MAE on TUEG + Siena (>21,000 h) | **256 Hz** (or 128 Hz, `patch_size=40`); **requires 3D `ch_positions` / `chs_info`**; supports arbitrary $C$ natively | **`BraindecodeClassifier (untested in BD)`** *(class in `braindecode.models.LUNA`, **no** pretrained wrapper)* |
| **3A. Topology-Aware / Montage-Conditioned** | **BrainOmni** *(+ `BrainTokenizer`)* | `Omni` + `BD` **(1)** | Sensor-geometry SEANet RVQ tokenizer + masked criss-cross Transformer across **EEG + MEG** (~2,600+ h) | **256 Hz**; **requires 3D sensor `chs_info` / coordinates + orientation**; arbitrary $C$ | **`BraindecodeClassifier (untested in BD)`** *(class in `braindecode.models.BrainOmni`, **no** pretrained wrapper)* |
| **3A. Topology-Aware / Montage-Conditioned** | **NeuroLM** (`Base` / `Large` / `XL`) | `Omni` **(1)** | Text-aligned neural VQ tokenizer + causal autoregressive multi-task GPT-2 LLM (~25,000 h) | **200 Hz** (`patch_size=200`); **requires 10-20 `ch_names` embedding lookup** | **`Missing`** *(not in `braindecode.models`)* |
| **3A. Topology-Aware / Montage-Conditioned** | **CSBrain** | `Arena` + `BD` **(1)** | Cross-scale temporal/spectral tokenization + brain-region-structured sparse attention | **200 Hz** (`patch_size=200`); uses **`ch_names` / anatomical region grouping** | **`BraindecodeClassifier (untested in BD)`** |
| **3A. Topology-Aware / Montage-Conditioned** | **ST-EEGFormer** (`Small`, `Base`, `Large`) | `Arena` + `BD` **(1)** | Spatio-temporal masked autoencoding Transformer | **200 / 250 Hz**; requires **`ch_names` + `model_channel_indices`** | **`BraindecodeClassifier (untested in BD)`** |
| **3A. Topology-Aware / Montage-Conditioned** | **NeuroRVQ** *(+ `NeuroRVQTokenizer`)* | `Arena` + `BD` **(1)** | Multi-scale residual vector quantisation + masked token prediction | **200 Hz** (`patch_size=200`); requires **`channel_names` + `model_channel_indices`** | **`BraindecodeClassifier (untested in BD)`** |
| **3A. Topology-Aware / Montage-Conditioned** | **SignalJEPA** (`Contextual`, `PreLocal`, `PostLocal`) | `OEB(cfg)` + `BD` **(0 + 1 cfg)** | Joint-Embedding Predictive Architecture over local spatial-temporal windows | **128 Hz**; **requires 3D `chs_info` coordinates** (or `InterpolatedSignalJEPA`) | **`BraindecodeClassifier (untested in BD)`** |
| **3A. Topology-Aware / Montage-Conditioned** | **HEAR** (`Base`, `Large`) | `Arena` **(1)** | Hierarchical / hybrid EEG representation pretraining | **200 Hz** (`patched`); **requires `ch_names` + 3D `ch_positions`** | **`Missing`** |
| **3A. Topology-Aware / Montage-Conditioned** | **LEAD** (`Base`) | `Arena` **(1)** | Multi-dataset contrastive/self-supervised clinical & AD EEG pretraining (Wang et al., 2025) | `raw` (**128 / 200 Hz**); **requires canonical `ch_names`** | **`Missing`** |
| **3A. Topology-Aware / Montage-Conditioned** | **mdJPT** | `Arena` **(1)** | Multi-dataset Joint Pretrained Transformer | `patched` (**200 Hz**); **requires `ch_names`** | **`Missing`** |
| **3A. Topology-Aware / Montage-Conditioned** | **SleepGPT** (`Large`) | `Arena` **(1)** | Autoregressive / masked sequence pretraining on clinical PSG/EEG | `raw`; **requires `ch_names`** | **`Missing`** |
| **3A. Topology-Aware / Montage-Conditioned** | **AXON**, **ZUNA**, **EpiNT**, **Guetschel2026**, **EEGCLIP** | `BD` only **(0)** | Coordinate/channel-conditioned FMs & EEG-text CLIP in Braindecode v1.x | Require `chs_info` (`AXON`, `ZUNA`, `Guetschel2026`) or fixed `n_chans` (`EpiNT`, `EEGCLIP`) | **`BraindecodeClassifier (untested in BD)`** |
| **3B. Channel-Agnostic / Montage-Free** | **CBraMod** | `OEB`, `Arena`, `NB`, `Ada`, `Omni` + `BD` **(5)** | Masked time-frequency patch reconstruction on TUEG (~9,000 h) with asymmetric conditional 2D conv positional encoding | **200 Hz**; `patch_size=200` (1 s patches); **no `ch_names` or 3D coords needed** — accepts arbitrary $(C, P \times 200)$ natively | **`Standalone`** (`CBraModClassifier` — frozen `RidgeClassifierCV` probe; auto-pads $T$ to multiple of 200) |
| **3B. Channel-Agnostic / Montage-Free** | **EEGMamba** | `Arena`, `Omni` **(2)** | Bidirectional Mamba state-space masked patch reconstruction | **200 Hz** (`patch_size=200`); channel-agnostic in Arena (or optional 19-ch adapter in OmniEEG) | **`Missing`** *(not in `braindecode.models`)* |
| **3B. Channel-Agnostic / Montage-Free** | **FEMBA** (*Foundational EEG Mamba*) | `Omni` **(1)** | Lightweight bidirectional Mamba SSM masked autoencoder on TUAB/TUEG (Tegon et al., 2025; ~7.8M–48M params) | **256 Hz**; operates on patched/adapted $(B, C, T)$ without requiring 3D coordinates (OmniEEG uses channel adapter when $C$ differs from checkpoint) | **`Missing`** |
| **3B. Channel-Agnostic / Montage-Free** | **CodeBrain** | `Arena` + `BD` **(1)** | Decoupled temporal + frequency discrete codebooks + SSM/sliding-window attention | **200 Hz** (`patch_size=200`); **no `ch_names` or 3D coords required** | **`BraindecodeClassifier (untested in BD)`** *(class in `braindecode.models.CodeBrain`, **no** pretrained wrapper)* |
| **3B. Channel-Agnostic / Montage-Free** | **SleepFM** (`Upstream`, `Sleep Staging`, `Diagnosis`) | `Arena` + `BD` **(1)** | Leave-one-modality-out contrastive PSG/EEG pretraining (>14,000–100,000 h) with attention channel pooling | **128 Hz** (5 s / 30 s windows); **channel-order & count invariant** via attention pooling (no `ch_names` needed) | **`BraindecodeClassifier (untested in BD)`** *(class in `braindecode.models.SleepFM`, **no** pretrained wrapper)* |
| **3B. Channel-Agnostic / Montage-Free** | **TFM-Tokenizer** (`TFM · CHB-MIT`) | `Arena` + `BD` **(1)** | Time-frequency motif discrete VQ tokenization + masked Transformer | **200 Hz**; channel-agnostic per-channel/pooled tokenization | **`BraindecodeClassifier (untested in BD)`** |
| **3B. Channel-Agnostic / Montage-Free** | **Uni-DMFM** (`Base`) | `Arena` **(1)** | Unified diffusion / masked patch foundation model | **200 Hz** (`patched`); **no `ch_names` or 3D coords required** | **`Missing`** |
| **3B. Channel-Agnostic / Montage-Free** | **PBT**, **MEDFormer**, **MIRepNet**, **MVPFormer**, **EEGDINO** | `BD` only **(0)** | Patched / multi-granularity / DINO self-supervised encoders in Braindecode | Fixed/patched $(C, T)$ at 200–250 Hz; no 3D `chs_info` required | **`BraindecodeClassifier (untested in BD)`** |

---

### Family 4: General Time Series & Tabular Baselines

| Algorithm / Baseline Family | Benchmarks (`Ext. Count`) | How Used Upstream | Hard Input Requirements | Current `aeon-neuro` Status |
| :--- | :--- | :--- | :--- | :--- |
| **Constant / Chance Classifiers** (`chance`, `dummy` / `DummyClassifier`) | `NB` **(1)** | Sanity floor for imbalanced clinical/ERP tasks | None | Available via `scikit-learn` (`DummyClassifier`) |
| **Linear / Kernel Tabular Classifiers** (`LDA`, `LogisticRegression`, `RidgeClassifierCV`, `SVC`, `ElasticNet`) | `MOABB`, `OEB` (`ridge_probe`), `Arena` (`LinearClassifierHead`), `NB`, `ETH`, `Omni` **(6)** | Used exclusively as **readout heads** atop CSP, xDAWN, Riemannian tangent space, spectral features, or frozen FM embeddings — **never** on raw EEG | 2D tabular feature matrix $(N, D)$ | Used inside `CSPClassifier`, `XDAWNClassifier`, `DifferentialEntropyClassifier`, `CBraModClassifier`, `LabramClassifier`, `MOABBPipelineClassifier`, `NeuralBenchTSLRClassifier` |
| **General Multivariate TSC Algorithms** (`HIVECOTEV2`, `MultiRocketHydraClassifier`, `Arsenal`, `QUANT`, `DrCIF`, `InceptionTimeClassifier`, `TimeCNNClassifier`) | **None (`0 / 7`)** | **Completely absent across all seven external EEG benchmark suites** | Equal-length 3D `(n_cases, n_channels, n_timepoints)`; **no `sfreq`, `channel_names`, 3D coords, or stimulus `freqs` required** | **`Standalone` (re-exported in `aeon_neuro.classification`)**: `HIVECOTEV2`, `MultiRocketHydraClassifier`, `InceptionTimeClassifier`, `TimeCNNClassifier` *(plus full `aeon` / `tsml-eval` suite)* |

> **Key Bake-Off Takeaway on Family 4**: Not a single external EEG benchmark (`MOABB`, `OpenEEGBench`, `EEG-Arena`, `NeuralBench`, `AdaBrain-Bench`, `ETH EEG-Bench`, or `OmniEEG-Bench`) tests general-purpose multivariate time series classifiers (`MultiRocketHydra`, `HIVECOTEV2`, `QUANT`, `InceptionTime`, `DrCIF`). Evaluating Domain-Specific Classical vs Supervised EEG Deep vs EEG Foundation Models vs General Multivariate TSC on identical splits is a genuinely novel contribution of the `aeon-neuro` / `EEGBench` programme.

---

## Part 3 — Gap Analysis for `aeon-neuro`

### 3.1 Cross-Benchmark Frequency of Algorithms Not Yet First-Class in `aeon-neuro`

The table below lists every algorithm appearing in **`>= 2` external benchmarks** that is currently **`Missing`**, only in **`experimental/`**, or **`untested`** in `BraindecodeClassifier`:

| External Benchmarks (`Count`) | Algorithm | Family | Current `aeon-neuro` State | Action Tier |
| :---: | :--- | :--- | :--- | :--- |
| **5** (`OEB`, `Arena`, `NB`, `Ada`, `Omni`) | **`BIOT`** | Foundation Model (3A) | Class in `braindecode.models`, **no** pretrained wrapper | Tier 3 (FM) |
| **4 + 1 cfg** (`Arena`, `NB`, `ETH`, `Omni`, `OEB[cfg]`) | **`BENDR`** | Foundation Model (3A) | Class in `braindecode.models`, **no** pretrained wrapper | Tier 3 (FM) |
| **4** (`OEB`, `Arena`, `NB`, `Omni`) | **`REVE`** | Foundation Model (3A) | Class in `braindecode.models`, **no** pretrained wrapper | Tier 3 (FM) |
| **3** (`MOABB`, `Arena`, `NB`) | **`ShallowFBCSPNet`** (`ShallowConvNet`) | Supervised CNN (2A) | `BraindecodeClassifier (tested)` *(no native standalone like `DeepConvNetClassifier`)* | Already covered via BD (optional native wrapper) |
| **3** (`OEB`, `Arena`, `Ada`) | **`EEGPT`** | Foundation Model (3A) | Class in `braindecode.models`, **no** pretrained wrapper | Tier 3 (FM) |
| **3** (`Arena`, `ETH`, `Omni`) | **`Neuro-GPT`** (`NeuroGPT`) | Foundation Model (3A) | `Missing` | Tier 3 (FM) |
| **2 + 1 yaml** (`MOABB`, `Arena`, `NB[yaml]`, `EEGDash`) | **`EEGNeX`** | Supervised CNN (2A) | `BraindecodeClassifier (tested)` | Already covered via BD |
| **2** (`MOABB`, `NB`) | **`TSLR` / `CovTsLR`** (Riemannian Tangent Space + LR) | Classical Riemannian (1C) | Only in `experimental/_neuralbench.py` (`MOABBTSLRClassifier` / `NeuralBenchTSLRClassifier`) | Tier 1 (Easy win — promote to first-class `TangentSpaceClassifier`) |
| **2** (`MOABB`, `NB`) | **`XdawnCov + TangentSpace + Linear`** (`XdawnTsLR` / `XdawnCov_TS_SVM`) | Classical ERP / Riemannian (1B) | SVM variant only in `experimental/` (`MOABBPipelineClassifier`); `XdawnTsLR` missing | Tier 1 (Easy win — `pyriemann` `XdawnCovariances` + `TangentSpace`) |
| **2** (`Arena`, `NB`) | **`ATCNet`** | Supervised CNN+Attn+TCN (2C) | `BraindecodeClassifier (tested)` | Already covered via BD |
| **2** (`Arena`, `NB`) | **`CTNet`** | Supervised CNN+Transformer (2C) | `BraindecodeClassifier (tested)` + `NeuralBenchCTNetClassifier` | Already covered via BD |
| **2** (`Arena`, `NB`) | **Multi-domain Spectral + Time Summary Baseline** (`YASA` / `brainfeatures` / `CoSpectraLogLR`) | Classical Feature-Based (1E) | `Missing` (only 5-band `DifferentialEntropyClassifier` exists) | Tier 1 (Easy win) |
| **2** (`Arena`, `BD`) | **`U-Sleep`** & **`DeepSleepNet`** *(1 benchmark + Braindecode)* | Supervised Sleep (2F) | In `braindecode.models`, **not** in `SUPPORTED_MODELS` | Tier 1 (Easy win — test/adapt in `BraindecodeClassifier`) |
| **2** (`Arena`, `NB`) | **`LUNA`** | Foundation Model (3A) | Class in `braindecode.models`, **no** pretrained wrapper | Tier 3 (FM) |
| **2** (`Arena`, `Omni`) | **`EEGMamba`** | Foundation Model (3B) | `Missing` | Tier 3 (FM) |

---

### 3.2 Actionable Recommendations by Implementation Effort

#### Tier 1 — Easy Wins via Existing Dependencies (`pyriemann`, `mne`, `scipy`, `braindecode`)

1. **Promote First-Class Classical Estimators Out of `experimental/_neuralbench.py`**:
   - **`TangentSpaceClassifier`** (`Covariances('oas')` → `TangentSpace('riemann')` → configurable `LogisticRegressionCV` / `RidgeClassifierCV` / `SVC`): `TSLR` / `CovTsLR` is the single strongest classical baseline in both **MOABB** and **NeuralBench**, yet in `aeon-neuro` it currently lives only inside `classification/experimental/_neuralbench.py`, while `distance_based/` only exposes `RiemannianMDMClassifier` and `RiemannianKNNClassifier`.
   - **`FilterBankCSPClassifier` (`FBCSP`)**: Currently buried inside `MOABBPipelineClassifier("FBCSP_SVM")`. Promoting a clean `sfreq`-parameterised `FilterBankCSPClassifier` (multi-band Butterworth + per-band `CSPClassifier` + `SelectKBest(mutual_info_classif)` + `SVC`/`LDA`) directly covers Paper 1's planned MI baseline without pulling in `moabb` runtime machinery.
   - **`XdawnCovariances` Riemannian Pipeline (`XdawnTangentSpaceClassifier` / `XdawnMDMClassifier`)**: Bridges `XDAWNClassifier` (which flattens time samples into LDA) and `pyriemann.estimation.XdawnCovariances` (used by both MOABB and NeuralBench's `XdawnTsLR` across all 12 ERP tasks).
2. **Add Spectral Cross-Covariance & Multi-Domain Feature Baselines**:
   - **`CoSpectraLogLR`** (`pyriemann.estimation.CoSpectra` + `log1p` diagonal + `LogisticRegressionCV`): ~30 lines of NumPy/`pyriemann` code; gives `aeon-neuro` a stimulus-frequency-free SSVEP baseline matching NeuralBench when per-class flicker `freqs` metadata are unavailable.
   - **Filter-Bank `TRCAClassifier` (`n_fbands > 1`)**: Extending `TRCAClassifier` in `distance_based/_template.py` with optional Chebyshev Type-I sub-bands (`sfreq` optional; `n_fbands=1` default preserves current metadata-free API) upgrades `TRCAClassifier` to full Nakanishi et al. (2018) `FBTRCA` parity with MOABB without needing stimulus `freqs`. (Sinusoidal `CCA`, `eCCA`, and `TDCA` can also be added as optional `freqs`-parameterised modes on `TemplateCCAClassifier`/`TRCAClassifier`.)
3. **Validate & Harden Remaining Supervised Models Already in `braindecode.models`**:
   - **`DeepSleepNet`**, **`AttnSleep`**, **`SleepStagerBlanco2020`**, and **`HybridNet`** are already installed with `braindecode` and return 2D logits — adding them to `BraindecodeClassifier.SUPPORTED_MODELS` (with documented minimum `n_timepoints` bounds) gives immediate coverage of sleep baselines used in EEG-Arena.
   - **`USleep`** requires a small check in `BraindecodeClassifier._coerce_logits` (when `n_timepoints` matches 1 epoch it returns `(B, n_classes)` or `(B, n_classes, 1)`, whereas multi-epoch inputs return `(B, n_classes, n_epochs)`).

#### Tier 2 — Standalone Supervised Deep-Learning Ports (Not in Braindecode)

Among supervised models **not** in `braindecode.models`, none appears in `>= 3` external benchmarks, confirming that `aeon-neuro` + `BraindecodeClassifier` already covers virtually the entire consensus supervised EEG deep-learning canon (`EEGNet`, `ShallowFBCSPNet`, `Deep4Net`, `EEGConformer`, `ATCNet`, `CTNet`, `EEGNeX`, `FBCNet`, `IFNet`, `BDTCN`, `EEGTCNet`, `EEGITNet`, `MSVTNet`, `MSCFormer`, `TMSANet`, `TSception`, `EEGInceptionERP`). If standalone additions are desired for paradigm breadth, the highest-value candidates are:

1. **`LMDA-Net`** (`AdaBrain-Bench`; Miao et al., 2023) & **`DBConformer`** (`EEG-Arena`; Wang et al., 2024) — Self-contained, lightweight, metadata-free `(B, C, T)` architectures for MI/ERP/cognitive tasks (~120–180 lines of PyTorch each).
2. **`SleepTransformer`** (Phan et al., 2022) or **`SlimSeiz`** (`EEG-Arena`) — Compact frame-based sleep/seizure baselines that handle shorter windows more gracefully than `DeepSleepNet`.
3. **`SimpleConvTimeAgg`** (`NeuralBench`; El Ouahidi et al., 2023 / Défossez et al., 2023) — Worth porting **only** if testing whether 3D Fourier electrode-coordinate `ChannelMerger` layers help supervised CNNs; requires 3D `ch_positions`.

#### Tier 3 — EEG Foundation Models: Pretrained Wrappers, Metadata Plumbing & Adaptation Modes

`aeon-neuro` currently wraps two foundation models (`CBraModClassifier` and `LabramClassifier`), which are indeed the two most widely benchmarked FMs (`Labram` in 6 suites, `CBraMod` in 5). Extending foundation-model coverage for Paper 2 exposes four concrete gaps:

1. **High-Priority Missing FM Wrappers (Appearing in 3–5 External Benchmarks, Already in `braindecode.models`)**:
   - **`BIOTClassifier`** (**5** benchmarks; `braindecode/biot-pretrained-six-datasets-18chs`, 200 Hz) — Needs a clear channel-alignment policy (18-channel name subset/zero-fill or MNE spline interpolation `InterpolatedBIOT` as in OpenEEGBench).
   - **`REVEClassifier`** (**4** benchmarks; `brain-bzh/reve-base`, 200 Hz) — Consistently the strongest or top-2 foundation model in OpenEEGBench, EEG-Arena, NeuralBench, and OmniEEG-Bench; requires plumbing 3D `ch_positions` (or resolving `ch_names` against standard 10-5 3D coordinates).
   - **`BENDRClassifier`** (**4 + 1** benchmarks; 256 Hz, 19/20-ch adapter), **`EEGPTClassifier`** (**3** benchmarks; 256 Hz, 58-ch lookup), and **`LUNAClassifier`** (**2** benchmarks; 3D `chs_info`, arbitrary $C$) — All five model classes already ship inside `braindecode.models`!
   - *External-only FMs (`>= 2` benchmarks)*: **`Neuro-GPT`** (**3** benchmarks: Arena, ETH, Omni) and **`EEGMamba`** (**2** benchmarks: Arena, Omni; channel-agnostic Mamba SSM, alongside **`FEMBA`** in OmniEEG).
2. **Channel-Agnostic FMs Already in `braindecode.models` (Zero `ch_names` Friction)**:
   - **`CodeBrain`** and **`SleepFM`** (both in `EEG-Arena` + `braindecode.models`) accept arbitrary channel counts without `ch_names` or 3D coordinates, making them unusually clean fits for `aeon`'s standard `(n_cases, n_channels, n_timepoints)` estimator contract alongside `CBraModClassifier`.
3. **Frozen Linear Probe vs Fine-Tuning / LoRA Gap**:
   - Currently, `CBraModClassifier` and `LabramClassifier` in `aeon-neuro` implement **frozen encoder + `RidgeClassifierCV` probing only**. OpenEEGBench's live numbers illustrate why an optional `adaptation="ridge_probe" | "lora" | "full_finetune"` mode matters: on OpenEEGBench's 10-dataset average, `CBraMod` jumps from **14.02%** (`probe`) to **36.11%** (`full_finetune`), and `LaBraM` jumps from **12.85%** (`probe`) to **31.24%** (`full_finetune`). Benchmarking frozen probes alone risks understating FM ceilings, whereas benchmarking full fine-tuning alone obscures representation quality and compute cost — supporting both modes directly answers a central research question.
4. **Mandatory Pretraining-Corpus Leakage Tracking**:
   - Inspection of `neuralbench/plots/_models.py` (`_PT_*` sets) and `eeg.fm` client metadata (`264-6b39b4e5c290cc46.js`) shows pervasive overlap between FM pretraining corpora and standard downstream benchmarks:
     - **TUEG family (`TUAB`, `TUAR`, `TUEV`, `TUEP`, `TUSZ`, `TUSL`)**: In pretraining of `BENDR`, `CBraMod`, `LaBraM`, `BIOT` (subset), `LUNA` (subset), `REVE` (subset), `Neuro-GPT`.
     - **Motor Imagery & BCI (`PhysioNet-MI`, `BCIC-IV-2a/2b`, `High-Gamma`, `OpenBMI`, `Lee2019`, `Cho2017`)** and **Emotion (`SEED`)**: Present in pretraining of `EEGPT`, `LaBraM` (`PhysioNet-MI`, `SEED`), `REVE` (92-dataset corpus covers much of MOABB!), `ST-EEGFormer`, and `HEAR`.
   - Any foundation-model comparison in `EEGBench` / `aeon-neuro` must annotate `(model, dataset)` pretraining overlap explicitly and report stratified rankings on guaranteed **held-out / zero-overlap** datasets alongside full-archive aggregates.
