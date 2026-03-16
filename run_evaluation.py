"""
run_evaluation.py — Full Evaluation Pipeline Runner

Executes the complete Section 3.6 evaluation in order:
  Step 1: Generate 50 paired terrain samples (extract_data.py)
  Step 2: Compute structural and performance metrics (evaluate_metrics.py)
  Step 3: Generate publication-ready figures (plot_metrics.py)

Usage:
    python run_evaluation.py
"""

import subprocess
import sys
import time
from pathlib import Path


def run_step(label: str, script: str):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    start = time.time()

    result = subprocess.run(
        [sys.executable, script],
        cwd=Path(__file__).parent,
    )

    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n[FAILED] {script} exited with code {result.returncode}")
        sys.exit(result.returncode)

    print(f"\n[DONE] Completed in {elapsed:.1f}s")


if __name__ == "__main__":
    total_start = time.time()

    run_step("Step 1/4 — Generating 50 paired terrain samples", "extract_data.py")
    run_step("Step 2/4 — Computing evaluation metrics",         "evaluate_metrics.py")
    run_step("Step 3/4 — Generating figures",                   "plot_metrics.py")
    run_step("Step 4/4 — Benchmarking framework (3.7 / 3.8)",  "benchmark_framework.py")

    total = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"  All steps complete in {total:.1f}s")
    print(f"  Figures saved to: output/validation_samples/graphs/")
    print(f"{'='*60}\n")
