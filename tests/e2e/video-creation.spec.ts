import { test, expect } from '@playwright/test';
import path from 'path';
import { promises as fs } from 'fs';
import exp from 'constants';
import { time } from 'console';

// Test configuration
const testConfig = {
    audioFile: 'my_fair_lady.mp3',
    lyricsFile: 'lyrics.txt',
    timingsFile: 'timings.json',
};

test.describe('Karaoke Track Creation', () => {
    test.describe.configure({ timeout: 300000 }); // 5 minutes

    test.beforeEach(async ({ page }) => {

        page.on('console', msg => {
            const type = msg.type();
            console.log(`Console ${type}: ${msg.text()}`);
        });
        // Login before each test (assuming authentication is required)
        await page.goto('/');
        await expect(page).toHaveTitle("The Tuul");
    });

    test('Create a complete karaoke track', async ({ page, context }) => {
        const fixturesDir = path.join(test.info().project.testDir, '../fixtures');
        // 1. Navigate to Song Info tab
        await page.click("nav.tabs .song-info-tab-header");
        await expect(page.locator('h2:has-text("Get Your Song Ready")')).toBeVisible();

        // 2. Upload audio file
        const audioFilePath = path.join(fixturesDir, testConfig.audioFile);
        const audioFileInput = page.locator('[name="song-file-upload"] [type="file"]');
        await audioFileInput.setInputFiles(audioFilePath);
        await expect(page.locator('[name="artist"]')).toHaveValue("David Byrne");
        await expect(page.locator('[name="title"]')).toHaveValue("My Fair Lady");

        // 3. Separate track
        // Mock separate_track API call to return a fixture file
        await context.route('**/separate_track', async (route) => {
            // Get the path to the fixture file
            const audioZipPath = path.join(fixturesDir, 'split_song.zip');

            // Read the file contents
            const fileBuffer = await fs.readFile(audioZipPath);

            // Fulfill the request with the file
            await route.fulfill({
                status: 200,
                contentType: 'application/zip',
                body: fileBuffer,
                headers: {
                    'Content-Disposition': 'attachment; filename=audio.zip'
                }
            });

            console.log('Mocked separate_track endpoint with fixture file:', audioZipPath);
        });

        // await page.click('button:has-text("Separate Track")');

        // 4. Add lyrics
        await expect(page.locator('.song-timing-tab-header')).toHaveClass(/is-disabled/);

        const lyrics = await fs.readFile(path.join(fixturesDir, testConfig.lyricsFile), 'utf-8');
        await page.click("nav.tabs .lyric-input-tab-header");
        await expect(page.locator('h2:has-text("Song Lyrics")')).toBeVisible();
        await page.locator('.lyric-input-tab .lyric-editor-textarea').pressSequentially(lyrics);
        // take screenshot
        await page.screenshot({ path: 'lyrics.png' });

        // temp
        await page.click("nav.tabs .song-info-tab-header");

        await expect(page.locator('.song-timing-tab-header')).not.toHaveClass(/is-disabled/);

        // 5. Song timing
        await page.click("nav.tabs .song-timing-tab-header");
        await expect(page.locator('h2:has-text("Song Timing")')).toBeVisible();
        await page.click(".song-timing-tab button[name='song-timing-play-pause']");

        // 6. Mark timing for each lyric line
        // timings is a json array of tuples [startTime, inputtype]
        await expect(page.locator('.submit-tab-header')).toHaveClass(/is-disabled/);

        const timings = JSON.parse(await fs.readFile(path.join(fixturesDir, testConfig.timingsFile), 'utf-8'));
        for (let i = 0; i < timings.length; i++) {
            const timing = timings[i];
            // Wait until we reach the desired time for this lyric
            const delay = (timing[0] - (i === 0 ? 0 : timings[i - 1][0])) * 1000;
            const key = timing[1] === 1 ? 'Space' : 'Enter';

            console.log(`Waiting for ${delay}ms before pressing ${key}`, Date.now());
            if (delay > 0) {
                await page.waitForTimeout(delay);
            }

            // Press spacebar to mark timing for current line
            await page.keyboard.press(key);
            //     // Verify the line was marked (should have a different class or attribute)
            //     await expect(page.locator(`[data-test="lyrics-line-${timing.lineIndex}"]`))
            //         .toHaveAttribute('data-timed', 'true');
        };
        // Stop the timing process
        await page.click(".song-timing-tab button[name='song-timing-play-pause']");
        await expect(page.locator('.song-timing-tab .message.is-success')).toBeVisible();

        // Submit tab
        await expect(page.locator('.submit-tab-header')).not.toHaveClass(/is-disabled/);
        await page.click("nav.tabs .submit-tab-header");
        await expect(page.locator('button:has-text("Create Video")')).toBeVisible();
        await page.click('button:has-text("Create Video")');

        // Wait for video to finish
        const VIDEO_CREATION_TIMEOUT = 180000; // 3 minutes
        const downloadPromise = page.waitForEvent('download', { timeout: VIDEO_CREATION_TIMEOUT });
        const download = await downloadPromise;
        const videoPath = await download.path();
        console.log('Video download path:', videoPath);
        await expect(videoPath).not.toBeNull();
    });
});