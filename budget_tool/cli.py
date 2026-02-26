from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from budget_tool.categorizer import categorize_transactions
from budget_tool.config import load_yaml
from budget_tool.importer import normalize_transactions, save_parquet
from budget_tool.reporting import build_monthly_report, export_report


def cmd_import(args: argparse.Namespace) -> None:
    config = load_yaml(args.config)
    df = normalize_transactions(args.csv, config)
    out = Path(args.out)
    save_parquet(df, out)
    print(f"Normalized parquet written to: {out}")


def cmd_categorize(args: argparse.Namespace) -> None:
    categories = load_yaml(args.categories)
    rules = load_yaml(args.rules)
    df = pd.read_parquet(args.input)
    out_df = categorize_transactions(df, categories, rules)
    out = Path(args.out)
    save_parquet(out_df, out)
    print(f"Categorized parquet written to: {out}")


def cmd_report(args: argparse.Namespace) -> None:
    df = pd.read_parquet(args.input)
    report = build_monthly_report(df, args.month)
    excel, html = export_report(report, args.month, args.out)
    print(f"Excel report: {excel}")
    print(f"HTML report: {html}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="budget", description="Budget analysis tool")
    sub = parser.add_subparsers(dest="command", required=True)

    p_import = sub.add_parser("import", help="Import CSV and normalize to parquet")
    p_import.add_argument("--csv", required=True, help="Path to CSV file")
    p_import.add_argument("--config", required=True, help="Path to import config YAML")
    p_import.add_argument("--out", default="normalized.parquet", help="Output parquet path")
    p_import.set_defaults(func=cmd_import)

    p_cat = sub.add_parser("categorize", help="Categorize normalized parquet")
    p_cat.add_argument("--in", dest="input", required=True, help="Input normalized parquet")
    p_cat.add_argument("--rules", required=True, help="Path to rules YAML")
    p_cat.add_argument("--categories", default="categories.yml", help="Path to categories YAML")
    p_cat.add_argument("--out", default="categorized.parquet", help="Output categorized parquet")
    p_cat.set_defaults(func=cmd_categorize)

    p_rep = sub.add_parser("report", help="Generate monthly report")
    p_rep.add_argument("--month", required=True, help="Month in YYYY-MM")
    p_rep.add_argument("--in", dest="input", required=True, help="Input categorized parquet")
    p_rep.add_argument("--out", default="reports", help="Output report directory")
    p_rep.set_defaults(func=cmd_report)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
