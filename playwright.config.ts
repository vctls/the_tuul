// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './tests/e2e',
    /* Maximum time one test can run for */
    timeout: 20000,
    /* Run tests in files in parallel */
    fullyParallel: false,
    /* Fail the build on CI if you accidentally left test.only in the source code. */
    forbidOnly: !!process.env.CI,
    /* Retry on CI only */
    retries: process.env.CI ? 2 : 0,
    /* Reporter to use */
    reporter: 'html',
    /* Shared settings for all the projects below */
    use: {
        /* Base URL to use in actions like `await page.goto('/')` */
        baseURL: process.env.BASE_URL || 'http://localhost:8000',
        /* Collect trace when retrying the failed test */
        trace: 'on-first-retry',
        /* Take screenshots on test failures */
        screenshot: 'only-on-failure',
        /* Record video on failure */
        video: 'on-first-retry',
        /* Viewport size optimized for the app */
        viewport: { width: 1280, height: 720 },
    },

    /* Configure projects for different browsers */
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],

    /* Run local dev server before starting the tests */
    webServer: {
        command: 'just run-prod',
        url: process.env.BASE_URL || 'http://localhost:8000',
        reuseExistingServer: !process.env.CI,
        timeout: 120000,
    },
});