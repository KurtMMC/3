"""
run_evaluation.py — Full Evaluation Pipeline Runner

Executes the complete Section 3.6 evaluation in order:
  Step 1: Generate 50 paired terrain samples (extract_data.py)
  Step 2: Compute structural and performance metrics (evaluate_metrics.py)
  Step 3: Generate publication-ready figures (plot_metrics.py)

Usage:
    python run_evaluation.py
"""

import os
import subprocess
import sys
import time
from pathlib import Path


def run_step(label: str, script: str, capture_output: bool = False):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    start = time.time()

    # Force UTF-8 for child processes on Windows
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    if capture_output:
        result = subprocess.run(
            [sys.executable, script],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    else:
        result = subprocess.run(
            [sys.executable, script],
            cwd=Path(__file__).parent,
            env=env
        )

    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n[FAILED] {script} exited with code {result.returncode}")
        sys.exit(result.returncode)

    print(f"\n[DONE] Completed in {elapsed:.1f}s")
    return result.stdout if capture_output else ""


if __name__ == "__main__":
    total_start = time.time()
    report_path = Path("output/validation_samples/metrics_evaluation_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write("# System Evaluation Report (Section 3.6, 3.7, 3.8)\n\n")
        report_file.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Step 1: Data Generation
        run_step("Step 1/4 — Generating 50 paired terrain samples", "extract_data.py")
        report_file.write("## Step 1: Data Generation\nStatus: Success (50 samples generated)\n\n")

        # Step 2: Core Metrics
        out2 = run_step("Step 2/4 — Computing evaluation metrics", "evaluate_metrics.py", capture_output=True)
        report_file.write("## Step 2: Algorithmic and Structural Metrics (Section 3.6)\n")
        report_file.write("```text\n" + out2 + "```\n\n")

        # Step 3: Figures
        run_step("Step 3/4 — Generating figures", "plot_metrics.py")
        report_file.write("## Step 3: Visual Validation\nStatus: Figures saved to `output/validation_samples/graphs/`\n\n")

        # Step 4: Benchmark Framework
        out4 = run_step("Step 4/4 — Benchmarking framework (3.7 / 3.8)", "benchmark_framework.py", capture_output=True)
        report_file.write("## Step 4: Benchmarking and Statistical Validation (Section 3.7 & 3.8)\n")
        report_file.write("```text\n" + out4 + "```\n\n")

    total = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"  All steps complete in {total:.1f}s")
    print(f"  Full report saved to: {report_path}")
    print(f"  Figures saved to: output/validation_samples/graphs/")
    print(f"{'='*60}\n")
