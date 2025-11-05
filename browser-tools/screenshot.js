#!/usr/bin/env node

/**
 * Screenshot Tool
 * Takes a screenshot of the current page and saves it to a file.
 *
 * Usage: node screenshot.js <output-path> [url]
 *
 * If URL is provided, navigates to it first, otherwise uses existing page.
 */

import puppeteer from 'puppeteer-core';

const args = process.argv.slice(2);

if (args.length < 1) {
  console.error('Usage: node screenshot.js <output-path> [url]');
  process.exit(1);
}

const outputPath = args[0];
const url = args[1];

async function takeScreenshot() {
  let browser;

  try {
    // Try to connect to existing Chrome instance on port 9222
    try {
      browser = await puppeteer.connect({
        browserURL: 'http://localhost:9222',
        defaultViewport: { width: 1920, height: 1080 }
      });
    } catch (e) {
      // If no browser is running, launch a new one
      console.error('No browser found on port 9222. Launching new Chrome instance...');
      browser = await puppeteer.launch({
        headless: false,
        executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        args: ['--remote-debugging-port=9222'],
        defaultViewport: { width: 1920, height: 1080 }
      });
    }

    let page;

    // Navigate to URL if provided
    if (url) {
      // Create a new page for the URL
      page = await browser.newPage();
      console.log(`Navigating to ${url}...`);
      await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
      // Give extra time for any dynamic content to load
      await new Promise(resolve => setTimeout(resolve, 2000));
    } else {
      // Use existing page
      const pages = await browser.pages();
      page = pages[pages.length - 1];
    }

    console.log(`Taking screenshot and saving to ${outputPath}...`);
    await page.screenshot({ path: outputPath, fullPage: false });
    console.log(`Screenshot saved successfully to ${outputPath}`);

  } catch (error) {
    console.error('Error taking screenshot:', error.message);
    process.exit(1);
  }
}

takeScreenshot();
