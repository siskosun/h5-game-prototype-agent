async function activate(locator, inputMode) {
  if (inputMode === "touch") await locator.tap();
  else if (inputMode === "keyboard") {
    await locator.focus();
    await locator.press("Enter");
  } else await locator.click();
}

export async function runPlayerPath(page, inputMode = "mouse") {
  await activate(page.locator('[data-qa="start"]'), inputMode);
  await page.waitForTimeout(1000);
  await activate(page.locator('[data-qa="action"]'), inputMode);
  await page.waitForTimeout(1000);
  await activate(page.locator('[data-qa="action"]'), inputMode);
  await page.waitForTimeout(1000);
  await activate(page.locator('[data-qa="action"]'), inputMode);
}
