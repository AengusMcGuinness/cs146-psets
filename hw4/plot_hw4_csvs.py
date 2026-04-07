#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import List, Optional

repo_dir = Path(__file__).resolve().parent
mpl_dir = repo_dir / ".mplconfig"
mpl_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))
cache_dir = repo_dir / ".cache"
cache_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(cache_dir))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_csv_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path} is empty")
    header = rows[0]
    data = rows[1:]
    return header, data


def parse_float(value: str) -> Optional[float]:
    value = value.strip()
    if value == "" or value.upper() == "NA":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def plot_single_series(path: Path, out_path: Path) -> None:
    header, data = read_csv_rows(path)
    xs: list[float] = []
    ys: list[float] = []
    for row in data:
        if len(row) < 2:
            continue
        x = parse_float(row[0])
        y = parse_float(row[1])
        if x is None or y is None:
            continue
        xs.append(x)
        ys.append(y)

    if not xs:
        raise ValueError(f"{path} does not contain any plottable numeric data")

    fig, ax = plt.subplots(figsize=(9, 6), dpi=144)
    ax.plot(xs, ys, marker="o", linewidth=2.2, color="#1f77b4")
    ax.set_xlabel(header[0])
    ax.set_ylabel(header[1])
    ax.set_title(title_for(path.name))
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_multi_series(path: Path, out_path: Path) -> None:
    header, data = read_csv_rows(path)
    if len(header) < 3:
        raise ValueError(f"{path} must have at least 3 columns for a multi-series plot")

    x_values: list[float] = []
    series: list[list[Optional[float]]] = [[] for _ in header[1:]]

    for row in data:
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        x = parse_float(row[0])
        if x is None:
            continue
        x_values.append(x)
        for i, cell in enumerate(row[1:], start=0):
            series[i].append(parse_float(cell))

    if not x_values:
        raise ValueError(f"{path} does not contain any plottable numeric data")

    fig, ax = plt.subplots(figsize=(9, 6), dpi=144)
    palette = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]

    for idx, ys in enumerate(series):
        numeric_points = [(x, y) for x, y in zip(x_values, ys) if y is not None]
        if not numeric_points:
            continue
        px, py = zip(*numeric_points)
        ax.plot(
            px,
            py,
            marker="o",
            linewidth=2.2,
            color=palette[idx % len(palette)],
            label=header[idx + 1],
        )

    ax.set_xlabel(header[0])
    ax.set_ylabel("Value")
    ax.set_title(title_for(path.name))
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def title_for(file_name: str) -> str:
    if "access_time_vs_assoc" in file_name:
        return "CACTI Access Time vs Associativity"
    if "victim_dm_misses" in file_name:
        return "Victim Cache Sweep with Direct-Mapped L1D"
    if "libquantum_dm_vs_8way" in file_name:
        return "Victim Cache Benefits: libquantum"
    if "hmmer_dm_vs_8way" in file_name:
        return "Victim Cache Benefits: hmmer"
    return Path(file_name).stem


def plot_csv(path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{path.stem}.png"

    header, _ = read_csv_rows(path)
    if len(header) == 2:
        plot_single_series(path, out_path)
    else:
        plot_multi_series(path, out_path)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plot CACTI / victim-cache CSV files with matplotlib."
    )
    parser.add_argument(
        "csv_files",
        nargs="*",
        help="CSV files to plot. If omitted, all CSVs in the current directory are used.",
    )
    parser.add_argument(
        "--output-dir",
        default="plots",
        help="Directory to write PNG files into (default: plots).",
    )
    args = parser.parse_args()

    csv_files = [Path(p) for p in args.csv_files] if args.csv_files else sorted(Path(".").glob("*.csv"))
    if not csv_files:
        raise SystemExit("No CSV files found.")

    output_dir = Path(args.output_dir)

    for csv_path in csv_files:
        if not csv_path.exists():
            print(f"Skipping missing file: {csv_path}")
            continue
        try:
            out_path = plot_csv(csv_path, output_dir)
            print(f"Wrote {out_path}")
        except Exception as exc:
            print(f"Skipping {csv_path}: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
