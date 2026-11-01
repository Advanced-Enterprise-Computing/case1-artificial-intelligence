# Progress – Mohamed Gomaa (issamfarouk)

## Done
- `src/metrics_utils.py`: metrics, table and graphs, computed only from `results/*.json` (no PyTorch or dataset needed).
  - Metrics: accuracy, precision, recall, specificity, F1, ROC-AUC (Dog = positive class), test loss, 95% confidence interval of the accuracy, error counts.
  - `metrics_table()`: one row per run.
  - Graphs: `plot_history` (accuracy / loss per epoch), `plot_confusion_matrices`, `plot_accuracy_ci`, `plot_roc_curves`.
- Tested on the four result files: the table and all four graphs render correctly.

| Run | Test acc | ± 95% CI | Precision | Recall | Specificity | F1 | ROC-AUC | FP (cat→dog) | FN (dog→cat) |
|---|---|---|---|---|---|---|---|---|---|
| 80/20 Adam | 0.9852 | 0.0047 | 0.9841 | 0.9864 | 0.9840 | 0.9852 | 0.9986 | 20 | 17 |
| 80/20 SGD  | 0.9848 | 0.0048 | 0.9879 | 0.9816 | 0.9880 | 0.9848 | 0.9986 | 15 | 23 |
| 50/50 Adam | 0.9792 | 0.0035 | 0.9870 | 0.9712 | 0.9872 | 0.9791 | 0.9986 | 40 | 90 |
| 50/50 SGD  | 0.9794 | 0.0035 | 0.9848 | 0.9738 | 0.9849 | 0.9793 | 0.9985 | 47 | 82 |

## Decisions
- Dog (label 1) is the positive class, matching `y_prob` = P(Dog) in the results JSON.
- Confusion matrices show the count and the share of each true class, so the 80/20 runs (2500 test images) and the 50/50 runs (6249) can be compared.
- `plot_roc_curves` zooms into the top-left corner by default (`zoom=None` shows the whole curve), because all AUCs are ~0.998.
- Every plot function takes `save_to="..."`, so the report figures come from the same code as the notebook.

## Observations for the report
- The 50/50 runs lose accuracy mainly on dogs: 2.6–2.9% of the dogs are called cats (1.4–1.8% with 80/20). Cats are recognised equally well (~98.5%) with both splits.
- Adam vs SGD: same accuracy. On 80/20, Adam misses fewer dogs (17 vs 23) but calls more cats dogs (20 vs 15).
- ROC-AUC is the same for all runs (0.9985–0.9986): the models rank the images equally well, the differences only show at the 0.5 threshold.
- The 50/50 confidence interval is narrower (±0.35 pp vs ±0.47 pp) because its test set is 2.5× larger. The intervals overlap slightly, so the 80/20 advantage is small.
- A possible extra reason for test acc > train acc: `model.train()` keeps updating the BatchNorm statistics of the frozen backbone, so the backbone's features shift during training and train acc is measured in train mode.

## Next steps
- Write `report/part2_classifier.md`.
- Save the Part 2 figures for the report with `save_to`, once the folder is agreed (see questions).

## Blockers / questions for the team
- Ahmed (AhmedWilly): please add the notebook code below and re-run.
- Ahmed Abdelrazek (AhmedElngar): can the Part 2 figures go into `report/img/` as `part2_*.png`? The folder is yours.

## Code for the notebook (for Ahmed – AhmedWilly)
Based on the notebook in commit `2cd3b51`. Nothing else in the notebook needs to change.

**1. Setup cell** – add at the end:
```python
# our helper module for metrics, table and graphs (src/metrics_utils.py)
import sys
sys.path.append("../src")
import metrics_utils as mu
```

**2. Training cell** (TODO "compute other metrics") – before `for imgs, labels in train_loader:` add:
```python
train_true, train_pred = [], []  # labels and predictions of the whole epoch
```
Inside the loop, right after `preds = logits.argmax(1)`, add:
```python
    train_true += labels.tolist()
    train_pred += preds.tolist()
```
Replace `# TODO: Please compute other metrics and print them` with:
```python
mu.print_metrics(train_true, train_pred, title="Train")
```

**3. Evaluation cell** (TODO "print metrics") – after `total, correct = 0, 0` add:
```python
test_true, test_pred, test_prob = [], [], []  # labels, predictions and P(Dog) of the test split
```
Inside the loop, right after `preds = logits.argmax(1)`, add:
```python
        test_true += labels.tolist()
        test_pred += preds.tolist()
        test_prob += F.softmax(logits, dim=1)[:, 1].tolist()
```
Replace the TODO comment at the end of the cell with:
```python
mu.print_metrics(test_true, test_pred, test_prob, title="Test")
```

**4. Cell "TODO (Mohamed Gomaa)"** under "Metrics table and graphs" – replace its content with:
```python
# table and graphs for all experiments, computed from results/*.json
runs = mu.load_results()
display(mu.metrics_table(runs))
mu.plot_history(runs)
mu.plot_confusion_matrices(runs)
mu.plot_accuracy_ci(runs)
mu.plot_roc_curves(runs)
```

**Re-running:** run the notebook from top to bottom, but skip the experiments cell (`for frac in SPLITS: ...`). The results JSON then stay exactly as analysed above, and cell 4 reads them. If you do re-run the experiments, tell me and I will regenerate the table and figures from the new JSON.
