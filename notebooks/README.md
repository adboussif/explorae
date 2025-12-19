
# Binder Selection Pipeline – Complete Documentation

## Overall Objective

The notebook `binder_selection_pipeline.ipynb` implements a **robust machine learning pipeline** to distinguish binders (validated protein–protein interactions) from non-binders (design failures).

It follows the methodology of the reference paper (Overath, Max D., Andreas S. H. Rygaard, Christian P. Jacobsen, et al. *“Predicting Experimental Success in De Novo Binder Design: A Meta-Analysis of 3,766 Experimentally Characterised Binders.”* Preprint, bioRxiv, September 17, 2025. [https://doi.org/10.1101/2025.08.14.670059](https://doi.org/10.1101/2025.08.14.670059).)

The latter uses:

* **Sparse Logistic Regression** (L1 penalty) for classification
* **Greedy Feature Selection (Individuals + Interactions)** (greedy forward selection) with nested cross-validation (nested CV)

**Main output**: A trained model capable of predicting whether a PPI prediction is viable.


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


## Detailed Sections

### Data Loading and Exploration

**Source files**:

* `../src/data/positive_labeled_dataset_dG_SASA.csv` → Validated binders
* `../src/data/negative_labeled_dataset_dG_SASA.csv` → Design failures

**Process**:

1. Load both CSV files
2. Assign labels (1 = binder, 0 = non-binder)
3. Merge and randomly shuffle
4. Create `pKd = -log₁₀(Kd + ε)` from `prodigy_kd`
5. Clean numeric columns (replace commas with dots, handle NaNs)
6. Remove rows with NaNs in the selected features

**Features used**:

* `ipsae` – AlphaFold2 confidence (iPAE, interface Predicted Aligned Error)
* `pdockq2` – DockQ v2 quality score
* `pKd` – log-transformed binding affinity
* `ipTM+pTM` – combined AlphaFold TM confidence
* `dG_SASA_ratio` – energy / solvent-accessible surface ratio
* `prodigy_dg_internal` – PRODIGY internal energy prediction
* `ipTM` – interface template modeling score
* `dG_rosetta` – Rosetta energy scoring

**Key statistics**:

* Binder vs non-binder comparison

---

### Train / Validation / Test Split (Stratified)

**Critical importance**: Avoid **data leakage**

**Strategy**:

* **70% TRAIN**: Used for

  * Exploratory data analysis (EDA)
  * Feature selection
  * Model training
  * Internal cross-validation

* **10% VALIDATION**: Used for

  * Univariate feature evaluation
  * Threshold optimization (F1 maximization)
  * Tuning decisions

* **20% TEST**: Never touched beforehand

  * Single final evaluation
  * Performance reporting

**Stratification**: Preserves the positive/negative ratio in each split.

**Tracking**: Indices are stored (`train_indices`, `val_indices`, `test_indices`) for reproducibility.

---

### Exploratory Data Analysis (EDA)

#### Distributions

**Histograms**:

* Compare binders vs non-binders for each feature
* Reveal separability

#### Statistical Tests

**Mann–Whitney U test** (non-parametric):

* Compares distributions without assuming normality
* Robust to outliers

**FDR correction** (Benjamini–Hochberg):

* Controls the false discovery rate under multiple testing
* Adjusted p-values reported

**Effect size** (rank-biserial correlation):

* Ranges from −1 to 1, measures the magnitude of the difference
* Interpretation: 0.1 = small, 0.3 = medium, 0.5 = large

#### Bootstrap 95% CI

* Resampling with replacement: 1000 iterations
* Confidence intervals for median difference and rank-biserial correlation
* Robust to small sample sizes

#### Dimensionality

**2D PCA**:

* Visualizes binder vs non-binder separation

---

### Univariate Feature Evaluation

Evaluates each feature **independently** as a predictor.

**Protocol**:

1. For each feature `f`:

   * Fit a LogisticRegression model (L1, balanced) on TRAIN
   * Normalize using StandardScaler (fit on TRAIN, apply to VALIDATION)
   * Evaluate on the VALIDATION set only

2. Computed metrics:

   * **ROC AUC**: Area under the ROC curve
   * **Average Precision (AP)**: Area under the Precision–Recall curve
   * **Coefficients**: Signs and magnitudes

**Comparison with the paper**:

* Paper, Figure 3B: reports AP per univariate feature
* Our approach: identical; similar feature ranking expected

---

### Interaction Generation

**Scientific motivation**:

* No single feature is perfect
* Combining confidence + physics: product of two features
* Examples:

  * `ipsae × prodigy_dg_internal` → confidence × thermodynamics
  * `pdockq2 × dG_SASA_ratio` → interface quality × thermodynamic property

**Implementation**:

```
For each pair (i, j) with i < j:
    interaction = feature_i × feature_j
    Evaluate univariately on VALIDATION
    Compute AP
Keep the top 20 interactions by AP
```

**Total generated**:

* Single features: 8
* Pairwise combinations: C(8,2) = 28
* **Top 20 interaction candidates** for greedy selection

---

### Greedy Feature Selection with Nested CV

**Algorithm** (reproduced from the paper, section “Logistic Regression Classifier”):

```
selected_features = []
remaining_features = all_features (8 singles + 20 interactions)
improvement_threshold = 0.005

while remaining_features:
    current_AP = CV_score(selected_features, TRAIN)
    
    for candidate in remaining_features:
        test_AP = CV_score(selected_features + [candidate], TRAIN)
        if test_AP > best_AP:
            best_candidate = candidate
            best_AP = test_AP
    
    improvement = best_AP - current_AP
    
    if improvement ≥ improvement_threshold:
        selected_features.append(best_candidate)
        remaining_features.remove(best_candidate)
    else:
        STOP  # No sufficient improvement
        
return selected_features
```

**Cross-validation**:

* **Outer loop** (greedy): iterates over candidates
* **Inner loop** (robustness): 5-fold stratified CV on TRAIN

  * For each fold: fit/evaluate LogisticRegression
  * Metric: mean AP across the 5 folds
  * StandardScaler fit fold-by-fold (prevents leakage)

**Stopping criterion**:

* Condition: `ΔAP < 0.005` (no significant improvement)
* Prevents overfitting by adding spurious features

**Difference vs the paper**:

* Paper: Leave-One-Group-Out (LOGO) due to target-grouped data
* Here: 5-fold StratifiedKFold (non-grouped data)
* Same principle: multi-fold robustness + greedy selection

---

### Final Evaluation on the TEST Set

**Critical protocol**:

1. **First and only access to the TEST set**

2. **Training the final model**:

   * Selected features only
   * StandardScaler fit on the full TRAIN set
   * LogisticRegression (L1, balanced) fit on the full TRAIN set

3. **Threshold optimization**:

   * On the VALIDATION set: find threshold maximizing F1
   * Apply this threshold once to the TEST set

4. **Final metrics** (TEST set):

   * **ROC AUC**: Probability that a binder ranks above a random non-binder
   * **Average Precision (AP)**: Area under the Precision–Recall curve
   * **Precision**: TP / (TP + FP) = confidence in positive predictions
   * **Recall (Sensitivity)**: TP / (TP + FN) = binder coverage
   * **F1-score**: Harmonic mean of precision and recall
   * **Accuracy**: (TP + TN) / Total
   * **Specificity**: TN / (TN + FP) = non-binder rejection

5. **95% Confidence Intervals** (Bootstrap):

   * 1000 resamplings with replacement of the TEST set
   * 2.5 and 97.5 percentiles for CIs
   * Uncertainty bands on ROC/PR curves

6. **Confusion Matrix**:

   * Visualizes TP, TN, FP, FN
   * Quantitative error analysis

7. **False Negative Analysis** (missed binders):

---

## Key Parameters & Tuning

| Parameter             | Value     | Justification      |
| --------------------- | --------- | ------------------ |
| RANDOM_STATE          | 42        | Reproducibility    |
| Train/Val/Test        | 70/10/20  | ML standard        |
| Improvement threshold | 0.005     | Greedy stopping    |
| CV folds              | 5         | Stratified         |
| Penalty               | L1        | Sparse features    |
| Solver                | liblinear | L1 penalty         |
| class_weight          | balanced  | Class imbalance    |
| Bootstrap iterations  | 1000      | Robust CIs         |
| Top interactions      | 20        | Reduce overfitting |

---

## Use Cases

### Prediction on New Data

1. Compute the 8 single features
2. Compute the selected interactions (from the 20 candidates)
3. Normalize using the trained StandardScaler
4. Apply the LogisticRegression model
5. Compare predicted probability to the optimal threshold

### Interpretability

* Visualize distributions of selected features
* Compare coefficients → most influential features
* Analyze false negatives → model edge cases

### Iterative Improvement

* Add new biological features
* Recompute interactions
* Rerun greedy selection
* Compare TEST set performance

---

## Common Pitfalls & Solutions

### 1. **Data Leakage**

**Problem**: Using the TEST set before final evaluation
**Solution**: Strict separation — TRAIN (70%) → EDA, feature selection, training

### 2. **Overfitting from Too Many Features**

**Problem**: Adding too many features degrades test performance
**Solution**: Minimum improvement threshold (ΔAP = 0.005)

### 3. **Class Imbalance**

**Problem**: In the paper: 88% non-binders → biased model
**Solution**: `class_weight="balanced"` + AP metric (robust)

### 4. **Incorrect Normalization**

**Problem**: Fitting StandardScaler on non-separated data
**Solution**: Always fit scaler on TRAIN only, apply to VAL/TEST

### 5. **Default Decision Threshold**

**Problem**: Threshold 0.5 may be suboptimal
**Solution**: Optimize on VALIDATION (max F1), apply to TEST

---

## References

**Main Paper**: 
Overath, Max D., Andreas S. H. Rygaard, Christian P. Jacobsen, et al. *“Predicting Experimental Success in De Novo Binder Design: A Meta-Analysis of 3,766 Experimentally Characterised Binders.”* Preprint, bioRxiv, September 17, 2025. [https://doi.org/10.1101/2025.08.14.670059](https://doi.org/10.1101/2025.08.14.670059)

**Statistical Techniques**:

* Mann–Whitney U: non-parametric rank test
* Bootstrap: CI estimation without distributional assumptions
* Nested CV: robust internal + external validation
