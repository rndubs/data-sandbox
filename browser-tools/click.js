#!/usr/bin/env node

/**
 * Click Tool
 * Clicks on an element specified by a CSS selector.
 *
 * Usage: node click.js <css-selector>
 */

import puppeteer from 'puppeteer-core';

const args = process.argv.slice(2);

if (args.length < 1) {
  console.error('Usage: node click.js <css-selector>');
  console.error('\nExamples:');
  console.error('  node click.js "button[role=\'tab\']:nth-child(2)"');
  console.error('  node click.js ".workflow-item"');
  console.error('  node click.js "#submit-button"');
  process.exit(1);
}

const selector = args[0];

async function clickElement() {
  let browser;

  try {
    // Try to connect to existing Chrome instance on port 9222
    try {
      browser = await puppeteer.connect({
        browserURL: 'http://localhost:9222',
        defaultViewport: { width: 1920, height: 1080 }
      });
    } catch (e) {
      console.error('Error: No browser found on port 9222.');
      console.error('Please navigate to a page first using navigate.js or screenshot.js');
      process.exit(1);
    }

    const pages = await browser.pages();
    if (pages.length === 0) {
      console.error('Error: No pages found.');
      process.exit(1);
    }

    const page = pages[pages.length - 1];

    console.log(`Looking for element: ${selector}`);

    // Wait for the element to be available
    try {
      await page.waitForSelector(selector, { timeout: 5000 });
    } catch (e) {
      console.error(`Error: Element not found: ${selector}`);

      // Try to help debug
      const allButtons = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('button')).map(b => ({
          text: b.textContent,
          role: b.getAttribute('role'),
          class: b.className
        }));
      });
      console.error('\nAvailable buttons:');
      console.error(JSON.stringify(allButtons, null, 2));

      process.exit(1);
    }

    console.log(`Clicking element...`);
    await page.click(selector);

    // Wait a moment for any animations/transitions
    await new Promise(resolve => setTimeout(resolve, 500));

    console.log(`✓ Successfully clicked: ${selector}`);

  } catch (error) {
    console.error('Error clicking element:', error.message);
    process.exit(1);
  }
}

clickElement();
