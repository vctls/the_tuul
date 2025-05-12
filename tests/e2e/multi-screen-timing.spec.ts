import { test, expect } from '@playwright/test';
import {
  setupTestEnvironment,
  navigateToTab,
  TabId,
  uploadAudioFile,
  loadAndEnterLyrics,
  mockSeparateTrackApi,
  togglePlayback,
  enterTimings,
  adjustTiming,
  getCurrentTimings,
  expectSegmentTimingsToBe
} from './utils';

test.describe('Multi-screen Timing and Adjustment', () => {
  test.describe.configure({ timeout: 180000 }); // 3 minutes

  test.beforeEach(async ({ page, context }) => {
    await setupTestEnvironment(page);
    await mockSeparateTrackApi(context);
  });

  test('Adjust timing on first screen and continue with second screen', async ({ page }) => {
    // 1. Setup: Upload audio and enter a 2-screen lyrics text
    await navigateToTab(page, TabId.SongInfo);
    await uploadAudioFile(page, 'my_fair_lady.mp3', "David Byrne", "My Fair Lady");

    await navigateToTab(page, TabId.LyricInput);

    // Two-screen lyrics with clear separation
    const twoScreenLyrics =
      "First_screen_line_1\n" +
      "First_screen_line_2\n" +
      "First_screen_line_3\n" +
      "First_screen_line_4\n" +
      "------\n" +  // This line marks the screen break
      "Second_screen_line_1\n" +
      "Second_screen_line_2\n" +
      "Second_screen_line_3\n" +
      "Second_screen_line_4";

    await loadAndEnterLyrics(page, twoScreenLyrics);

    // 2. Navigate to Timing tab and do timings for first screen only
    await navigateToTab(page, TabId.SongTiming);

    // Define timings for the first screen (4 lines = 8 events, start and end for each line)
    const firstScreenTimings = [
      { time: 1.0, type: 1 },  // Line 1 start
      { time: 2.0, type: 2 },  // Line 1 end
      { time: 3.0, type: 1 },  // Line 2 start
      { time: 4.0, type: 2 },  // Line 2 end
      { time: 5.0, type: 1 },  // Line 3 start
      { time: 6.0, type: 2 },  // Line 3 end
      { time: 7.0, type: 1 },  // Line 4 start
      { time: 8.0, type: 2 },  // Line 4 end
      { time: 9.0, type: 1 },  // Screen separator start
    ];

    // Enter timings for first screen
    await enterTimings(page, firstScreenTimings);

    // Stop playback after entering timings for first screen
    await togglePlayback(page);

    // 3. Navigate to Adjustment tab and adjust the first segment
    await navigateToTab(page, TabId.TimingAdjustment);

    // Adjust the timing of the first segment - move start time earlier by 0.5 seconds
    const firstSegmentIndex = 0;
    const startTimeAdjustment = -50; // Pixel adjustment that would correspond to ~0.5 seconds
    await adjustTiming(page, firstSegmentIndex, startTimeAdjustment, 0);

    // Get adjusted timings to verify later
    const adjustedTimings = await getCurrentTimings(page);

    // 4. Navigate back to Timing tab to do timings for second screen
    await navigateToTab(page, TabId.SongTiming);

    // Continue with timings for the second screen
    const secondScreenTimings = [
      { time: 9.0, type: 2 },  // Screen separator end
      { time: 10.0, type: 1 }, // Line 5 start
      { time: 11.0, type: 2 }, // Line 5 end
      { time: 12.0, type: 1 }, // Line 6 start
      { time: 13.0, type: 2 }, // Line 6 end
      { time: 14.0, type: 1 }, // Line 7 start
      { time: 15.0, type: 2 }, // Line 7 end
      { time: 16.0, type: 1 }, // Line 8 start
      { time: 17.0, type: 2 }, // Line 8 end
    ];

    // Enter timings for second screen
    await togglePlayback(page); // Start playback again
    await enterTimings(page, secondScreenTimings);

    // 5. Verify that adjustment to first segment was not overwritten
    await navigateToTab(page, TabId.TimingAdjustment);

    // Check that first segment still has the adjusted start time (~0.5 seconds earlier)
    // The expected value will depend on the exact conversion between pixels and time
    // For this test, we'll assume it's around 0.5 seconds
    const expectedStartTime = 0.5; // Should be very close to this value
    const expectedEndTime = 2.0;   // Should be unchanged

    await expectSegmentTimingsToBe(page, firstSegmentIndex, expectedStartTime, expectedEndTime, 0.1);

    // 6. Verify the Submit tab is now enabled after completing all timings
    await expectTabToBeEnabled(page, TabId.Submit);
  });
});
