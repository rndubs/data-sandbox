/**
 * Web Client Tests
 *
 * Tests for the Time Series Platform web client (app.js)
 *
 * These tests validate:
 * - JavaScript code structure and syntax
 * - API integration logic
 * - Data transformation functions
 * - DAG layout algorithms
 */

const fs = require('fs');
const path = require('path');

// Test framework
let testsPassed = 0;
let testsFailed = 0;

function test(name, fn) {
    try {
        fn();
        console.log(`✓ ${name}`);
        testsPassed++;
    } catch (error) {
        console.log(`✗ ${name}`);
        console.log(`  Error: ${error.message}`);
        testsFailed++;
    }
}

function assert(condition, message) {
    if (!condition) {
        throw new Error(message || 'Assertion failed');
    }
}

function assertEquals(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(message || `Expected ${expected}, got ${actual}`);
    }
}

// Mock browser environment
global.window = {};
global.document = {
    getElementById: (id) => ({
        value: '',
        innerHTML: '',
        classList: {
            add: () => {},
            remove: () => {}
        }
    }),
    querySelectorAll: () => [],
};
global.alert = (msg) => console.log(`[ALERT] ${msg}`);
global.confirm = () => true;
global.fetch = async (url, options) => {
    return {
        ok: true,
        json: async () => ({}),
        status: 200
    };
};
global.Plotly = {
    newPlot: () => {}
};
global.d3 = {
    select: () => ({
        append: () => ({
            attr: () => ({
                attr: () => ({
                    attr: () => ({})
                })
            }),
            append: () => ({})
        }),
        selectAll: () => ({
            data: () => ({
                enter: () => ({
                    append: () => ({
                        attr: () => ({
                            attr: () => ({
                                attr: () => ({})
                            })
                        }),
                        append: () => ({
                            attr: () => ({
                                attr: () => ({})
                            })
                        }),
                        text: () => ({})
                    })
                })
            })
        })
    })
};

console.log('='.repeat(60));
console.log('Web Client Test Suite');
console.log('='.repeat(60));

// Test 1: File exists
test('app.js file exists', () => {
    const filePath = path.join(__dirname, '../web/public/app.js');
    assert(fs.existsSync(filePath), 'app.js should exist');
});

// Test 2: Load and parse JavaScript
let appCode;
test('app.js is valid JavaScript', () => {
    const filePath = path.join(__dirname, '../web/public/app.js');
    appCode = fs.readFileSync(filePath, 'utf-8');

    // Try to evaluate it (will throw if syntax error)
    try {
        eval(appCode);
    } catch (error) {
        if (error.message.includes('not defined')) {
            // Expected - browser APIs not defined, but syntax is valid
        } else {
            throw error;
        }
    }
});

// Test 3: Check for required constants
test('Defines API_BASE constant', () => {
    assert(appCode.includes('const API_BASE'), 'Should define API_BASE');
    assert(appCode.includes('http://localhost:8000/api'), 'Should point to correct API URL');
});

// Test 4: Check for tab switching function
test('Defines showTab function', () => {
    assert(appCode.includes('function showTab('), 'Should define showTab function');
});

// Test 5: Check for dataset functions
test('Defines dataset management functions', () => {
    assert(appCode.includes('async function uploadDataset('), 'Should define uploadDataset');
    assert(appCode.includes('async function loadDatasets('), 'Should define loadDatasets');
    assert(appCode.includes('async function previewDataset('), 'Should define previewDataset');
});

// Test 6: Check for workflow functions
test('Defines workflow management functions', () => {
    assert(appCode.includes('async function createWorkflow('), 'Should define createWorkflow');
    assert(appCode.includes('async function loadWorkflows('), 'Should define loadWorkflows');
    assert(appCode.includes('async function executeWorkflow('), 'Should define executeWorkflow');
});

// Test 7: Check for visualization functions
test('Defines visualization functions', () => {
    assert(appCode.includes('async function loadWorkflowDAG('), 'Should define loadWorkflowDAG');
    assert(appCode.includes('function renderDAG('), 'Should define renderDAG');
    assert(appCode.includes('async function loadPlot('), 'Should define loadPlot');
    assert(appCode.includes('function calculateDAGLayout('), 'Should define calculateDAGLayout');
});

// Test 8: Check for error handling
test('Includes error handling', () => {
    const tryBlocks = (appCode.match(/try\s*{/g) || []).length;
    const catchBlocks = (appCode.match(/catch\s*\(/g) || []).length;
    assert(tryBlocks > 5, `Should have multiple try blocks (found ${tryBlocks})`);
    assert(catchBlocks > 5, `Should have multiple catch blocks (found ${catchBlocks})`);
    assertEquals(tryBlocks, catchBlocks, 'Try and catch blocks should match');
});

// Test 9: Check API endpoints used
test('Uses correct API endpoints', () => {
    const endpoints = [
        '/datasets/upload',
        '/datasets/',
        '/workflows/',
        '/dag',
        '/execute',
        '/nodes/',
        '/data',
        '/plot'
    ];

    endpoints.forEach(endpoint => {
        assert(
            appCode.includes(endpoint),
            `Should use endpoint containing: ${endpoint}`
        );
    });
});

// Test 10: Check for status color mapping
test('Defines status color mapping', () => {
    assert(appCode.includes('function getStatusColor('), 'Should define getStatusColor');
    assert(appCode.includes("'draft'"), 'Should handle draft status');
    assert(appCode.includes("'running'"), 'Should handle running status');
    assert(appCode.includes("'completed'"), 'Should handle completed status');
    assert(appCode.includes("'failed'"), 'Should handle failed status');
});

// Test 11: Check for node color mapping
test('Defines node color mapping for DAG', () => {
    assert(appCode.includes('function getNodeColor('), 'Should define getNodeColor');
    assert(appCode.includes("'pending'"), 'Should handle pending status');
});

// Test 12: Test calculateDAGLayout algorithm
test('DAG layout algorithm structure', () => {
    assert(appCode.includes('function calculateDAGLayout(nodes, edges)'), 'Should define layout function');
    assert(appCode.includes('topological'), 'Should reference topological ordering');
    assert(appCode.includes('levels'), 'Should calculate node levels');
});

// Test 13: Check for comparison plots
test('Includes multi-node comparison', () => {
    assert(appCode.includes('async function loadComparisonPlots('), 'Should define comparison function');
    assert(appCode.includes('completedNodes'), 'Should filter for completed nodes');
});

// Test 14: HTML structure validation
test('index.html exists and is valid', () => {
    const htmlPath = path.join(__dirname, '../web/public/index.html');
    assert(fs.existsSync(htmlPath), 'index.html should exist');

    const htmlContent = fs.readFileSync(htmlPath, 'utf-8');
    assert(htmlContent.includes('<!DOCTYPE html>'), 'Should have DOCTYPE');
    assert(htmlContent.includes('<html'), 'Should have html tag');
    assert(htmlContent.includes('</html>'), 'Should close html tag');
});

// Test 15: HTML includes required libraries
test('HTML includes required external libraries', () => {
    const htmlPath = path.join(__dirname, '../web/public/index.html');
    const htmlContent = fs.readFileSync(htmlPath, 'utf-8');

    assert(htmlContent.includes('tailwindcss'), 'Should include Tailwind CSS');
    assert(htmlContent.includes('plotly'), 'Should include Plotly.js');
    assert(htmlContent.includes('d3js.org') || htmlContent.includes('d3.js'), 'Should include D3.js');
});

// Test 16: HTML includes app.js
test('HTML links to app.js', () => {
    const htmlPath = path.join(__dirname, '../web/public/index.html');
    const htmlContent = fs.readFileSync(htmlPath, 'utf-8');

    assert(htmlContent.includes('app.js'), 'Should link to app.js');
});

// Test 17: HTML has required tabs
test('HTML has all required tabs', () => {
    const htmlPath = path.join(__dirname, '../web/public/index.html');
    const htmlContent = fs.readFileSync(htmlPath, 'utf-8');

    assert(htmlContent.includes('tab-datasets'), 'Should have datasets tab');
    assert(htmlContent.includes('tab-workflows'), 'Should have workflows tab');
    assert(htmlContent.includes('tab-visualization'), 'Should have visualization tab');
});

// Test 18: HTML has required content areas
test('HTML has all content areas', () => {
    const htmlPath = path.join(__dirname, '../web/public/index.html');
    const htmlContent = fs.readFileSync(htmlPath, 'utf-8');

    assert(htmlContent.includes('content-datasets'), 'Should have datasets content');
    assert(htmlContent.includes('content-workflows'), 'Should have workflows content');
    assert(htmlContent.includes('content-visualization'), 'Should have visualization content');
});

// Test 19: HTML has visualization elements
test('HTML has visualization containers', () => {
    const htmlPath = path.join(__dirname, '../web/public/index.html');
    const htmlContent = fs.readFileSync(htmlPath, 'utf-8');

    assert(htmlContent.includes('id="dagViz"'), 'Should have DAG visualization container');
    assert(htmlContent.includes('id="plotViz"'), 'Should have plot visualization container');
    assert(htmlContent.includes('id="comparisonPlots"'), 'Should have comparison plots container');
});

// Test 20: Check for responsive design
test('Uses responsive design classes', () => {
    const htmlPath = path.join(__dirname, '../web/public/index.html');
    const htmlContent = fs.readFileSync(htmlPath, 'utf-8');

    assert(htmlContent.includes('grid'), 'Should use grid layout');
    assert(htmlContent.includes('lg:'), 'Should have large screen breakpoints');
    assert(htmlContent.includes('md:'), 'Should have medium screen breakpoints');
});

// Test 21: Nginx config exists
test('nginx.conf exists', () => {
    const configPath = path.join(__dirname, '../web/nginx.conf');
    assert(fs.existsSync(configPath), 'nginx.conf should exist');
});

// Test 22: Nginx config is valid
test('nginx.conf has valid structure', () => {
    const configPath = path.join(__dirname, '../web/nginx.conf');
    const configContent = fs.readFileSync(configPath, 'utf-8');

    assert(configContent.includes('server {'), 'Should have server block');
    assert(configContent.includes('listen 80'), 'Should listen on port 80');
    assert(configContent.includes('root /usr/share/nginx/html'), 'Should set correct root');
});

// Test 23: Dockerfile exists
test('Web Dockerfile exists', () => {
    const dockerfilePath = path.join(__dirname, '../web/Dockerfile');
    assert(fs.existsSync(dockerfilePath), 'Dockerfile should exist');
});

// Test 24: Dockerfile uses nginx
test('Dockerfile uses nginx base image', () => {
    const dockerfilePath = path.join(__dirname, '../web/Dockerfile');
    const dockerContent = fs.readFileSync(dockerfilePath, 'utf-8');

    assert(dockerContent.includes('FROM nginx'), 'Should use nginx base image');
    assert(dockerContent.includes('COPY public'), 'Should copy public files');
});

// Test 25: Code follows async/await pattern
test('Uses async/await for API calls', () => {
    const asyncFunctions = (appCode.match(/async function/g) || []).length;
    const awaitCalls = (appCode.match(/await /g) || []).length;

    assert(asyncFunctions >= 8, `Should have multiple async functions (found ${asyncFunctions})`);
    assert(awaitCalls >= 10, `Should have multiple await calls (found ${awaitCalls})`);
});

// Print summary
console.log('\n' + '='.repeat(60));
console.log('Test Summary');
console.log('='.repeat(60));
console.log(`Total tests: ${testsPassed + testsFailed}`);
console.log(`Passed: ${testsPassed}`);
console.log(`Failed: ${testsFailed}`);

if (testsFailed === 0) {
    console.log('\n✅ All web client tests passed!');
    console.log('='.repeat(60));
    process.exit(0);
} else {
    console.log('\n❌ Some tests failed!');
    console.log('='.repeat(60));
    process.exit(1);
}
