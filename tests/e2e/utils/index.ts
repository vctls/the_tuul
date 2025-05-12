/**
 * Index file for e2e test utilities
 *
 * This file exports all utility functions from the utils directory.
 */

// Export all utility modules
export * from './navigation';
export * from './setupHelpers';
export * from './inputs';
export * from './timings';
export * from './apiMocks';
export * from './assertions';

// Re-export expectTabToBeEnabled and expectTabToBeDisabled using isTabEnabled
import { Page, expect } from '@playwright/test';
import { TabId, isTabEnabled } from './navigation';

/**
 * Verifies that a specific tab is enabled
 */
export async function expectTabToBeEnabled(page: Page, tabId: TabId): Promise<void> {
  expect(await isTabEnabled(page, tabId)).toBeTruthy();
}

/**
 * Verifies that a specific tab is disabled
 */
export async function expectTabToBeDisabled(page: Page, tabId: TabId): Promise<void> {
  expect(await isTabEnabled(page, tabId)).toBeFalsy();
}
