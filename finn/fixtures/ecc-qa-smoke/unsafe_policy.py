"""Deliberately unsafe synthetic smoke-test code; never product code."""
def approve(*, role, can_review, bank_match, already_approved=False):
    return "already_approved" if already_approved else "approved"
