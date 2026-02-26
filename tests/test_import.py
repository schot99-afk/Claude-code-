from budget_tool.importer import normalize_transactions


def test_csv_to_canonical_mapping():
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

    assert list(df.columns) == ["date", "amount", "description", "account", "tx_id"]
    assert df.iloc[0]["date"] == "2024-01-02"
    assert isinstance(df.iloc[0]["amount"], float)
    assert len(df.iloc[0]["tx_id"]) == 64
