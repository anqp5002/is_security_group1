"""
utils.py — Shared utility functions for the IDS ML project.

Functions
---------
load_data               Load and concatenate raw CSV files.
plot_confusion_matrix   Plot (and optionally save) a confusion matrix heatmap.
format_alert_log        Format a single Suricata-style alert string.
"""

import os
import glob
import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix as sk_confusion_matrix


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(data_path: str) -> pd.DataFrame:
    """
    Load and concatenate all CSV files found in *data_path*.

    Parameters
    ----------
    data_path : str
        Directory that contains the raw CIC-IDS2017 CSV files.

    Returns
    -------
    pd.DataFrame
        Single concatenated DataFrame with stripped column names.

    Raises
    ------
    FileNotFoundError
        If no CSV files are found in *data_path*.
    """
    csv_files = sorted(glob.glob(os.path.join(data_path, "*.csv")))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {data_path}")

    print(f"Found {len(csv_files)} CSV file(s) in '{data_path}'")
    dfs = []
    for path in csv_files:
        df_temp = pd.read_csv(path, low_memory=False)
        print(f"  Loaded {os.path.basename(path)}: {df_temp.shape[0]:,} rows x {df_temp.shape[1]} cols")
        dfs.append(df_temp)

    df = pd.concat(dfs, ignore_index=True)
    df.columns = df.columns.str.strip()   # remove accidental whitespace
    print(f"Combined: {df.shape[0]:,} rows x {df.shape[1]} columns\n")
    return df


# ---------------------------------------------------------------------------
# Confusion matrix plotting
# ---------------------------------------------------------------------------

def plot_confusion_matrix(
    y_true,
    y_pred,
    class_names,
    title: str = "Confusion Matrix",
    cmap: str = "Blues",
    save_path: str | None = None,
    figsize: tuple = (10, 8),
) -> np.ndarray:
    """
    Plot a labelled confusion matrix heatmap.

    Parameters
    ----------
    y_true : array-like
        Ground-truth labels (encoded integers or strings).
    y_pred : array-like
        Predicted labels (same encoding as y_true).
    class_names : list[str]
        Human-readable class names, ordered to match the encoded indices.
    title : str
        Plot title.
    cmap : str
        Matplotlib/Seaborn colour map (e.g. "Blues", "Greens", "OrRd").
    save_path : str or None
        If given, save the figure to this file path (PNG).
        Parent directories are created automatically.
    figsize : tuple
        Figure size in inches (width, height).

    Returns
    -------
    np.ndarray
        Raw confusion matrix array (rows = actual, cols = predicted).
    """
    cm = sk_confusion_matrix(y_true, y_pred)

    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap=cmap,
        xticklabels=class_names,
        yticklabels=class_names,
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Predicted", fontsize=12)
    ax.set_ylabel("Actual", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Confusion matrix saved to: {save_path}")

    plt.show()
    return cm


# ---------------------------------------------------------------------------
# Alert log formatting
# ---------------------------------------------------------------------------

def format_alert_log(
    label: str,
    dst_port: int | None = None,
    src_ip: str | None = None,
    dst_ip: str | None = None,
    timestamp: str | None = None,
) -> str:
    """
    Format a single Suricata-style IDS alert string.

    Parameters
    ----------
    label : str
        Predicted attack label (e.g. "DDoS", "PortScan", "Bot").
    dst_port : int or None
        Destination port of the flagged flow.
    src_ip : str or None
        Source IP address (optional, for richer logging).
    dst_ip : str or None
        Destination IP address (optional).
    timestamp : str or None
        ISO-format timestamp string. Defaults to *now* if not provided.

    Returns
    -------
    str
        Formatted alert line, e.g.:
        ``[2026-04-27 00:48:34] [ALERT] Suspicious traffic detected: DDoS. Destination Port: 80.``
    """
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    parts = [f"[{timestamp}]", "[ALERT]", f"Suspicious traffic detected: {label}."]

    if dst_port is not None:
        parts.append(f"Destination Port: {int(dst_port)}.")
    if src_ip is not None:
        parts.append(f"Src IP: {src_ip}.")
    if dst_ip is not None:
        parts.append(f"Dst IP: {dst_ip}.")

    return " ".join(parts)
