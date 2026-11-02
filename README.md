# Case 1 – Artificial Intelligence: Machine Learning Applications

Advanced Enterprise Computing: Management of AI, TU Dortmund, WS 2026/27. See `assignment.pdf` for the task and `PROJECT.md` for roles and conventions. The submitted report is in `report/final/`.

## Setup
```bash
git clone https://github.com/Advanced-Enterprise-Computing/case1-artificial-intelligence.git
cd case1-artificial-intelligence
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126   # NVIDIA GPU; CPU only: pip install torch torchvision
pip install -r requirements.txt
```
Then put the dataset at `data/1_Case_AEC/Cat` and `data/1_Case_AEC/Dog` (not in Git).

## Layout
| Path | Content |
|---|---|
| `notebooks/cats_vs_dogs_classifier.ipynb` | Cat vs Dog classifier (Part 2) |
| `src/metrics_utils.py` | Metrics, table and plots |
| `results/` | One JSON per experiment |
| `report/` | Report sections + screenshots |
| `report/final/` | Submitted report (PDF) |
| `tools/report_pdf/` | Scripts that build the report PDF |
| `slides/` | Discussion slides |
| `progress/` | Per-person handoff notes |
