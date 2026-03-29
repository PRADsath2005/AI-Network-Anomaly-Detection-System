"""
preprocess.py
-------------
Handles loading, cleaning, encoding, and normalization of the NSL-KDD dataset.
FIX: Assigns correct column names, handles missing values and duplicates properly.
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split

# -------------------------------------------------------------------
# NSL-KDD column definitions (41 features + label + difficulty level)
# -------------------------------------------------------------------
NSL_KDD_COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes",
    "dst_bytes", "land", "wrong_fragment", "urgent", "hot",
    "num_failed_logins", "logged_in", "num_compromised", "root_shell",
    "su_attempted", "num_root", "num_file_creations", "num_shells",
    "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
    "dst_host_srv_count", "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate", "dst_host_srv_serror_rate", "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate", "label", "difficulty_level",
]

# Categorical columns requiring encoding
CATEGORICAL_COLS = ["protocol_type", "service", "flag"]

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TRAIN_FILE = os.path.join(DATA_DIR, "KDDTrain+.txt")
TEST_FILE  = os.path.join(DATA_DIR, "KDDTest+.txt")


def _load_file(filepath: str) -> pd.DataFrame:
    """Load a raw NSL-KDD text file with correct column names."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Dataset not found: {filepath}\n"
            "Run: python download_dataset.py"
        )
    df = pd.read_csv(filepath, header=None, names=NSL_KDD_COLUMNS)
    return df


def _binarize_labels(series: pd.Series) -> pd.Series:
    """Convert multi-class labels to binary: 0 = Normal, 1 = Attack."""
    return series.apply(lambda x: 0 if str(x).strip().lower() == "normal" else 1)


def load_and_preprocess(test_size: float = 0.2, random_state: int = 42):
    """
    Full pipeline: load → clean → encode → normalize → split.

    Returns
    -------
    X_train, X_test, y_train, y_test : np.ndarray
    feature_names                      : list[str]
    scaler                             : fitted MinMaxScaler
    encoders                           : dict of fitted LabelEncoders
    """
    # 1. Load -------------------------------------------------------------
    if os.path.exists(TRAIN_FILE) and os.path.exists(TEST_FILE):
        train_df = _load_file(TRAIN_FILE)
        test_df  = _load_file(TEST_FILE)
        df = pd.concat([train_df, test_df], ignore_index=True)
    else:
        # Fallback: generate synthetic data so the app still runs
        print("[WARN] NSL-KDD files not found. Generating synthetic dataset.")
        df = _generate_synthetic_data()

    # 2. Drop difficulty level (not a feature) ----------------------------
    df.drop(columns=["difficulty_level"], inplace=True, errors="ignore")

    # 3. Remove duplicates ------------------------------------------------
    before = len(df)
    df.drop_duplicates(inplace=True)
    print(f"[PREPROCESS] Removed {before - len(df)} duplicate rows.")

    # 4. Handle missing values -------------------------------------------
    df.replace("?", np.nan, inplace=True)
    # Numeric columns: fill with median
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for col in num_cols:
        if df[col].isnull().any():
            df[col].fillna(df[col].median(), inplace=True)
    # Categorical: fill with mode
    for col in CATEGORICAL_COLS:
        if col in df.columns and df[col].isnull().any():
            df[col].fillna(df[col].mode()[0], inplace=True)

    # 5. Encode categorical columns ---------------------------------------
    encoders = {}
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            encoders[col] = le

    # 6. Binarize labels -------------------------------------------------
    df["label"] = _binarize_labels(df["label"])

    # 7. Separate features / labels --------------------------------------
    X = df.drop(columns=["label"])
    y = df["label"]
    feature_names = X.columns.tolist()

    # 8. Normalize -------------------------------------------------------
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # 9. Train/test split ------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y.values, test_size=test_size,
        random_state=random_state, stratify=y
    )

    print(f"[PREPROCESS] Train samples: {len(X_train)} | Test samples: {len(X_test)}")
    print(f"[PREPROCESS] Attack rate  : {y.mean() * 100:.1f}%")

    return X_train, X_test, y_train, y_test, feature_names, scaler, encoders


# -------------------------------------------------------------------
# Synthetic data fallback (when NSL-KDD files are absent)
# -------------------------------------------------------------------
def _generate_synthetic_data(n_samples: int = 5000) -> pd.DataFrame:
    """Generate a minimal synthetic dataset mirroring NSL-KDD structure."""
    rng = np.random.default_rng(42)
    feature_cols = [c for c in NSL_KDD_COLUMNS if c not in ("label", "difficulty_level")]
    data = {}
    for col in feature_cols:
        if col in CATEGORICAL_COLS:
            choices = {
                "protocol_type": ["tcp", "udp", "icmp"],
                "service": ["http", "ftp", "smtp", "ssh", "dns"],
                "flag": ["SF", "S0", "REJ", "RSTO", "SH"],
            }
            data[col] = rng.choice(choices[col], size=n_samples)
        else:
            data[col] = rng.uniform(0, 100, size=n_samples).round(4)
    # Binary labels: 60% normal, 40% attack
    labels = rng.choice(["normal", "neptune", "smurf", "ipsweep"],
                        size=n_samples, p=[0.6, 0.2, 0.1, 0.1])
    data["label"] = labels
    data["difficulty_level"] = rng.integers(1, 21, size=n_samples)
    return pd.DataFrame(data)


if __name__ == "__main__":
    X_train, X_test, y_train, y_test, features, scaler, encoders = load_and_preprocess()
    print(f"Features ({len(features)}): {features[:5]} ...")
