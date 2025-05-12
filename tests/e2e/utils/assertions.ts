/**
 * Assertion helpers for Playwright tests
 */
import { Page, expect } from '@playwright/test';
import { TabId, isTabEnabled } from './navigation';

/**
 * Checks if lyrics have been successfully loaded
 */
export async function expectLyricsToBeLoaded(page: Page): Promise<void> {
  // Check if the lyrics textarea has content
  const textArea = page.locator('.lyric-input-tab .lyric-editor-textarea');
  await expect(textArea).not.toHaveValue('');
}

/**
 * Checks if song info (artist and title) has been loaded
 */
export async function expectSongInfoToBeLoaded(page: Page, artist: string, title: string): Promise<void> {
  await expect(page.locator('[name="artist"]')).toHaveValue(artist);
  await expect(page.locator('[name="title"]')).toHaveValue(title);
}

/**
 * Verifies that a success message is displayed in a specific tab
 */
export async function expectSuccessMessage(page: Page, tabSelector: string): Promise<void> {
  await expect(page.locator(`${tabSelector} .message.is-success`)).toBeVisible();
}

/**
 * Verifies that an error message is displayed in a specific tab
 */
export async function expectErrorMessage(page: Page, tabSelector: string): Promise<void> {
  await expect(page.locator(`${tabSelector} .message.is-danger`)).toBeVisible();
}

/**
 * Verifies that timings have been created by checking if the Submit tab is enabled
 */
export async function expectTimingsToBeCreated(page: Page): Promise<void> {
  expect(await isTabEnabled(page, TabId.Submit)).toBeTruthy();
}

/**
 * Verifies that a specific number of lyric segments have been created
 */
export async function expectLyricSegmentsCount(page: Page, count: number): Promise<void> {
  // This will need to be adjusted based on how segments are represented in the UI
  const segments = page.locator('.timing-adjustment-tab .segment');
  await expect(segments).toHaveCount(count);
}

/**
 * Verifies that a download event occurs and returns the downloaded file path
 */
export async function expectFileDownload(page: Page, timeoutMs: number = 60000): Promise<string> {
  const downloadPromise = page.waitForEvent('download', { timeout: timeoutMs });
  const download = await downloadPromise;
  const filePath = await download.path();

  expect(filePath).not.toBeNull();
  return filePath as string;
}

/**
 * Verifies that a specific form input has a value
 */
export async function expectInputToHaveValue(page: Page, selector: string, value: string): Promise<void> {
  await expect(page.locator(selector)).toHaveValue(value);
}

/**
 * Verifies that the video preview is visible and loaded
 */
export async function expectVideoPreviewToBeLoaded(page: Page): Promise<void> {
  const videoPreview = page.locator('.video-preview-tab video');
  await expect(videoPreview).toBeVisible();

  // Check if video has loaded by verifying it has a valid duration
  const hasDuration = await videoPreview.evaluate((el: HTMLVideoElement) => {
    return el.duration > 0 && !isNaN(el.duration);
  });

  expect(hasDuration).toBeTruthy();
}

/**
 * Checks that the timing segment at the given index has expected start and end times
 */
export async function expectSegmentTimingsToBe(
  page: Page,
  segmentIndex: number,
  expectedStartTime: number,
  expectedEndTime: number,
  tolerance: number = 0.1
): Promise<void> {
  const timingData = await page.evaluate((index) => {
    // Access the Vue app instance
    // @ts-ignore
    const appElement = document.querySelector('.wrapper');
    if (!appElement) {
      throw new Error('App element not found');
    }

    // Get the Vue component instance using __vue__ property
    // @ts-ignore
    const app = appElement.__vue__;
    if (!app) {
      throw new Error('Vue app instance not found');
    }

    // Get timings directly from App.vue data
    const timings = app.timings;
    if (!timings) {
      throw new Error('Timings not found in App component');
    }

    // Process the timings to extract segment information
    const processedTimings = [];
    let currentSegmentIndex = 0;
    let currentSegment = { startTime: 0, endTime: 0 };

    for (let i = 0; i < timings.length; i++) {
      const [time, marker] = timings[i];
      if (marker === 1) { // Start marker
        if (i > 0 && currentSegment.startTime > 0) {
          processedTimings.push(currentSegment);
          currentSegmentIndex++;
        }
        currentSegment = { startTime: time, endTime: 0 };
      } else if (marker === 2) { // End marker
        currentSegment.endTime = time;
      }
    }

    // Add the last segment if it exists
    if (currentSegment.startTime > 0) {
      processedTimings.push(currentSegment);
    }

    return index < processedTimings.length ? processedTimings[index] : null;
  }, segmentIndex);

  expect(timingData).not.toBeNull();
  expect(Math.abs(timingData.startTime - expectedStartTime)).toBeLessThanOrEqual(tolerance);
  expect(Math.abs(timingData.endTime - expectedEndTime)).toBeLessThanOrEqual(tolerance);
}
