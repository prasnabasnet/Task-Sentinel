import requests


def test_unauthenticated_request_is_blocked(api_base_url):
    response = requests.get(f"{api_base_url}/api/tasks/")
    assert response.status_code == 401


def test_create_bug_defect_via_api(api_base_url, auth_headers):

    payload = {
        "project": 1,
        "title": "Automated Defect Test - Button Unclickable",
        "description": "Found via automated regression suite.",
        "status": "TODO",
        "priority": "HIGH",
        "issue_type": "BUG",
        "severity": "CRITICAL",
        "steps_to_reproduce": "1. Navigate to Project Board\n2. Click Create\n3. Observe error",
        "expected_behavior": "Modal should open.",
        "actual_behavior": "Nothing happens.",
        "environment": "Chromium / macOS",
    }

    response = requests.post(
        f"{api_base_url}/api/tasks/",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["issue_type"] == "BUG"
    assert data["severity"] == "CRITICAL"
    assert data["title"] == payload["title"]


def test_export_bug_markdown_report(api_base_url, auth_headers):
    # First, list tasks to find a valid task ID
    list_res = requests.get(f"{api_base_url}/api/tasks/", headers=auth_headers)
    assert list_res.status_code == 200
    tasks = list_res.json()
    task_list = tasks if isinstance(tasks, list) else tasks.get("results", [])

    if not task_list:
        pytest.skip("No tasks available to test export endpoint.")

    task_id = task_list[0]["id"]

    # Call the export-report endpoint
    export_res = requests.get(
        f"{api_base_url}/api/tasks/{task_id}/export-report/",
        headers=auth_headers,
    )

    assert export_res.status_code == 200
    data = export_res.json()
    assert "markdown" in data
    assert f"[BUG-{task_id}]" in data["markdown"]
    assert "Steps to Reproduce" in data["markdown"]