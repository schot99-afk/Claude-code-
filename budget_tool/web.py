from __future__ import annotations

from pathlib import Path

import pandas as pd
from flask import Flask, redirect, render_template, request, send_file, url_for

from budget_tool.categorizer import categorize_transactions
from budget_tool.config import load_yaml
from budget_tool.importer import normalize_transactions, save_parquet
from budget_tool.reporting import build_monthly_report, export_report


def create_app(base_dir: str | Path | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    root = Path(base_dir) if base_dir else Path.cwd()
    data_dir = root / "data"
    reports_dir = root / "reports"

    @app.get("/")
    def home():
        months = []
        categorized_path = root / "categorized.parquet"
        if categorized_path.exists():
            df = pd.read_parquet(categorized_path)
            if not df.empty and "date" in df.columns:
                months = sorted(pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m").dropna().unique())
        return render_template("index.html", months=months)

    @app.post("/run-pipeline")
    def run_pipeline():
        csv_path = request.form.get("csv_path", "data/sample_generic.csv").strip()
        month = request.form.get("month", "").strip()

        normalized = root / "normalized.parquet"
        categorized = root / "categorized.parquet"

        config = load_yaml(root / "import_config.yml")
        categories = load_yaml(root / "categories.yml")
        rules = load_yaml(root / "rules.yml")

        normalized_df = normalize_transactions(root / csv_path, config)
        save_parquet(normalized_df, normalized)

        categorized_df = categorize_transactions(normalized_df, categories, rules)
        save_parquet(categorized_df, categorized)

        if month:
            report = build_monthly_report(categorized_df, month)
            export_report(report, month, reports_dir)

        return redirect(url_for("home"))

    @app.get("/preview/<month>")
    def preview(month: str):
        categorized_path = root / "categorized.parquet"
        if not categorized_path.exists():
            return "Geen categorized.parquet gevonden. Draai eerst de pipeline.", 400

        df = pd.read_parquet(categorized_path)
        report = build_monthly_report(df, month)

        summary = {"month": month, "net_cashflow": report["net_cashflow"]}
        return render_template(
            "preview.html",
            summary=summary,
            income=report["income_by_category"].to_dict(orient="records"),
            expenses=report["expenses_by_category"].to_dict(orient="records"),
            top=report["top_descriptions"].to_dict(orient="records"),
            month=month,
        )

    @app.get("/download/<month>/<fmt>")
    def download(month: str, fmt: str):
        report = reports_dir / f"budget_report_{month}.{fmt}"
        if not report.exists():
            categorized_path = root / "categorized.parquet"
            if not categorized_path.exists():
                return "Geen gecategoriseerde data gevonden.", 400
            df = pd.read_parquet(categorized_path)
            export_report(build_monthly_report(df, month), month, reports_dir)

        if fmt not in {"xlsx", "html"}:
            return "Ongeldig formaat", 400
        return send_file(report, as_attachment=True)

    return app


def main() -> None:
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=False)


if __name__ == "__main__":
    main()
