#!/usr/bin/env node

/**
 * Evaluate Tool
 * Executes JavaScript code in the browser context and returns the result.
 *
 * Usage: node evaluate.js <javascript-code>
 *
 * The code should be a valid JavaScript expression or function.
 * Common uses:
 *   - Get page title: document.title
 *   - Get text content: document.body.innerText
 *   - Query elements: document.querySelector('h1').textContent
 *   - Get all links: Array.from(document.querySelectorAll('a')).map(a => a.href)
 */

import puppeteer from 'puppeteer-core';

const args = process.argv.slice(2);

if (args.length < 1) {
  console.error('Usage: node evaluate.js <javascript-code>');
  console.error('\nExamples:');
  console.error('  node evaluate.js "document.title"');
  console.error('  node evaluate.js "document.body.innerText"');
  console.error('  node evaluate.js "Array.from(document.querySelectorAll(\'h1\')).map(h => h.textContent)"');
  process.exit(1);
}

const code = args.join(' ');

async function evaluate() {
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
      console.error('Please launch Chrome with remote debugging enabled first.');
      console.error('You can use the navigate.js script to do this automatically.');
      process.exit(1);
    }

    const pages = await browser.pages();
    const page = pages[pages.length - 1];

    console.log(`Evaluating: ${code}`);
    const result = await page.evaluate((code) => {
      // eslint-disable-next-line no-eval
      return eval(code);
    }, code);

    console.log('\nResult:');
    console.log(JSON.stringify(result, null, 2));

  } catch (error) {
    console.error('Error evaluating code:', error.message);
    process.exit(1);
  }
}

evaluate();
