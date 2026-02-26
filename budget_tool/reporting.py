from __future__ import annotations

from pathlib import Path

import pandas as pd


class ReportError(ValueError):
    """Raised when report generation fails due to invalid inputs."""


def build_monthly_report(df: pd.DataFrame, month: str) -> dict[str, pd.DataFrame | float]:
    if not pd.Series([month]).str.match(r"^\d{4}-\d{2}$").all():
        raise ReportError("month must follow YYYY-MM")

    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work[work["date"].dt.strftime("%Y-%m") == month]

    if work.empty:
        income = pd.DataFrame(columns=["category", "total_income"])
        expenses = pd.DataFrame(columns=["category", "total_expenses"])
        top = pd.DataFrame(columns=["description", "total_amount", "count"])
        net = 0.0
    else:
        income = (
            work[work["amount"] > 0]
            .groupby("category", as_index=False)["amount"]
            .sum()
            .rename(columns={"amount": "total_income"})
            .sort_values("total_income", ascending=False)
        )

        expenses = (
            work[work["amount"] < 0]
            .groupby("category", as_index=False)["amount"]
            .sum()
            .assign(total_expenses=lambda d: d["amount"].abs())
            [["category", "total_expenses"]]
            .sort_values("total_expenses", ascending=False)
        )

        top = (
            work.assign(abs_amount=lambda d: d["amount"].abs())
            .groupby("description", as_index=False)
            .agg(total_amount=("abs_amount", "sum"), count=("description", "size"))
            .sort_values(["total_amount", "count"], ascending=[False, False])
            .head(10)
        )

        net = float(work["amount"].sum())

    return {
        "income_by_category": income.reset_index(drop=True),
        "expenses_by_category": expenses.reset_index(drop=True),
        "net_cashflow": net,
        "top_descriptions": top.reset_index(drop=True),
    }


def export_report(report: dict[str, pd.DataFrame | float], month: str, out_dir: str | Path) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    excel_path = out / f"budget_report_{month}.xlsx"
    html_path = out / f"budget_report_{month}.html"

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        pd.DataFrame([{"month": month, "net_cashflow": report["net_cashflow"]}]).to_excel(
            writer, sheet_name="summary", index=False
        )
        report["income_by_category"].to_excel(writer, sheet_name="income", index=False)
        report["expenses_by_category"].to_excel(writer, sheet_name="expenses", index=False)
        report["top_descriptions"].to_excel(writer, sheet_name="top_descriptions", index=False)

    summary_html = pd.DataFrame([{"month": month, "net_cashflow": report["net_cashflow"]}]).to_html(index=False)
    income_html = report["income_by_category"].to_html(index=False)
    expenses_html = report["expenses_by_category"].to_html(index=False)
    top_html = report["top_descriptions"].to_html(index=False)

    html = f"""
    <html>
      <head><title>Budget report {month}</title></head>
      <body>
        <h1>Budget report {month}</h1>
        <h2>Netto cashflow</h2>
        {summary_html}
        <h2>Inkomsten per categorie</h2>
        {income_html}
        <h2>Uitgaven per categorie</h2>
        {expenses_html}
        <h2>Top 10 descriptions/merchants</h2>
        {top_html}
      </body>
    </html>
    """
    html_path.write_text(html, encoding="utf-8")
    return excel_path, html_path
