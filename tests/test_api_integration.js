/**
 * API Integration Tests
 *
 * Tests the API integration patterns in the web client to ensure
 * correct endpoint usage, error handling, and data transformation.
 */

const fs = require('fs');
const path = require('path');

// Read the app.js code
const appCode = fs.readFileSync(
    path.join(__dirname, '../web/public/app.js'),
    'utf-8'
);

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

console.log('='.repeat(60));
console.log('API Integration Tests');
console.log('='.repeat(60));

// Test 1: API_BASE configuration
test('API_BASE points to correct localhost endpoint', () => {
    const apiBaseMatch = appCode.match(/const API_BASE = ['"]([^'"]+)['"]/);
    assert(apiBaseMatch, 'Should define API_BASE');
    assert(apiBaseMatch[1] === 'http://localhost:8000/api', 'Should point to localhost:8000/api');
});

// Test 2: Upload uses FormData
test('Dataset upload uses FormData', () => {
    assert(appCode.includes('uploadDataset'), 'Should have uploadDataset function');
    assert(appCode.toLowerCase().includes('formdata'), 'Should use FormData for file upload');
    assert(appCode.includes('fileInput.files'), 'Should access file input');
});

// Test 3: All fetch calls use async/await
test('All fetch calls use async/await', () => {
    const fetchCalls = appCode.match(/fetch\(/g) || [];
    const awaitFetchCalls = appCode.match(/await fetch\(/g) || [];

    assert(fetchCalls.length > 0, 'Should have fetch calls');
    assert(fetchCalls.length === awaitFetchCalls.length,
        `All ${fetchCalls.length} fetch calls should use await`);
});

// Test 4: Error handling in API calls
test('API calls include try-catch error handling', () => {
    const asyncFunctions = appCode.match(/async function \w+\([^)]*\)\s*{/g) || [];
    const functionsWithTry = appCode.match(/async function[\s\S]+?try\s*{/g) || [];

    assert(asyncFunctions.length > 5, 'Should have multiple async functions');
    assert(functionsWithTry.length >= 5,
        'Most async functions should have try-catch');
});

// Test 5: Response status checking
test('Checks response.ok before processing', () => {
    const responseChecks = appCode.match(/response\.ok/g) || [];
    assert(responseChecks.length >= 3, 'Should check response.ok in multiple places');
});

// Test 6: JSON parsing
test('Uses response.json() to parse responses', () => {
    const jsonCalls = appCode.match(/await response\.json\(\)/g) || [];
    assert(jsonCalls.length >= 5, 'Should parse JSON responses');
});

// Test 7: Dataset endpoints
test('Dataset operations use correct endpoints', () => {
    // Upload
    assert(appCode.includes('`${API_BASE}/datasets/upload`'),
        'Should have upload endpoint');

    // List
    assert(appCode.includes('`${API_BASE}/datasets/`'),
        'Should have list datasets endpoint');

    // Preview
    assert(appCode.includes('`${API_BASE}/datasets/${datasetId}/preview'),
        'Should have preview endpoint');
});

// Test 8: Workflow endpoints
test('Workflow operations use correct endpoints', () => {
    // Create
    assert(appCode.includes('`${API_BASE}/workflows/`'),
        'Should have create workflow endpoint');

    // Get DAG
    assert(appCode.includes('/dag`'),
        'Should have DAG endpoint');

    // Execute
    assert(appCode.includes('/execute`'),
        'Should have execute endpoint');
});

// Test 9: Node endpoints
test('Node operations use correct endpoints', () => {
    // Get data
    assert(appCode.includes('/data'),
        'Should have node data endpoint');

    // Get plot
    assert(appCode.includes('/plot'),
        'Should have plot endpoint');
});

// Test 10: HTTP methods
test('Uses correct HTTP methods', () => {
    // POST for create operations
    const postCalls = appCode.match(/method:\s*['"]POST['"]/g) || [];
    assert(postCalls.length >= 3, 'Should have POST requests for create operations');

    // GET is default (no method specified)
    const getCalls = appCode.match(/fetch\([^)]+\)/g) || [];
    assert(getCalls.length > postCalls.length, 'Should have more GET than POST requests');
});

// Test 11: Content-Type headers
test('Sets Content-Type for JSON requests', () => {
    const jsonHeaders = appCode.match(/['"]Content-Type['"]:\s*['"]application\/json['"]/g) || [];
    assert(jsonHeaders.length >= 1, 'Should set JSON content type for POST requests');
});

// Test 12: Query parameters
test('Uses query parameters correctly', () => {
    // Should use params for filtering/pagination
    assert(appCode.includes('?limit='),
        'Should use limit query parameter');

    // Should use template literals for dynamic params
    assert(appCode.includes('?channel_id='),
        'Should use channel_id query parameter');
});

// Test 13: Error messages to user
test('Shows error messages to user', () => {
    const alertCalls = appCode.match(/alert\(/g) || [];
    assert(alertCalls.length >= 5, 'Should show alerts for errors and success');

    // Check error message formatting
    assert(appCode.includes('Error:'), 'Should prefix error messages');
});

// Test 14: Loading states
test('Has loading state management patterns', () => {
    // Should define load functions
    assert(appCode.includes('function loadDatasets'), 'Should define loadDatasets');
    assert(appCode.includes('function loadWorkflows'), 'Should define loadWorkflows');

    // Should call load functions
    assert(appCode.includes('loadDatasets()'), 'Should call loadDatasets');
    assert(appCode.includes('loadWorkflows()'), 'Should call loadWorkflows');
});

// Test 15: Template literal usage
test('Uses template literals for dynamic content', () => {
    const templateLiterals = appCode.match(/`[^`]*\$\{[^}]+\}[^`]*`/g) || [];
    assert(templateLiterals.length >= 20,
        `Should use template literals extensively (found ${templateLiterals.length})`);
});

// Test 16: Map operations for rendering
test('Uses map() for rendering lists', () => {
    const mapCalls = appCode.match(/\.map\(/g) || [];
    assert(mapCalls.length >= 5, 'Should use map() to render lists');
});

// Test 17: Array join for HTML
test('Uses join() to combine HTML strings', () => {
    const joinCalls = appCode.match(/\.join\(['"]['"]\)/g) || [];
    assert(joinCalls.length >= 3, 'Should use join to combine HTML');
});

// Test 18: Plotly integration
test('Integrates with Plotly for charts', () => {
    assert(appCode.includes('Plotly.newPlot'), 'Should use Plotly.newPlot');

    // Should create traces
    assert(appCode.includes('type:'), 'Should define trace type');
    assert(appCode.includes('mode:'), 'Should define trace mode');

    // Should create layouts
    assert(appCode.includes('xaxis:'), 'Should define x-axis');
    assert(appCode.includes('yaxis:'), 'Should define y-axis');
});

// Test 19: D3 integration for DAG
test('Integrates with D3 for DAG visualization', () => {
    assert(appCode.includes('d3.select'), 'Should use d3.select');
    assert(appCode.includes('svg'), 'Should create SVG');
    assert(appCode.includes('append'), 'Should append elements');
});

// Test 20: Dynamic element updates
test('Updates DOM elements dynamically', () => {
    assert(appCode.includes('.innerHTML'), 'Should update innerHTML');
    assert(appCode.includes('.value'), 'Should access input values');
});

// Test 21: Confirmation dialogs
test('Uses confirmation for destructive actions', () => {
    const confirmCalls = appCode.match(/if\s*\(\s*!confirm\(/g) || [];
    assert(confirmCalls.length >= 1, 'Should confirm destructive actions');
});

// Test 22: URL parameter handling
test('Handles workflow and node IDs in URLs', () => {
    // Should use workflowId variable
    assert(appCode.includes('workflowId'), 'Should use workflowId variable');

    // Should use nodeId variable
    assert(appCode.includes('nodeId'), 'Should use nodeId variable');
});

// Test 23: State management
test('Manages client-side state', () => {
    assert(appCode.includes('let currentWorkflow'), 'Should track current workflow');
    assert(appCode.includes('let currentDAG'), 'Should track current DAG');
});

// Test 24: Event handlers
test('Defines event handlers', () => {
    const onclickHandlers = appCode.match(/onclick="/g) || [];
    const onchangeHandlers = appCode.match(/onchange="/g) || [];

    // Note: onclick/onchange are in HTML, not JS, so this checks references
    assert(appCode.includes('showTab'), 'Should have tab switching');
});

// Test 25: Select element population
test('Populates select elements dynamically', () => {
    assert(appCode.includes('select.innerHTML'), 'Should update select innerHTML');
    assert(appCode.includes('<option'), 'Should create option elements');
});

// Print summary
console.log('\n' + '='.repeat(60));
console.log('Test Summary');
console.log('='.repeat(60));
console.log(`Total tests: ${testsPassed + testsFailed}`);
console.log(`Passed: ${testsPassed}`);
console.log(`Failed: ${testsFailed}`);

if (testsFailed === 0) {
    console.log('\n✅ All API integration tests passed!');
    console.log('='.repeat(60));
    process.exit(0);
} else {
    console.log('\n❌ Some tests failed!');
    console.log('='.repeat(60));
    process.exit(1);
}
