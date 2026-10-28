import { chromium } from "playwright";
import path from "path";
import fs from "fs";

const ASSETS_DIR = "C:\\Users\\saidm\\OneDrive\\Desktop\\ShiftSync_Manual_Assets";
if (!fs.existsSync(ASSETS_DIR)) {
  fs.mkdirSync(ASSETS_DIR, { recursive: true });
}

async function capture() {
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  console.log("1. Capturing Login Page...");
  await page.goto("http://127.0.0.1:5173/login", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(ASSETS_DIR, "01_login_page.png"), fullPage: true });

  console.log("2. Capturing Sign Up Page...");
  await page.goto("http://127.0.0.1:5173/signup", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(ASSETS_DIR, "02_signup_page.png"), fullPage: true });

  console.log("3. Logging in as Admin...");
  await page.goto("http://127.0.0.1:5173/login", { waitUntil: "networkidle" });
  await page.getByTestId("demo-admin-btn").click();
  await page.waitForTimeout(500);
  await page.getByTestId("login-submit-button").click();
  await page.waitForURL("**/dashboard", { timeout: 15000 });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(ASSETS_DIR, "03_admin_dashboard.png"), fullPage: true });

  console.log("4. Capturing Handovers Management / Status View...");
  await page.goto("http://127.0.0.1:5173/handovers", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(ASSETS_DIR, "04_handovers_list.png"), fullPage: true });

  // Open first handover to view detail/ack
  const firstHandover = page.locator('a[href^="/handovers/"]').first();
  if (await firstHandover.count() > 0) {
    console.log("5. Capturing Handover Detail / Audit View...");
    await firstHandover.click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(ASSETS_DIR, "05_handover_detail.png"), fullPage: true });
  }

  console.log("6. Logging in as Outgoing Worker to capture Handover Creation with NLP...");
  await page.goto("http://127.0.0.1:5173/login", { waitUntil: "networkidle" });
  await page.getByTestId("demo-outgoing-btn").click();
  await page.waitForTimeout(500);
  await page.getByTestId("login-submit-button").click();
  await page.waitForURL("**/dashboard", { timeout: 15000 });
  await page.waitForTimeout(1500);

  await page.goto("http://127.0.0.1:5173/handovers/new", { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  // Fill sample task to demonstrate NLP categorization & priority preview
  try {
    const rawInput = page.locator('textarea').first();
    if (await rawInput.count() > 0) {
      await rawInput.fill("Boeing 787 APU fuel pump inspection completed. Hyd fluid leak identified on right gear, hydraulic pressure test required before pushback.");
      await page.waitForTimeout(1500);
    }
  } catch (e) {
    console.log("Note on input:", e.message);
  }
  await page.screenshot({ path: path.join(ASSETS_DIR, "06_handover_creation_nlp.png"), fullPage: true });

  console.log("7. Logging in as Supervisor for Operations Oversight...");
  await page.goto("http://127.0.0.1:5173/login", { waitUntil: "networkidle" });
  await page.getByTestId("demo-supervisor-btn").click();
  await page.waitForTimeout(500);
  await page.getByTestId("login-submit-button").click();
  await page.waitForURL("**/dashboard", { timeout: 15000 });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(ASSETS_DIR, "07_supervisor_dashboard.png"), fullPage: true });

  await browser.close();
  console.log("All screenshots captured successfully in:", ASSETS_DIR);
}

capture().catch((err) => {
  console.error("Capture failed:", err);
  process.exit(1);
});
