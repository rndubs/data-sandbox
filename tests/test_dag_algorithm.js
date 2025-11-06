/**
 * DAG Layout Algorithm Tests
 *
 * Tests the topological sorting and layout algorithm used in the web client
 * to visualize workflow DAGs.
 */

// Extract and test the calculateDAGLayout function
function calculateDAGLayout(nodes, edges) {
    // Simple layout: arrange nodes from left to right based on dependencies
    const positions = {};
    const levels = {};

    // Build dependency graph
    const incoming = {};
    nodes.forEach(node => {
        incoming[node.id] = [];
    });

    edges.forEach(edge => {
        incoming[edge.to_node].push(edge.from_node);
    });

    // Calculate levels (topological ordering)
    const calculateLevel = (nodeId, visited = new Set()) => {
        if (levels[nodeId] !== undefined) return levels[nodeId];
        if (visited.has(nodeId)) return 0; // Cycle detection

        visited.add(nodeId);

        const deps = incoming[nodeId];
        if (deps.length === 0) {
            levels[nodeId] = 0;
        } else {
            levels[nodeId] = Math.max(...deps.map(d => calculateLevel(d, visited))) + 1;
        }

        return levels[nodeId];
    };

    nodes.forEach(node => calculateLevel(node.id));

    // Group by level
    const levelGroups = {};
    nodes.forEach(node => {
        const level = levels[node.id];
        if (!levelGroups[level]) levelGroups[level] = [];
        levelGroups[level].push(node);
    });

    const maxLevel = Math.max(...Object.keys(levelGroups).map(Number));

    // Assign positions
    Object.entries(levelGroups).forEach(([level, levelNodes]) => {
        const x = (Number(level) + 0.5) / (maxLevel + 1);
        levelNodes.forEach((node, idx) => {
            const y = (idx + 1) / (levelNodes.length + 1);
            positions[node.id] = { x, y };
        });
    });

    return positions;
}

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

function assertBetween(value, min, max, message) {
    if (value < min || value > max) {
        throw new Error(message || `Expected ${value} to be between ${min} and ${max}`);
    }
}

console.log('='.repeat(60));
console.log('DAG Layout Algorithm Tests');
console.log('='.repeat(60));

// Test 1: Simple linear workflow
test('Linear workflow (A -> B -> C)', () => {
    const nodes = [
        { id: 'a', name: 'Node A' },
        { id: 'b', name: 'Node B' },
        { id: 'c', name: 'Node C' }
    ];

    const edges = [
        { from_node: 'a', to_node: 'b' },
        { from_node: 'b', to_node: 'c' }
    ];

    const positions = calculateDAGLayout(nodes, edges);

    // Check all nodes have positions
    assert(positions.a, 'Node A should have position');
    assert(positions.b, 'Node B should have position');
    assert(positions.c, 'Node C should have position');

    // Check x positions increase left to right
    assert(positions.a.x < positions.b.x, 'A should be left of B');
    assert(positions.b.x < positions.c.x, 'B should be left of C');

    // Check positions are normalized (0-1)
    assertBetween(positions.a.x, 0, 1, 'A x position should be normalized');
    assertBetween(positions.a.y, 0, 1, 'A y position should be normalized');
});

// Test 2: Parallel branches
test('Parallel branches (A -> B, A -> C)', () => {
    const nodes = [
        { id: 'a', name: 'Node A' },
        { id: 'b', name: 'Node B' },
        { id: 'c', name: 'Node C' }
    ];

    const edges = [
        { from_node: 'a', to_node: 'b' },
        { from_node: 'a', to_node: 'c' }
    ];

    const positions = calculateDAGLayout(nodes, edges);

    // A should be at level 0, B and C at level 1
    assert(positions.a.x < positions.b.x, 'A should be left of B');
    assert(positions.a.x < positions.c.x, 'A should be left of C');

    // B and C should be at same x level (parallel)
    assert(Math.abs(positions.b.x - positions.c.x) < 0.01, 'B and C should be at same level');

    // B and C should have different y positions
    assert(Math.abs(positions.b.y - positions.c.y) > 0.1, 'B and C should be vertically separated');
});

// Test 3: Diamond pattern
test('Diamond pattern (A -> B, A -> C, B -> D, C -> D)', () => {
    const nodes = [
        { id: 'a', name: 'Node A' },
        { id: 'b', name: 'Node B' },
        { id: 'c', name: 'Node C' },
        { id: 'd', name: 'Node D' }
    ];

    const edges = [
        { from_node: 'a', to_node: 'b' },
        { from_node: 'a', to_node: 'c' },
        { from_node: 'b', to_node: 'd' },
        { from_node: 'c', to_node: 'd' }
    ];

    const positions = calculateDAGLayout(nodes, edges);

    // Check proper levels
    assert(positions.a.x < positions.b.x, 'A before B');
    assert(positions.a.x < positions.c.x, 'A before C');
    assert(positions.b.x < positions.d.x, 'B before D');
    assert(positions.c.x < positions.d.x, 'C before D');

    // B and C at same level
    assert(Math.abs(positions.b.x - positions.c.x) < 0.01, 'B and C at same level');

    // D should be rightmost
    assert(positions.d.x > positions.a.x, 'D is after A');
    assert(positions.d.x > positions.b.x, 'D is after B');
    assert(positions.d.x > positions.c.x, 'D is after C');
});

// Test 4: Single node
test('Single node (no edges)', () => {
    const nodes = [{ id: 'a', name: 'Node A' }];
    const edges = [];

    const positions = calculateDAGLayout(nodes, edges);

    assert(positions.a, 'Node should have position');
    assertBetween(positions.a.x, 0, 1, 'X should be normalized');
    assertBetween(positions.a.y, 0, 1, 'Y should be normalized');
});

// Test 5: Multiple independent chains
test('Multiple independent chains', () => {
    const nodes = [
        { id: 'a', name: 'Node A' },
        { id: 'b', name: 'Node B' },
        { id: 'c', name: 'Node C' },
        { id: 'd', name: 'Node D' }
    ];

    const edges = [
        { from_node: 'a', to_node: 'b' },
        { from_node: 'c', to_node: 'd' }
    ];

    const positions = calculateDAGLayout(nodes, edges);

    // All nodes should have positions
    assert(positions.a && positions.b && positions.c && positions.d, 'All nodes should have positions');

    // Chain 1: A -> B
    assert(positions.a.x < positions.b.x, 'A before B');

    // Chain 2: C -> D
    assert(positions.c.x < positions.d.x, 'C before D');

    // A and C should be at same level (both start nodes)
    assert(Math.abs(positions.a.x - positions.c.x) < 0.01, 'A and C at same level');

    // B and D should be at same level (both end nodes)
    assert(Math.abs(positions.b.x - positions.d.x) < 0.01, 'B and D at same level');
});

// Test 6: Complex DAG
test('Complex workflow (5 nodes, multiple paths)', () => {
    const nodes = [
        { id: 'load', name: 'Load Data' },
        { id: 'filter', name: 'Filter' },
        { id: 'transform', name: 'Transform' },
        { id: 'fft', name: 'FFT' },
        { id: 'save', name: 'Save' }
    ];

    const edges = [
        { from_node: 'load', to_node: 'filter' },
        { from_node: 'filter', to_node: 'transform' },
        { from_node: 'filter', to_node: 'fft' },
        { from_node: 'transform', to_node: 'save' },
        { from_node: 'fft', to_node: 'save' }
    ];

    const positions = calculateDAGLayout(nodes, edges);

    // Check all nodes have positions
    Object.values(positions).forEach(pos => {
        assertBetween(pos.x, 0, 1, 'X position normalized');
        assertBetween(pos.y, 0, 1, 'Y position normalized');
    });

    // Load should be leftmost
    assert(positions.load.x <= Math.min(
        positions.filter.x,
        positions.transform.x,
        positions.fft.x,
        positions.save.x
    ), 'Load should be leftmost');

    // Save should be rightmost
    assert(positions.save.x >= Math.max(
        positions.load.x,
        positions.filter.x,
        positions.transform.x,
        positions.fft.x
    ), 'Save should be rightmost');
});

// Test 7: Verify no overlapping nodes at same level
test('No overlapping nodes at same level', () => {
    const nodes = [
        { id: 'a', name: 'A' },
        { id: 'b', name: 'B' },
        { id: 'c', name: 'C' },
        { id: 'd', name: 'D' }
    ];

    const edges = [
        { from_node: 'a', to_node: 'b' },
        { from_node: 'a', to_node: 'c' },
        { from_node: 'a', to_node: 'd' }
    ];

    const positions = calculateDAGLayout(nodes, edges);

    // B, C, D should all have different y positions
    const yPositions = [positions.b.y, positions.c.y, positions.d.y];
    const uniqueY = new Set(yPositions);
    assert(uniqueY.size === 3, 'Nodes at same level should have unique y positions');
});

// Print summary
console.log('\n' + '='.repeat(60));
console.log('Test Summary');
console.log('='.repeat(60));
console.log(`Total tests: ${testsPassed + testsFailed}`);
console.log(`Passed: ${testsPassed}`);
console.log(`Failed: ${testsFailed}`);

if (testsFailed === 0) {
    console.log('\n✅ All DAG algorithm tests passed!');
    console.log('='.repeat(60));
    process.exit(0);
} else {
    console.log('\n❌ Some tests failed!');
    console.log('='.repeat(60));
    process.exit(1);
}
