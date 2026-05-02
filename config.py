"""
config.py — Central configuration for the IDS ML project.
All paths, feature lists, and hyperparameters live here so every
notebook/script stays in sync.
"""

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_RAW_PATH       = "data/raw"
DATA_PROCESSED_PATH = "data/processed"
DATA_FINAL_PATH     = "data/final"
OUTPUT_DIR          = "outputs"
ARTIFACTS_DIR       = "artifacts"
LOGS_DIR            = "logs"

# Processed file names
CLEANED_CSV         = f"{DATA_PROCESSED_PATH}/merged_cleaned.csv"
X_TRAIN_CSV         = f"{DATA_FINAL_PATH}/X_train.csv"
X_TEST_CSV          = f"{DATA_FINAL_PATH}/X_test.csv"
Y_TRAIN_CSV         = f"{DATA_FINAL_PATH}/y_train.csv"
Y_TEST_CSV          = f"{DATA_FINAL_PATH}/y_test.csv"

SCALER_PKL          = f"{ARTIFACTS_DIR}/scaler.pkl"
LABEL_ENCODER_PKL   = f"{ARTIFACTS_DIR}/label_encoder.pkl"
RF_MODEL_PKL        = f"{ARTIFACTS_DIR}/random_forest_model.pkl"
ALERTS_LOG          = f"{LOGS_DIR}/alerts.log"

# ---------------------------------------------------------------------------
# Dataset column names
# ---------------------------------------------------------------------------
LABEL_COLUMN  = "Label"
BENIGN_LABEL  = "BENIGN"

# 18 core features as specified in the lab PDF (short CIC-IDS2017 names)
SELECTED_FEATURES = [
    "Protocol",
    "Flow Duration",
    "Tot Fwd Pkts",
    "Tot Bwd Pkts",
    "TotLen Fwd Pkts",
    "TotLen Bwd Pkts",
    "Fwd Pkt Len Mean",
    "Bwd Pkt Len Mean",
    "Flow Byts/s",
    "Flow Pkts/s",
    "Pkt Len Mean",
    "Pkt Len Std",
    "SYN Flag Cnt",
    "ACK Flag Cnt",
    "FIN Flag Cnt",
    "RST Flag Cnt",
    "PSH Flag Cnt",
    "URG Flag Cnt",
]

# Some CSV versions of CIC-IDS2017 ship with longer column names.
# This mapping is used to normalise them before feature selection.
FEATURE_ALT_NAMES = {
    "Tot Fwd Pkts":     "Total Fwd Packets",
    "Tot Bwd Pkts":     "Total Backward Packets",
    "TotLen Fwd Pkts":  "Total Length of Fwd Packets",
    "TotLen Bwd Pkts":  "Total Length of Bwd Packets",
    "Fwd Pkt Len Mean": "Fwd Packet Length Mean",
    "Bwd Pkt Len Mean": "Bwd Packet Length Mean",
    "Flow Byts/s":      "Flow Bytes/s",
    "Flow Pkts/s":      "Flow Packets/s",
    "Pkt Len Mean":     "Packet Length Mean",
    "Pkt Len Std":      "Packet Length Std",
    "SYN Flag Cnt":     "SYN Flag Count",
    "ACK Flag Cnt":     "ACK Flag Count",
    "FIN Flag Cnt":     "FIN Flag Count",
    "RST Flag Cnt":     "RST Flag Count",
    "PSH Flag Cnt":     "PSH Flag Count",
    "URG Flag Cnt":     "URG Flag Count",
}

# ---------------------------------------------------------------------------
# Hyperparameters
# ---------------------------------------------------------------------------
HYPERPARAMS = {
    # Train/test split
    "train_test_split": {
        "test_size": 0.2,
        "random_state": 42,
        "stratify": True,
    },

    # SMOTE — over-sample minority classes to 10 % of the majority class
    "smote": {
        "random_state": 42,
        "minority_threshold_pct": 0.10,
    },

    # RandomUnderSampler — cap majority class at 3× the minority target
    "random_under_sampler": {
        "random_state": 42,
        "majority_ratio": 3,
    },

    # Individual model params
    "logistic_regression": {
        "max_iter": 1000,
        "random_state": 42,
        "class_weight": "balanced",
        "solver": "lbfgs",
        "multi_class": "auto",
    },
    "svm": {
        # TV3 uses Nystroem approximation (kernel="rbf") for scalability
        "kernel": "rbf",
        "random_state": 42,
        "nystroem_n_components": 300,
    },
    "naive_bayes": {
        # CategoricalNB with equal-width binning (n_bins=10)
        "n_bins": 10,
    },
    "knn": {
        "n_neighbors": 5,
        "n_jobs": -1,
    },
    "random_forest": {
        "n_estimators": 100,
        "random_state": 42,
        "n_jobs": -1,
        "warm_start": True,   # used for incremental training with progress bar
    },
}
