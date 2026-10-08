def test_deliberate_failure_for_qa_sentinel():
    """This test is designed to fail so we can verify the AI Auto-Triage Sentinel."""
    expected_status = "DONE"
    actual_status = "TODO"
    assert actual_status == expected_status, f"Expected task status '{expected_status}', but got '{actual_status}'"