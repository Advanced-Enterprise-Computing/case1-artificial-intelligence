"""Metrics, table and graphs for Part 2 (Cat vs Dog classifier).

Everything is computed from the experiment files in results/*.json (format: see PROJECT.md),
so this needs neither PyTorch nor the dataset - only numpy, pandas, scikit-learn and matplotlib.
Labels: 0 = Cat, 1 = Dog. Dog is the "positive" class for precision, recall, F1 and ROC.

In the notebook (working directory = notebooks/):

    import sys
    sys.path.append("../src")
    import metrics_utils as mu

    results = mu.load_results()           # or the `results` dict from the experiments cell
    mu.metrics_table(results)             # table: final test metrics per run
    mu.plot_history(results)              # graph: accuracy / loss after every epoch
    mu.plot_confusion_matrices(results)   # graph: which images are misclassified
    mu.plot_accuracy_ci(results)          # graph: test accuracy with 95% confidence interval
    mu.plot_roc_curves(results)           # graph: ROC curves

Every plot function also takes save_to="some/file.png" to save the figure, e.g. for the report.
Quick check from the terminal: python src/metrics_utils.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score, roc_curve)

# results/ sits next to src/, so this works no matter where the notebook is started from
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

CAT, DOG = 0, 1  # Dog is the positive class

# colour = train/test split, marker + line style = optimizer, so both experiment factors stay readable
SPLIT_COLORS = {0.8: "#2a78d6", 0.5: "#eb6834"}  # blue, orange: a colour-blind safe pair
EXTRA_COLOR = "#1baf7a"                          # aqua, for any additional split (e.g. 90/10)
OPTIMIZER_STYLES = {"Adam": ("o", "-"), "SGD": ("s", "--")}
BLUES = LinearSegmentedColormap.from_list("blues", ["#cde2fb", "#6da7ec", "#2a78d6", "#184f95", "#0d366b"])

# quiet, consistent look; only applied inside the plot functions below (the notebook style stays untouched)
STYLE = {
    "axes.facecolor": "#fcfcfb", "axes.edgecolor": "#c3c2b7", "axes.grid": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 11, "axes.titlecolor": "#0b0b0b", "axes.labelcolor": "#52514e",
    "grid.color": "#e1e0d9", "grid.linewidth": 0.8,
    "xtick.color": "#c3c2b7", "ytick.color": "#c3c2b7",
    "xtick.labelcolor": "#52514e", "ytick.labelcolor": "#52514e",
    "legend.frameon": False, "lines.linewidth": 2, "lines.markersize": 6,
}


# ---------- loading ----------

def load_results(results_dir=RESULTS_DIR):
    """Read every results/*.json -> list of runs (80/20 before 50/50, Adam before SGD)."""
    return _as_list([json.loads(p.read_text(encoding="utf-8")) for p in Path(results_dir).glob("*.json")])


def _as_list(results):
    # accept the list from load_results() or the {run_name: run} dict built in the notebook
    runs = list(results.values()) if isinstance(results, dict) else list(results)
    return sorted(runs, key=lambda r: (-r["train_frac"], r["optimizer"]))


def run_label(r):
    """Short name of a run, e.g. "80/20 Adam"."""
    train = round(r["train_frac"] * 100)
    return f"{train}/{100 - train} {r['optimizer']}"


# ---------- metrics ----------

def compute_metrics(y_true, y_pred, y_prob=None):
    """Accuracy, precision, recall, specificity and F1 (+ ROC-AUC when P(Dog) is given)."""
    m = {
        "accuracy": accuracy_score(y_true, y_pred),                                    # share of all images right
        "precision": precision_score(y_true, y_pred, pos_label=DOG, zero_division=0),  # predicted dogs that are dogs
        "recall": recall_score(y_true, y_pred, pos_label=DOG, zero_division=0),        # dogs that were found
        "specificity": recall_score(y_true, y_pred, pos_label=CAT, zero_division=0),   # cats that were found
        "f1": f1_score(y_true, y_pred, pos_label=DOG, zero_division=0),                # balance of precision and recall
    }
    if y_prob is not None:
        m["roc_auc"] = roc_auc_score(y_true, y_prob)  # how well P(Dog) ranks dogs above cats, at any threshold
    return {name: float(value) for name, value in m.items()}


def print_metrics(y_true, y_pred, y_prob=None, title=""):
    """Print all metrics on one line, e.g. print_metrics(train_true, train_pred, title="Train")."""
    text = ", ".join(f"{name}: {value:.3f}" for name, value in compute_metrics(y_true, y_pred, y_prob).items())
    print(f"{title} — {text}" if title else text)


def _ci95(p, n):
    # half-width of the 95% confidence interval of an accuracy measured on n images (normal approximation)
    return 1.96 * np.sqrt(p * (1 - p) / n)


def metrics_table(results):
    """Table: final metrics of every run, one row per run."""
    rows = []
    for r in _as_list(results):
        y_true, y_pred, y_prob = r["test"]["y_true"], r["test"]["y_pred"], r["test"]["y_prob"]
        m = compute_metrics(y_true, y_pred, y_prob)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[CAT, DOG]).ravel()
        rows.append({
            "Run": run_label(r),
            "Train imgs": r["n_train"],
            "Test imgs": r["n_test"],
            "Train acc": r["history"][-1]["train_acc"],
            "Test acc": m["accuracy"],
            "± 95% CI": _ci95(m["accuracy"], len(y_true)),
            "Precision": m["precision"],
            "Recall": m["recall"],
            "Specificity": m["specificity"],
            "F1": m["f1"],
            "ROC-AUC": m["roc_auc"],
            "Test loss": r["history"][-1]["test_loss"],
            "FP (cat→dog)": int(fp),
            "FN (dog→cat)": int(fn),
            "Time (s)": r["train_time_sec"],
        })
    return pd.DataFrame(rows).set_index("Run").round(4)


# ---------- graphs ----------

def _style(r):
    color = SPLIT_COLORS.get(r["train_frac"], EXTRA_COLOR)
    marker, linestyle = OPTIMIZER_STYLES.get(r["optimizer"], ("^", ":"))
    return {"color": color, "marker": marker, "linestyle": linestyle}


def _finish(fig, save_to):
    # optionally save as PNG (e.g. for the report), then show
    if save_to:
        Path(save_to).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_to, dpi=200, bbox_inches="tight")
    plt.show()


def plot_history(results, save_to=None):
    """Graph: train/test accuracy and loss after every epoch, one line per run.
    Each row shares its y-axis, so train and test can be compared directly."""
    runs = _as_list(results)
    epochs = sorted({h["epoch"] for r in runs for h in r["history"]})
    panels = [("train_acc", "Train accuracy"), ("test_acc", "Test accuracy"),
              ("train_loss", "Train loss"), ("test_loss", "Test loss")]
    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(2, 2, figsize=(10, 6.5), sharex=True, sharey="row", layout="constrained")
        for ax, (key, title) in zip(axes.flat, panels):
            for r in runs:
                ax.plot([h["epoch"] for h in r["history"]], [h[key] for h in r["history"]],
                        label=run_label(r), **_style(r))
            ax.set_title(title)
            ax.set_xticks(epochs)
        for ax in axes[1]:
            ax.set_xlabel("Epoch")
        fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="outside upper center", ncol=len(runs))
        _finish(fig, save_to)


def plot_confusion_matrices(results, save_to=None):
    """Graph: confusion matrix of every run (rows = split, columns = optimizer).
    Each cell shows the number of images and the share of its true class, so splits of different size compare."""
    runs = _as_list(results)
    splits = sorted({r["train_frac"] for r in runs}, reverse=True)
    optimizers = sorted({r["optimizer"] for r in runs})
    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(len(splits), len(optimizers), squeeze=False, layout="constrained",
                                 figsize=(3.4 * len(optimizers), 3.2 * len(splits)))
        for ax in axes.flat:
            ax.set_visible(False)  # stays hidden if a split/optimizer combination was not run
        for r in runs:
            ax = axes[splits.index(r["train_frac"]), optimizers.index(r["optimizer"])]
            ax.set_visible(True)
            cm = confusion_matrix(r["test"]["y_true"], r["test"]["y_pred"], labels=[CAT, DOG])
            share = cm / cm.sum(axis=1, keepdims=True)  # row = true class, e.g. 0.98 = 98% of the cats called cat
            ax.imshow(share, cmap=BLUES, vmin=0, vmax=1)
            for i in range(2):
                for j in range(2):
                    ax.text(j, i, f"{cm[i, j]}\n{share[i, j]:.1%}", ha="center", va="center",
                            color="white" if share[i, j] > 0.5 else "#0b0b0b")
            ax.set_xticks([0, 1], r["classes"])
            ax.set_yticks([0, 1], r["classes"])
            ax.set_xlabel("Predicted")
            ax.set_ylabel("True")
            ax.set_title(f"{run_label(r)} (test n = {cm.sum()})")
            ax.grid(False)
            ax.spines[:].set_visible(False)
        _finish(fig, save_to)


def plot_accuracy_ci(results, save_to=None):
    """Graph: test accuracy of every run with its 95% confidence interval.
    A bigger test set gives a narrower interval, i.e. a more reliable estimate."""
    runs = _as_list(results)
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(7, 1.2 + 0.7 * len(runs)), layout="constrained")
        for y, r in enumerate(runs):
            y_true, y_pred = r["test"]["y_true"], r["test"]["y_pred"]
            acc = accuracy_score(y_true, y_pred)
            style = _style(r)
            ax.errorbar(acc, y, xerr=_ci95(acc, len(y_true)), fmt=style["marker"], color=style["color"],
                        markersize=8, capsize=4)
            ax.annotate(f"{acc:.3f}", (acc, y), xytext=(0, 9), textcoords="offset points", ha="center",
                        color="#52514e")
        ax.set_yticks(range(len(runs)), [f"{run_label(r)}\n(test n = {r['n_test']})" for r in runs])
        ax.set_ylim(len(runs) - 0.5, -0.5)  # first run on top
        ax.set_xlabel("Test accuracy (dot) and its 95% confidence interval (bar)")
        ax.grid(False, axis="y")
        _finish(fig, save_to)


def plot_roc_curves(results, save_to=None, zoom=(0.1, 0.9)):
    """Graph: ROC curve of every run (true vs. false positive rate for every threshold on P(Dog)).
    All runs are close to perfect, so by default the plot zooms into the top-left corner:
    zoom = (largest false positive rate, smallest true positive rate) shown; zoom=None shows the whole curve."""
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(6, 5), layout="constrained")
        if not zoom:
            ax.plot([0, 1], [0, 1], color="#c3c2b7", linewidth=1, label="Random guess")
        for r in _as_list(results):
            y_true, y_prob = r["test"]["y_true"], r["test"]["y_prob"]
            fpr, tpr, _ = roc_curve(y_true, y_prob, pos_label=DOG)
            style = _style(r)
            ax.plot(fpr, tpr, color=style["color"], linestyle=style["linestyle"],
                    label=f"{run_label(r)} (AUC = {roc_auc_score(y_true, y_prob):.4f})")
        if zoom:
            ax.set_xlim(0, zoom[0])
            ax.set_ylim(zoom[1], 1.002)
        ax.set_xlabel("False positive rate (share of cats called dog)")
        ax.set_ylabel("True positive rate (share of dogs found)")
        ax.set_title("ROC curves" + (" (zoomed into the top-left corner)" if zoom else ""))
        ax.legend(loc="lower right")
        _finish(fig, save_to)


if __name__ == "__main__":
    # quick check from the terminal: python src/metrics_utils.py
    print(metrics_table(load_results()).to_string())
