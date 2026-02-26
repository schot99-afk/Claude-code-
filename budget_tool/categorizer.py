from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pandas as pd

ALLOWED_FALLBACK = "Ongecategoriseerd"


class CategorizationError(ValueError):
    """Raised on invalid categorization configs."""


@dataclass(frozen=True)
class PatternRule:
    category: str
    type: str
    value: str
    field: str = "description"


def parse_allowed_categories(categories_config: dict[str, Any]) -> set[str]:
    categories = categories_config.get("categories")
    if not isinstance(categories, list) or not categories:
        raise CategorizationError("categories.yml must contain non-empty 'categories' list")

    allowed = set()
    for item in categories:
        name = item.get("name") if isinstance(item, dict) else None
        if not name:
            raise CategorizationError("Each category entry must contain 'name'")
        allowed.add(name)

    if ALLOWED_FALLBACK not in allowed:
        raise CategorizationError(f"'{ALLOWED_FALLBACK}' must be defined in categories.yml")
    return allowed


def parse_rules(rules_config: dict[str, Any], allowed_categories: set[str]) -> tuple[dict[str, str], list[PatternRule]]:
    overrides = rules_config.get("overrides", {}) or {}
    if not isinstance(overrides, dict):
        raise CategorizationError("rules.yml 'overrides' must be a mapping")

    for tx_id, cat in overrides.items():
        if cat not in allowed_categories:
            raise CategorizationError(f"Override category '{cat}' for tx_id '{tx_id}' not in categories.yml")

    pattern_rules_raw = rules_config.get("pattern_rules", []) or []
    if not isinstance(pattern_rules_raw, list):
        raise CategorizationError("rules.yml 'pattern_rules' must be a list")

    pattern_rules: list[PatternRule] = []
    for idx, item in enumerate(pattern_rules_raw):
        if not isinstance(item, dict):
            raise CategorizationError(f"pattern_rules[{idx}] must be a mapping")
        category = item.get("category")
        rule_type = item.get("type")
        value = item.get("value")
        field = item.get("field", "description")
        if category not in allowed_categories:
            raise CategorizationError(f"Pattern rule category '{category}' not in categories.yml")
        if rule_type not in {"keyword", "regex"}:
            raise CategorizationError("Pattern rule type must be 'keyword' or 'regex'")
        if not isinstance(value, str) or not value.strip():
            raise CategorizationError("Pattern rule value must be non-empty string")
        if field not in {"description", "account"}:
            raise CategorizationError("Pattern rule field must be 'description' or 'account'")
        pattern_rules.append(PatternRule(category=category, type=rule_type, value=value, field=field))

    return overrides, pattern_rules


def categorize_transactions(
    df: pd.DataFrame,
    categories_config: dict[str, Any],
    rules_config: dict[str, Any],
) -> pd.DataFrame:
    allowed_categories = parse_allowed_categories(categories_config)
    overrides, pattern_rules = parse_rules(rules_config, allowed_categories)

    out = df.copy()
    out["category"] = ALLOWED_FALLBACK

    for idx, row in out.iterrows():
        tx_id = row["tx_id"]
        if tx_id in overrides:
            out.at[idx, "category"] = overrides[tx_id]
            continue

        desc = str(row.get("description", ""))
        account = str(row.get("account", ""))
        for rule in pattern_rules:
            target = desc if rule.field == "description" else account
            if rule.type == "keyword" and rule.value.lower() in target.lower():
                out.at[idx, "category"] = rule.category
                break
            if rule.type == "regex" and re.search(rule.value, target, flags=re.IGNORECASE):
                out.at[idx, "category"] = rule.category
                break

    return out
