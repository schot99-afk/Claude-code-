from budget_tool.categorizer import categorize_transactions
from budget_tool.importer import normalize_transactions


def test_categorization_and_fallback():
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
            {"name": "Boodschappen"},
            {"name": "Inkomen werk"},
            {"name": "Ongecategoriseerd"},
        ]
    }
    rules = {
        "overrides": {},
        "pattern_rules": [
            {"category": "Boodschappen", "type": "keyword", "value": "groceries"},
            {"category": "Inkomen werk", "type": "regex", "value": "salary|freelance"},
        ],
    }

    out = categorize_transactions(df, categories, rules)

    groceries = out[out["description"].str.contains("groceries", case=False)].iloc[0]
    salary = out[out["description"].str.contains("Salary", case=False)].iloc[0]
    rent = out[out["description"].str.contains("Rent", case=False)].iloc[0]

    assert groceries["category"] == "Boodschappen"
    assert salary["category"] == "Inkomen werk"
    assert rent["category"] == "Ongecategoriseerd"
