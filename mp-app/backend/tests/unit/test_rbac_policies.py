def test_member_and_super_admin_set_feedback_policy() -> None:
    """M39-c3 — شکاف policy: member باید بازخورد خودش را بفرستد؛ super_admin باید در policy باشد."""
    from security.rbac import enforce

    assert enforce("member", "/api/v1/programs/set-feedback", "POST")
    assert enforce("super_admin", "/api/v1/programs/set-feedback", "POST")
    assert not enforce("reception", "/api/v1/programs/set-feedback", "POST")
