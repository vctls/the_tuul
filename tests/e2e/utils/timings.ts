/**
 * Timing helpers for Playwright tests
 */
import { Page, expect } from '@playwright/test';
import { TabId, navigateToTab } from './navigation';
import { loadFixtureJson } from './setupHelpers';

// Define the format of a timing entry
export interface TimingEntry {
  time: number;
  type: 1 | 2; // 1 = Space (start), 2 = Enter (end)
}

/**
 * Toggles playback in the timing tab
 */
export async function togglePlayback(page: Page): Promise<void> {
  if (!await page.locator('.song-timing-tab').isVisible()) {
    await navigateToTab(page, TabId.SongTiming);
  }

  await page.click(".song-timing-tab button[name='song-timing-play-pause']");
}

/**
 * Enters a series of timings based on provided timing data
 * Each timing entry contains a time and a type (1 = Space for start, 2 = Enter for end)
 */
export async function enterTimings(page: Page, timings: TimingEntry[]): Promise<void> {
  if (!await page.locator('.song-timing-tab').isVisible()) {
    await navigateToTab(page, TabId.SongTiming);
  }

  // Start playback
  await togglePlayback(page);

  for (let i = 0; i < timings.length; i++) {
    const timing = timings[i];

    // Calculate delay based on the difference between current and previous timing
    const previousTime = i === 0 ? 0 : timings[i - 1].time;
    const delay = (timing.time - previousTime) * 1000;

    // Determine which key to press based on timing type
    const key = timing.type === 1 ? 'Space' : 'Enter';

    console.log(`Waiting for ${delay}ms before pressing ${key} at time ${timing.time}`);

    if (delay > 0) {
      await page.waitForTimeout(delay);
    }

    // Press the appropriate key
    await page.keyboard.press(key);
  }

  // Stop playback
  await togglePlayback(page);

  // Verify success message is displayed
  await expect(page.locator('.song-timing-tab .message.is-success')).toBeVisible();
}

/**
 * Loads timings from a JSON file and enters them
 * The file should contain an array of [time, type] tuples
 */
export async function loadAndEnterTimings(page: Page, timingsFilename: string): Promise<void> {
  // Load the timings file
  const timingsData = await loadFixtureJson<[number, number][]>(timingsFilename);

  // Convert to TimingEntry format
  const timings: TimingEntry[] = timingsData.map(([time, type]) => ({
    time,
    type: type as 1 | 2
  }));

  // Enter the timings
  await enterTimings(page, timings);
}

/**
 * Adjusts timing for a specific segment by dragging handles
 */
export async function adjustTiming(
  page: Page,
  segmentIndex: number,
  startOffset: number = 0,
  endOffset: number = 0
): Promise<void> {
  if (!await page.locator('.timing-adjustment-tab').isVisible()) {
    await navigateToTab(page, TabId.TimingAdjustment);
  }

  // Get segment handles based on the region-handle classes from OpenEndedRegionPlugin
  const startHandle = page.locator(`[part="region ${segmentIndex}_${segmentIndex}"] [part="region-handle region-handle-left"]`);
  const endHandle = page.locator(`[part="region ${segmentIndex}_${segmentIndex}"] [part="region-handle region-handle-right"]`);

  // Perform drag operations if offsets are non-zero
  if (startOffset !== 0) {
    await startHandle.dragTo(startHandle, {
      force: true,
      targetPosition: { x: startOffset, y: 0 }
    });
  }

  if (endOffset !== 0) {
    await endHandle.dragTo(endHandle, {
      force: true,
      targetPosition: { x: endOffset, y: 0 }
    });
  }
}

/**
 * Gets the current timings array from the app
 * This is useful for verifying timing adjustments
 */
export async function getCurrentTimings(page: Page): Promise<TimingEntry[]> {
  return await page.evaluate(() => {
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

    return timings;
  });
}
