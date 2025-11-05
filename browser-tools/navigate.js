#!/usr/bin/env node

/**
 * Navigate Tool
 * Navigates to a URL in a new or existing tab.
 *
 * Usage: node navigate.js <url> [--new-tab]
 */

import puppeteer from 'puppeteer-core';

const args = process.argv.slice(2);

if (args.length < 1) {
  console.error('Usage: node navigate.js <url> [--new-tab]');
  process.exit(1);
}

const url = args[0];
const newTab = args.includes('--new-tab');

async function navigate() {
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

    if (newTab) {
      page = await browser.newPage();
    } else {
      const pages = await browser.pages();
      if (pages.length > 0) {
        page = pages[pages.length - 1];
      } else {
        page = await browser.newPage();
      }
    }

    console.log(`Navigating to ${url}...`);
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
    console.log(`Successfully navigated to ${url}`);

  } catch (error) {
    console.error('Error navigating:', error.message);
    process.exit(1);
  }
}

navigate();
