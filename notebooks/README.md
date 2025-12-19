# Binder Selection Pipeline

The `binder_selection_pipeline.ipynb` notebook implements a robust machine learning pipeline to distinguish validated protein-protein binders from design failures.

It follows the methodology from the reference paper using sparse logistic regression with L1 penalty and greedy forward feature selection (individuals + interactions) via nested cross-validation.

 
## Pipeline Overview

1. **Data Loading and Cleaning**
   - Positive samples (binders)
   - Negative samples (non-binders)
   - Dataset merging and normalization

2. **Stratified Train / Validation / Test Split (70 / 10 / 20)**
   - Prevention of data leakage
   - Index tracking for full reproducibility

3. **Exploratory Data Analysis (EDA)**
   - Feature distributions and correlations
   - Statistical testing (Mann–Whitney U test)
   - Effect size estimation (rank-biserial correlation)
   - Bootstrap-based 95% confidence intervals

4. **Univariate Feature Evaluation**
   - Average Precision (AP) per feature
   - ROC AUC analysis

5. **Feature Interaction Generation**
   - Pairwise feature interactions (fᵢ × fⱼ)
   - Selection of top 20 interactions based on AP
   - Inclusion in the candidate feature pool

6. **Greedy Feature Selection with Nested Cross-Validation**
   - Iterative feature addition
   - Selection criterion: ΔAP ≥ 0.005
   - Internal 5-fold stratified cross-validation on the training set

7. **Final Evaluation on the Test Set**
   - Model trained on the full training set
   - Feature normalization using `StandardScaler`
   - Optimal decision threshold selected on the validation set
   - Performance metrics: AP, AUC, F1-score, Precision, Recall, Accuracy
   - Bootstrap-based 95% confidence intervals
   - False negative error analysis

## Data Loading and Features

Source files include `../src/data/positive_labeled_dataset_dG_SASA.csv` for binders and `../src/data/negative_labeled_dataset_dG_SASA.csv` for non-binders.

Process merges datasets, assigns labels (1=binder, 0=non-binder), computes `pKd = -log₁₀(Kd + ε)`, cleans numeric columns, and removes NaN rows.

Key features:
- `ipsae`: AlphaFold2 interface confidence (iPAE)
- `pdockq2`: DockQ v2 quality score
- `pKd`: Log-transformed binding affinity
- `ipTM+pTM`: Combined AlphaFold TM confidence
- `dG_SASA_ratio`: Energy/surface area ratio
- `prodigy_dg_internal`: PRODIGY internal energy prediction
- `ipTM`: Interface template modeling score
- `dG_rosetta`: Rosetta energy score

 
## TRAIN/TEST SPLIT

**Avoid any data leakage**

**Before any model evaluation**:
- Split Train/Validation/Test in 70/10/20 with stratification
- All model selection and feature engineering is performed **only** on the training set
- The test set is completely set aside and **never** used for:
  - univariate feature evaluation
  - greedy feature selection
  - interaction feature generation or evaluation
- Final evaluation is performed **only** on the test set, using models trained on the train set

 

## EDA Details

Histograms compare binder vs non-binder distributions per feature.

Mann-Whitney U tests (FDR-corrected) assess differences, with rank-biserial effect sizes and bootstrap 95% CIs for medians.

PCA visualizes 2D separability between classes.

## Univariate Evaluation

The original study tests **each metric individually** to identify the best binding predictors.

**Paper's logic**:
- For each feature, calculate its ability to separate binders from non-binders
- Use Average Precision (AP) as primary metric (robust to class imbalance ~12% binders in their dataset, here ~50%)
- Also report ROC AUC for comparison
- Identify the best individual predictors

**Our implementation**:
- Univariate training on the full TRAIN set (70% of data)
- Normalization with StandardScaler
- Simple logistic regression for each feature (univariate)
- ROC AUC and AP calculation on VAL for unbiased results


 
 
### Explanation of Interaction Features

The paper generates **interaction features** by multiplying features pairwise: $f_i \times f_j$

**Scientific logic**:
- A single metric (ex: AF2 confidence) may not be discriminative enough
- Combining confidence + physics can improve prediction
  - Ex: (high AF2 confidence) × (favorable dG/SASA) = very good binding
  - Ex: (low AF2 confidence) × (anything) = design failure even with good energy
- Some interactions are more predictive than individual features

**Our implementation**:
- Generate all pairwise combinations $f_i \times f_j$ on TRAIN
- Evaluate each product univariately (TRAIN → VAL)
- Keep top 20 interactions by AP
- These interactions become candidates for greedy selection

 
# Greedy Feature Selection with Nested Cross-Validation

As in the paper (section 6, Figure 4), we implement **greedy forward selection** with **nested stratified cross-validation**.

## Paper Logic

The paper (section "Logistic regression classifier") uses:
1. **Leave-One-Group-Out (LOGO) CV externe**: each target/group is left out as test
2. **Internal greedy selection**: for each fold, build a sparse logistic model (L1 penalty) by adding features one by one
3. **Stopping criterion**: add a feature only if it improves AP by > 0.005
4. **Class imbalance handling**: `class_weight="balanced"` in LogisticRegression
5. **Normalization**: z-score per fold (fit on internal TRAIN)

## Our Implementation

- Greedy selection with iterative loop
- **Nested Cross-Validation**: StratifiedKFold externe (5 folds) for robustness
- At each iteration, test adding each candidate feature
- Metrics = average precision (AP) calculated with internal CV
- Improvement threshold: ΔAP ≥ 0.005 to add a feature
- Initial pool: all simple features + top 20 interactions
- **Difference**: StratifiedKFold (5-fold) instead of LOGO-CV (our data lacks explicit target grouping)

 

 
 
# FINAL EVALUATION on TEST SET

## Paper Logic

The paper (section "Outer Loop"):
- **Leave-One-Group-Out external**: performance of selected model on test group
- **Metrics**: AP, ROC AUC, F1, precision, recall
- **Optimal threshold**: adjusted to maximize F1 on Validation data
- **Robustness**: uncertainty/variance over LOGO outer loop (multiple folds)

## Our Implementation

- TEST set never touched during selection or internal CV
- First and **only** access to TEST set here
- Train final model on TRAIN with selected features
- Normalization: StandardScaler fit on TRAIN, applied to TEST
- Full evaluation: AP, ROC AUC, F1, precision, recall, accuracy
- Optimal threshold: find threshold that maximizes F1 on VAL and apply to TEST
- Confusion matrix and detailed analysis


## Key Parameters

| Parameter              | Value          | Justification                  |
|------------------------|----------------|-------------------------------|
| RANDOM_STATE           | 42             | Reproducibility                |
| Split ratios           | 70/10/20       | Standard ML practice           |
| ΔAP threshold          | 0.005          | Greedy stopping criterion      |
| CV folds               | 5              | Stratified robustness          |
| Penalty                | L1             | Sparse selection               |
| Solver                 | liblinear      | L1 compatibility               |
| class_weight           | balanced       | Class imbalance                |
| Bootstrap iterations   | 1000           | Robust CIs                     |
| Top interactions       | 20             | Overfitting control            |

## Usage

For new predictions: compute 8 base features + selected interactions, scale with fitted StandardScaler, apply LogisticRegression, threshold at optimized value.

Interpret via feature coefficients and false negative review.

Iterate by adding biological features and re-running selection.
 

## Reference

Bryant et al. "Predicting Experimental Success in de novo Binder Design." bioRxiv 2025. [https://www.biorxiv.org/content/10.1101/2025.08.14.670059v1.full.pdf](https://www.biorxiv.org/content/10.1101/2025.08.14.670059v1.full.pdf)

