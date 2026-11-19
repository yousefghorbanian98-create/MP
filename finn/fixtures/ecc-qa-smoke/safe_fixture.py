"""Synthetic comparison only; not a production payment implementation."""
def approve(*, role, can_review, bank_match, already_approved=False):
    if role != "super_admin" and not (role == "admin" and can_review):
        return "forbidden"
    if not bank_match:
        return "unmatched"
    return "already_approved" if already_approved else "approved"
