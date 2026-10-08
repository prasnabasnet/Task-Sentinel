import re
from playwright.sync_api import Page, expect


def test_login_and_navigate_to_projects(page: Page, frontend_base_url):
    """
    E2E Test:
    1. Opens React login page.
    2. Fills credentials and logs in.
    3. Verifies redirection to dashboard.
    """
    page.goto(f"{frontend_base_url}/login")
    page.fill('input[type="email"]', "super@example.com")
    page.fill('input[type="password"]', "super@123")
    page.click('button[type="submit"]')

    # Wait for React Router navigation away from /login
    expect(page).not_to_have_url(re.compile(r".*/login$"), timeout=20000)
    expect(page.locator("body")).not_to_contain_text("Invalid credentials")


def test_verify_project_board_renders(page: Page, frontend_base_url):
    """
    E2E Test:
    Logs in and checks that navigation / headers render.
    """
    page.goto(f"{frontend_base_url}/login")
    page.fill('input[type="email"]', "super@example.com")
    page.fill('input[type="password"]', "super@123")
    page.click('button[type="submit"]')

    expect(page).not_to_have_url(re.compile(r".*/login$"), timeout=20000)

    main_heading = page.locator("h1, h2").first
    expect(main_heading).to_be_visible(timeout=10000)


def test_navigate_to_kanban_board_and_verify_columns(page: Page, frontend_base_url):
    """
    E2E Test:
    1. Logs in.
    2. Navigates to project 1 board.
    3. Waits for Neon DB fetch ('Loading board...') to finish.
    4. Verifies Kanban columns render.
    """
    page.goto(f"{frontend_base_url}/login")
    page.fill('input[type="email"]', "super@example.com")
    page.fill('input[type="password"]', "super@123")
    page.click('button[type="submit"]')

    expect(page).not_to_have_url(re.compile(r".*/login$"), timeout=20000)

    # Navigate to project 1 board
    page.goto(f"{frontend_base_url}/projects/1/board")

    # Explicitly wait for 'Loading board…' to disappear (giving remote Neon DB up to 30s) [1]
    expect(page.locator("text=Loading board…")).not_to_be_visible(timeout=30000)

    # Verify Kanban columns exist on screen
    expect(page.locator("body")).to_contain_text("To Do", timeout=20000)
    expect(page.locator("body")).to_contain_text("In Progress")
    expect(page.locator("body")).to_contain_text("Done")


def test_create_task_modal_flow(page: Page, frontend_base_url):
    """
    E2E Test:
    1. Opens the Kanban board.
    2. Opens the 'Add task' / 'Create issue' modal.
    3. Fills in task details and submits.
    4. Verifies the card appears on the board.
    """
    page.goto(f"{frontend_base_url}/login")
    page.fill('input[type="email"]', "super@example.com")
    page.fill('input[type="password"]', "super@123")
    page.click('button[type="submit"]')

    page.goto(f"{frontend_base_url}/projects/1/board")

    # Wait for loading to finish
    loading_indicator = page.locator("text=Loading board…")
    if loading_indicator.is_visible():
        expect(loading_indicator).not_to_be_visible(timeout=25000)

    # Look for button to add task
    add_btn = page.locator('button:has-text("Create issue"), button:has-text("Add task"), button:has-text("Create")').first
    if add_btn.is_visible(timeout=10000):
        add_btn.click()

        unique_title = f"Automated E2E Task {re.sub(r'[^0-9]', '', str(page.url))}"
        page.fill('input[name="title"], input[placeholder*="title" i]', unique_title)
        
        page.click('button[type="submit"]:has-text("Create"), button:has-text("Save")')

        expect(page.locator("body")).to_contain_text(unique_title, timeout=20000)

def test_shift_task_status_to_done(page: Page, frontend_base_url):
    """
    E2E Test to reproduce and catch the status shift defect:
    Explicitly waits for the remote Neon DB API fetch to complete.
    """
    # 1. Log in
    page.goto(f"{frontend_base_url}/login")
    page.fill('input[type="email"]', "super@example.com")
    page.fill('input[type="password"]', "super@123")
    page.click('button[type="submit"]')
    expect(page).not_to_have_url(re.compile(r".*/login$"), timeout=20000)

    # 2. Navigate to project board and WAIT for the tasks API to respond (up to 35s for Neon DB)
    with page.expect_response(re.compile(r".*/api/tasks/.*"), timeout=35000):
        page.goto(f"{frontend_base_url}/projects/1/board")

    # 3. Wait for the task card to be attached and visible on the DOM
    task_card = page.locator('text="Task status remains TODO instead of DONE"').first
    if not task_card.is_visible():
        task_card = page.locator('.task-card, [draggable="true"]').first

    # Give the board 15s to render the card after the network data arrives
    expect(task_card).to_be_visible(timeout=15000)
    task_card.click()

    # 4. In the modal, locate the status selector and select 'Done'
    status_select = page.locator('select[name="status"], select:has-text("To Do")').first
    expect(status_select).to_be_visible(timeout=10000)

    # 5. Intercept the PATCH request and catch the HTTP 500 error!
    with page.expect_response(re.compile(r".*/api/tasks/\d+/.*"), timeout=20000) as response_info:
        status_select.select_option(label="Done")

    response = response_info.value
    assert response.status == 200, (
        f"Status shift failed! Expected HTTP 200 but received HTTP {response.status}: {response.text()}"
    )