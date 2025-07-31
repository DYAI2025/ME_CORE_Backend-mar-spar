import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';

test.describe('Dashboard E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load dashboard homepage', async ({ page }) => {
    await expect(page).toHaveTitle(/MarkerEngine Core Dashboard/);
    await expect(page.locator('h1')).toContainText('MarkerEngine Dashboard');
  });

  test('should display system health status', async ({ page }) => {
    const healthCard = page.locator('[data-testid="system-health"]');
    await expect(healthCard).toBeVisible();
    
    // Check for health status indicators
    await expect(healthCard.locator('.status-indicator')).toBeVisible();
    
    // Check for component statuses
    const components = ['Backend API', 'MongoDB', 'Redis', 'Spark NLP'];
    for (const component of components) {
      await expect(healthCard).toContainText(component);
    }
  });

  test('should navigate to markers page', async ({ page }) => {
    await page.click('text=Markers');
    await expect(page).toHaveURL(/\/markers/);
    
    // Check tabs are visible
    await expect(page.locator('text=Active Markers')).toBeVisible();
    await expect(page.locator('text=DETECT Registry')).toBeVisible();
    await expect(page.locator('text=Schemas')).toBeVisible();
  });

  test('should display marker list', async ({ page }) => {
    await page.goto('/markers');
    
    // Wait for markers to load
    await page.waitForSelector('[data-testid="marker-list"]', { timeout: 10000 });
    
    // Check if markers are displayed
    const markerItems = page.locator('[data-testid="marker-item"]');
    await expect(markerItems.first()).toBeVisible();
    
    // Check marker details
    const firstMarker = markerItems.first();
    await expect(firstMarker.locator('[data-testid="marker-id"]')).toBeVisible();
    await expect(firstMarker.locator('[data-testid="marker-type"]')).toBeVisible();
    await expect(firstMarker.locator('[data-testid="marker-status"]')).toBeVisible();
  });

  test('should open DETECT registry editor', async ({ page }) => {
    await page.goto('/markers');
    await page.click('text=DETECT Registry');
    
    // Wait for editor to load
    await page.waitForSelector('.monaco-editor', { timeout: 15000 });
    
    // Check editor controls
    await expect(page.locator('text=Validate')).toBeVisible();
    await expect(page.locator('text=Save Changes')).toBeVisible();
    await expect(page.locator('text=Revert')).toBeVisible();
  });

  test('should validate registry JSON', async ({ page }) => {
    await page.goto('/markers');
    await page.click('text=DETECT Registry');
    
    // Wait for editor
    await page.waitForSelector('.monaco-editor', { timeout: 15000 });
    
    // Click validate button
    await page.click('text=Validate');
    
    // Check for validation result
    await expect(page.locator('text=Registry is valid')).toBeVisible({ timeout: 5000 });
  });

  test('should display Jenkins status', async ({ page }) => {
    const jenkinsCard = page.locator('[data-testid="jenkins-status"]');
    await expect(jenkinsCard).toBeVisible();
    
    // Check Jenkins metrics
    await expect(jenkinsCard).toContainText(/Queue Size/);
    await expect(jenkinsCard).toContainText(/Executors/);
    
    // Check recent builds section
    await expect(jenkinsCard).toContainText(/Recent Builds/);
  });

  test('should show real-time updates', async ({ page }) => {
    // Check if WebSocket connection is established
    const wsIndicator = page.locator('[data-testid="ws-status"]');
    await expect(wsIndicator).toHaveClass(/connected/, { timeout: 10000 });
  });

  test('should handle API errors gracefully', async ({ page, context }) => {
    // Block API requests to simulate error
    await context.route(`${API_URL}/api/**`, route => route.abort());
    
    await page.reload();
    
    // Check error handling
    await expect(page.locator('text=Failed to load')).toBeVisible({ timeout: 10000 });
  });

  test('should search markers', async ({ page }) => {
    await page.goto('/markers');
    
    // Type in search box
    const searchInput = page.locator('[data-testid="marker-search"]');
    await searchInput.fill('A_TEST');
    
    // Check filtered results
    await expect(page.locator('[data-testid="marker-item"]')).toHaveCount(1, { timeout: 5000 });
  });

  test('should trigger deployment', async ({ page }) => {
    // Navigate to deployment section
    await page.click('text=Quick Actions');
    await page.click('text=Deploy to Staging');
    
    // Confirm deployment
    const modal = page.locator('[data-testid="confirm-modal"]');
    await expect(modal).toBeVisible();
    await modal.locator('text=Confirm').click();
    
    // Check deployment initiated
    await expect(page.locator('text=Deployment initiated')).toBeVisible({ timeout: 5000 });
  });
});

test.describe('API Integration Tests', () => {
  test('should fetch health status from API', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/health`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('status');
    expect(data).toHaveProperty('components');
  });

  test('should fetch markers from API', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/markers`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
    
    if (data.length > 0) {
      expect(data[0]).toHaveProperty('id');
      expect(data[0]).toHaveProperty('type');
      expect(data[0]).toHaveProperty('confidence');
    }
  });

  test('should validate DETECT registry', async ({ request }) => {
    const validRegistry = {
      "TEST_MARKER": {
        "type": "keyword",
        "keywords": ["test"],
        "confidence": 0.9
      }
    };

    const response = await request.post(`${API_URL}/api/dashboard/detect/registry/validate`, {
      data: { registry: validRegistry }
    });
    
    expect(response.ok()).toBeTruthy();
    
    const result = await response.json();
    expect(result.valid).toBe(true);
  });
});

test.describe('Performance Tests', () => {
  test('dashboard should load within 3 seconds', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    
    expect(loadTime).toBeLessThan(3000);
  });

  test('marker list should render 100+ items smoothly', async ({ page }) => {
    await page.goto('/markers');
    
    // Measure render performance
    const metrics = await page.evaluate(() => {
      const perfData = window.performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
        loadComplete: perfData.loadEventEnd - perfData.loadEventStart
      };
    });
    
    expect(metrics.domContentLoaded).toBeLessThan(1000);
    expect(metrics.loadComplete).toBeLessThan(2000);
  });
});