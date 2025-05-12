/**
 * API mocking helpers for Playwright tests
 */
import { BrowserContext } from '@playwright/test';
import { promises as fs } from 'fs';
import { getFixturePath } from './setupHelpers';

/**
 * Mocks the separate_track API to return a fixture ZIP file
 */
export async function mockSeparateTrackApi(context: BrowserContext, zipFilename: string = 'split_song.zip'): Promise<void> {
  await context.route('**/separate_track', async (route) => {
    // Get the path to the fixture file
    const audioZipPath = getFixturePath(zipFilename);

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
}
