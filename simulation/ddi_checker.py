from db.queries import check_ddi


def run_ddi_check(drug_ids: list[str]) -> tuple[bool, str]:
    if len(drug_ids) < 2:
        return False, ""

    rows = check_ddi(drug_ids)
    for severity, direction, mechanism, drug_a, drug_b in rows:
        if severity in ("contraindicated", "major"):
            return True, f"{drug_a} + {drug_b}: {mechanism}"

    return False, ""
