import { test, expect } from "@playwright/test";

test.describe("ShiftSync End-to-End Lifecycle & Security Verification", () => {
  test("14-Step Complete Handover Lifecycle: Admin Provisioning -> Outgoing Draft & NLP Override -> Refresh Persistence -> Submit -> Explicit Incoming Ack -> Supervisor Oversight", async ({
    page,
  }) => {
    const uniqueSuffix = Date.now().toString().slice(-6);
    const outEmail = `e2e.out.${uniqueSuffix}@shiftsync.ac.ke`;
    const incEmail = `e2e.inc.${uniqueSuffix}@shiftsync.ac.ke`;
    const shiftTitle = `E2E Line Maint Shift ${uniqueSuffix}`;
    const workerPw = "ShiftSync@2026!";

    // 1. Invalid Login Attempt Rejected
    await page.goto("/login");
    await page.getByTestId("login-email-input").fill("admin@shiftsync.ac.ke");
    await page.getByTestId("login-password-input").fill("WrongPassword999!");
    await page.getByTestId("login-submit-button").click();
    await expect(page.getByTestId("login-error")).toBeVisible();

    // 2. Administrator Logs In & Creates Outgoing and Incoming Worker Accounts + Assigns Shift
    await page.getByTestId("demo-admin-btn").click();
    await page.getByTestId("login-submit-button").click();
    await expect(page).toHaveURL(/\/dashboard/);

    // Provision Outgoing Worker
    await page.goto("/admin/users/new");
    await page.getByTestId("user-fullname-input").fill(`E2E Outgoing ${uniqueSuffix}`);
    await page.getByTestId("user-email-input").fill(outEmail);
    await page.getByTestId("user-role-select").selectOption("OUTGOING_WORKER");
    await page.getByTestId("user-department-input").fill("Line Maintenance");
    await page.getByTestId("user-password-input").fill(workerPw);
    await page.getByTestId("save-user-submit-btn").click();
    await expect(page).toHaveURL(/\/admin\/users$/);

    // Provision Incoming Worker
    await page.goto("/admin/users/new");
    await page.getByTestId("user-fullname-input").fill(`E2E Incoming ${uniqueSuffix}`);
    await page.getByTestId("user-email-input").fill(incEmail);
    await page.getByTestId("user-role-select").selectOption("INCOMING_WORKER");
    await page.getByTestId("user-department-input").fill("Line Maintenance");
    await page.getByTestId("user-password-input").fill(workerPw);
    await page.getByTestId("save-user-submit-btn").click();
    await expect(page).toHaveURL(/\/admin\/users$/);

    // Create & Assign Shift
    await page.goto("/admin/shifts/new");
    await page.getByTestId("shift-name-input").fill(shiftTitle);
    await page
      .getByTestId("shift-outgoing-select")
      .selectOption({ label: `E2E Outgoing ${uniqueSuffix} (${outEmail} • Outgoing Worker)` });
    await page
      .getByTestId("shift-incoming-select")
      .selectOption({ label: `E2E Incoming ${uniqueSuffix} (${incEmail} • Incoming Worker)` });
    await page.getByTestId("save-shift-submit-btn").click();
    await expect(page).toHaveURL(/\/shifts$/);

    // Admin Logs Out
    await page.getByTestId("logout-button").click();
    await expect(page).toHaveURL(/\/login$/);

    // 3. Outgoing Worker Logs In
    await page.getByTestId("login-email-input").fill(outEmail);
    await page.getByTestId("login-password-input").fill(workerPw);
    await page.getByTestId("login-submit-button").click();
    await expect(page).toHaveURL(/\/dashboard$/);

    // 4. Outgoing Worker Navigates to Create Handover & Enters Task Description
    await page.goto("/handovers/create");
    await expect(page.getByTestId("handover-incoming-select")).not.toHaveValue("");
    await page
      .getByTestId("task-description-input")
      .fill(
        "Major safety alert: jet fuel seepage detected at engine pylon fuel disconnect coupling; aircraft grounded pending seal swap."
      );

    // 5. Run NLP Categorisation & Priority Detection
    await page.getByTestId("run-nlp-button").click();
    await expect(page.getByTestId("nlp-suggestion-banner")).toBeVisible({ timeout: 20000 });

    // 6. Worker Edits Suggestion (Manual Override on Category) and Adds Task
    await page.getByTestId("task-category-select").selectOption("Maintenance");
    await page.getByTestId("task-priority-select").selectOption("Critical");
    await page.getByTestId("task-status-select").selectOption("Pending");
    await page.getByTestId("add-task-to-handover-btn").click();
    await expect(page.getByTestId("handover-tasks-table")).toContainText(
      "Major safety alert: jet fuel seepage detected"
    );

    // Save Draft in PostgreSQL
    await page.getByTestId("safety-issues-input").fill("Fuel coupling seepage on Bay 2.");
    await page.getByTestId("save-draft-btn").click();
    await expect(page.getByTestId("handover-draft-saved-msg")).toBeVisible();
    await expect(page).toHaveURL(/\/handovers\/[0-9a-f-]+\/edit/);

    // 7. Refreshing the Browser Does Not Erase Saved Draft or Session
    await page.reload();
    await expect(page.getByTestId("handover-tasks-table")).toContainText(
      "Major safety alert: jet fuel seepage detected"
    );

    // 8. Outgoing Worker Reviews & Formally Submits the Handover
    await page.getByTestId("open-review-submit-btn").click();
    await expect(page.getByTestId("pre-submission-review-panel")).toBeVisible();
    await page.getByTestId("confirm-formal-submit-btn").click();
    await expect(page).toHaveURL(/\/handovers\/[0-9a-f-]+$/);
    const handoverUrl = page.url();
    await expect(page.locator("body")).toContainText("Submitted (Awaiting Ack)");

    // Outgoing Worker Logs Out
    await page.getByTestId("logout-button").click();
    await expect(page).toHaveURL(/\/login$/);

    // 9. Incoming Worker Logs In & Opens Submitted Handover
    await page.getByTestId("login-email-input").fill(incEmail);
    await page.getByTestId("login-password-input").fill(workerPw);
    await page.getByTestId("login-submit-button").click();
    await expect(page).toHaveURL(/\/dashboard$/);

    await page.goto(handoverUrl);
    // Merely viewing the handover MUST NOT mark it acknowledged
    await expect(page.locator("body")).toContainText(
      "Awaiting explicit incoming worker acknowledgment"
    );

    // 10. Incoming Worker Proceeds to Explicit Acknowledgment
    await page.getByTestId("goto-acknowledge-page-btn").click();
    await expect(page.getByTestId("explicit-acknowledge-form")).toBeVisible();
    await page
      .getByTestId("ack-notes-input")
      .fill("Formally acknowledged receipt of 5Y-KZE fuel coupling task.");
    await page.getByTestId("confirm-review-checkbox").check();
    await page.getByTestId("submit-explicit-ack-btn").click();

    // 11. Application Records Acknowledgment Identity & Timestamp, and Unfinished Task Remains Pending
    await expect(page).toHaveURL(handoverUrl);
    await expect(page.getByTestId("detail-acknowledged-at")).toContainText(
      `E2E Incoming ${uniqueSuffix}`
    );
    await expect(page.locator("body")).toContainText("Carried Forward");
    await expect(page.locator("body")).toContainText("Pending");

    // Incoming Worker Logs Out
    await page.getByTestId("logout-button").click();
    await expect(page).toHaveURL(/\/login$/);

    // 12. Outgoing Worker Can See the Acknowledgment
    await page.getByTestId("login-email-input").fill(outEmail);
    await page.getByTestId("login-password-input").fill(workerPw);
    await page.getByTestId("login-submit-button").click();
    await expect(page).toHaveURL(/\/dashboard$/);
    await page.goto(handoverUrl);
    await expect(page.getByTestId("detail-acknowledged-at")).toContainText(
      `E2E Incoming ${uniqueSuffix}`
    );
    await page.getByTestId("logout-button").click();
    await expect(page).toHaveURL(/\/login$/);

    // 13. Supervisor Logs In and Sees Handover & Updated Dashboard Metrics
    await page.getByTestId("demo-supervisor-btn").click();
    await page.getByTestId("login-submit-button").click();
    await expect(page).toHaveURL(/\/supervisor\/dashboard$/);
    await expect(page.getByTestId("dashboard-metrics-grid")).toBeVisible();
    await page.goto(`/supervisor/history/${handoverUrl.split("/").pop()}`);
    await expect(page.getByTestId("detail-acknowledged-at")).toContainText(
      `E2E Incoming ${uniqueSuffix}`
    );
  });
});
