import { test, expect } from '@playwright/test';
import path from 'path';
import { promises as fs } from 'fs';

// Test configuration
const testConfig = {
  audioFile: 'my_fair_lady.mp3',
  lyricsFile: 'lyrics.txt',
  timingsFile: 'timings.json',
};

test.describe('Timings File Upload', () => {
  test.beforeEach(async ({ page }) => {
    // Log console messages
    page.on('console', msg => {
      const type = msg.type();
      console.log(`Console ${type}: ${msg.text()}`);
    });

    // Navigate to app
    await page.goto('/');
    await expect(page).toHaveTitle("The Tuul");
  });

  test('Submit tab becomes enabled after uploading timings file', async ({ page }) => {
    const fixturesDir = path.join(test.info().project.testDir, '../fixtures');

    // 1. Navigate to Song Info tab
    await page.click("nav.tabs .song-info-tab-header");
    await expect(page.locator('h2:has-text("Get Your Song Ready")')).toBeVisible();

    // 2. Upload audio file
    const audioFilePath = path.join(fixturesDir, testConfig.audioFile);
    const audioFileInput = page.locator('[name="song-file-upload"] [type="file"]');
    await audioFileInput.setInputFiles(audioFilePath);

    // Wait for metadata to be loaded
    await expect(page.locator('[name="artist"]')).toHaveValue("David Byrne");
    await expect(page.locator('[name="title"]')).toHaveValue("My Fair Lady");

    // 3. Add lyrics
    await page.click("nav.tabs .lyric-input-tab-header");
    await expect(page.locator('h2:has-text("Song Lyrics")')).toBeVisible();

    const lyrics = await fs.readFile(path.join(fixturesDir, testConfig.lyricsFile), 'utf-8');
    await page.locator('.lyric-input-tab .lyric-editor-textarea').pressSequentially(lyrics);

    // 4. Verify Submit tab is initially disabled
    await expect(page.locator('.submit-tab-header')).toHaveClass(/is-disabled/);

    // 5. Click Advanced in Song Info tab to reveal Timings File upload
    await page.click("nav.tabs .song-info-tab-header");
    await page.click("button:has-text('Advanced')");

    // 6. Upload timings file
    const timingsFilePath = path.join(fixturesDir, testConfig.timingsFile);
    const timingsFileInput = page.locator('[name="timings-file-upload"] input[type="file"]');
    await timingsFileInput.setInputFiles(timingsFilePath);

    // 7. Verify Submit tab is now enabled
    await expect(page.locator('.submit-tab-header')).not.toHaveClass(/is-disabled/);

    // 8. Navigate to Submit tab and verify it's accessible
    await page.click("nav.tabs .submit-tab-header");
    await expect(page.locator('button:has-text("Create Video")')).toBeVisible();
  });
});
