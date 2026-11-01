# Progress – Ahmed (AhmedWilly)

## Done
- Repo set up, teammates invited.
- Notebook TODOs 1–4: train/test split with `random_split` (seed 42), train/test loaders, `CrossEntropyLoss`, Adam optimizer; runs on CUDA if available.
- Added an experiments section: `run_experiment(train_frac, optimizer_name, epochs)` – 2 splits × 2 optimizers, 3 epochs each, lr 1e-3, batch 32.
- Ran the full notebook on the RTX 2060 (~5.5 min per experiment). Results are in `results/*.json`.

| Run | n_train | n_test | Test acc (epoch 3) | Test loss (epoch 3) |
|---|---|---|---|---|
| split80_adam | 9998 | 2500 | 0.985 | 0.046 |
| split80_sgd  | 9998 | 2500 | 0.985 | 0.049 |
| split50_adam | 6249 | 6249 | 0.979 | 0.056 |
| split50_sgd  | 6249 | 6249 | 0.979 | 0.056 |

Baseline cell (80/20, Adam, 1 epoch): train acc 0.943, test acc 0.984.

- Added Mohamed Gomaa's code to the notebook (TODO 5 and 6): `metrics_utils` import, train/test metrics printed after
  the baseline training and evaluation, and the "Metrics table and graphs" cell (table + 4 graphs from `results/*.json`).
- Re-ran the notebook top to bottom on the GPU, skipping the experiments cell (its outputs are from the original run),
  so `results/*.json` are unchanged and the table matches `report/part2_classifier.md`.
  Baseline: Train — acc 0.943, F1 0.943 | Test — acc 0.984, precision 0.985, recall 0.982, F1 0.984, ROC-AUC 0.998.

## Decisions
- Same seed for every run → same split and same initial weights, so only split size / optimizer differ.
- SGD uses momentum 0.9 (plain SGD at lr 1e-3 would be much slower to converge).
- 3 epochs per run: accuracy is already ~98% after epoch 1, more epochs add little.

## Observations for the report
- 50/50 is ~0.6 pp worse than 80/20: fewer training images (6249 vs 9998). The 50/50 test set is larger, so its estimate is more reliable (less variance).
- Adam vs SGD (momentum) end up the same: only the final linear layer (1026 params) is trained on strong pretrained features, so the problem is easy and convex-like. Adam is slightly faster in epoch 1 on 80/20; on 50/50 SGD starts better (train loss 0.193 vs 0.224).
- Test accuracy > train accuracy: train acc is averaged while the model is still learning during the epoch, test acc is measured after the epoch.

## Next steps
- Export the notebook with outputs to PDF for the report appendix and send it to Ahmed Abdelrazek.
- Send my matriculation number to Ahmed Abdelrazek for the front page; review the final PDF draft.
- Optional: a third split (90/10) or third optimizer (RMSprop) – only if there is time, and then Mohamed Gomaa must regenerate the table and figures.

## Blockers / questions for the team
- None. Part 2 (notebook + `report/part2_classifier.md`) is complete; Ahmed Abdelrazek can start Part 1, the final PDF and the slides.
