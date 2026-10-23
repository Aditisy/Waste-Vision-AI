"""Transparent cleanup triage estimate. This is not an official hazard assessment."""

SEVERITY_POINTS = {"Light": 0, "Moderate": 3, "Severe": 7}


def calculate_priority(item_count, categories, overflowing=False, severity="Moderate", sensitive_site=False):
    """Return a level, numeric estimate, and an auditable factor breakdown."""
    severity = severity if severity in SEVERITY_POINTS else "Moderate"
    item_points = min(max(int(item_count), 0), 6)
    variety_points = min(len(set(categories)), 3)
    severity_points = SEVERITY_POINTS[severity]
    overflow_points = 5 if overflowing else 0
    sensitive_points = 5 if sensitive_site else 0
    score = item_points + variety_points + severity_points + overflow_points + sensitive_points
    level = "High" if score >= 15 else "Medium" if score >= 7 else "Low"
    factors = {
        "Detected items": f"{item_points}/6 points",
        "Category variety": f"{variety_points}/3 points",
        "Visible severity": f"{severity} (+{severity_points})",
        "Overflowing or dumped": f"Yes (+{overflow_points})" if overflowing else "No (+0)",
        "Sensitive location": f"Yes (+{sensitive_points})" if sensitive_site else "No (+0)",
    }
    return {"level": level, "score": score, "factors": factors}


def score_priority(item_count, categories, overflowing=False, severity="Moderate", sensitive_site=False):
    """Backwards-compatible helper returning just the priority label."""
    return calculate_priority(item_count, categories, overflowing, severity, sensitive_site)["level"]
