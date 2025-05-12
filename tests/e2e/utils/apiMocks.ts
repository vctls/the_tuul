/**
 * API mocking helpers for Playwright tests
 */
import { BrowserContext } from '@playwright/test';
import { promises as fs } from 'fs';
import { getFixturePath } from './setupHelpers';
import JSZip from 'jszip';

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

/**
 * Mocks the YouTube download API to return a fixture ZIP file
 */
export async function mockYouTubeDownloadApi(context: BrowserContext): Promise<void> {
  await context.route(/\/download_video\?/, async (route) => {
    // Create a new zip file with our fixtures
    const zip = new JSZip();

    // Add files to the zip
    const audioData = await fs.readFile(getFixturePath('youtube/audio'));
    const videoData = await fs.readFile(getFixturePath('youtube/video'));
    const metadataJson = await fs.readFile(getFixturePath('youtube/metadata.json'), 'utf-8');

    zip.file('audio.mp4', audioData);
    zip.file('video.mp4', videoData);
    zip.file('metadata.json', metadataJson);

    // Generate the zip file
    const zipBlob = await zip.generateAsync({ type: 'nodebuffer' });

    // Fulfill the request with the zip file
    await route.fulfill({
      status: 200,
      contentType: 'application/zip',
      body: zipBlob,
      headers: {
        'Content-Disposition': 'attachment; filename=youtube_video.zip'
      }
    });

    console.log('Mocked YouTube download endpoint with fixture files');
  });
}
