from budget_tool.categorizer import categorize_transactions
from budget_tool.importer import normalize_transactions
from budget_tool.reporting import build_monthly_report


def test_report_numbers_for_january():
    config = {
        "columns": {
            "date": "transaction_date",
            "amount": "amount",
            "description": "description",
            "account": "account",
        },
        "date_format": "%Y-%m-%d",
    }
    df = normalize_transactions("data/sample_generic.csv", config)

    categories = {
        "categories": [
            {"name": "Inkomen werk"},
            {"name": "Inkomen beleggingen"},
            {"name": "Ongecategoriseerd"},
        ]
    }
    rules = {
        "overrides": {},
        "pattern_rules": [
            {"category": "Inkomen werk", "type": "regex", "value": "salary|freelance"},
            {"category": "Inkomen beleggingen", "type": "keyword", "value": "Dividend"},
        ],
    }

    categorized = categorize_transactions(df, categories, rules)
    report = build_monthly_report(categorized, "2024-01")

    january_total = categorized[categorized["date"].str.startswith("2024-01")]["amount"].sum()
    assert round(report["net_cashflow"], 2) == round(float(january_total), 2)
    assert len(report["top_descriptions"]) <= 10
