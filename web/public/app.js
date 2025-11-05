// API base URL
const API_BASE = 'http://localhost:8000/api';

// State
let currentWorkflow = null;
let currentDAG = null;

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.add('hidden');
    });

    // Remove active styling from all tab buttons
    document.querySelectorAll('.tab-button').forEach(el => {
        el.classList.remove('border-blue-500', 'text-blue-600');
        el.classList.add('border-transparent', 'text-gray-500');
    });

    // Show selected tab
    document.getElementById(`content-${tabName}`).classList.remove('hidden');

    // Add active styling to selected tab button
    const tabButton = document.getElementById(`tab-${tabName}`);
    tabButton.classList.add('border-blue-500', 'text-blue-600');
    tabButton.classList.remove('border-transparent', 'text-gray-500');

    // Load data if needed
    if (tabName === 'datasets') {
        loadDatasets();
    } else if (tabName === 'workflows') {
        loadWorkflows();
    } else if (tabName === 'visualization') {
        populateWorkflowSelect();
    }
}

// Dataset functions
async function uploadDataset() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', file.name);

    try {
        const response = await fetch(`${API_BASE}/datasets/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upload failed');

        const data = await response.json();
        alert(`Dataset uploaded successfully! ID: ${data.id}`);
        loadDatasets();
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function loadDatasets() {
    try {
        const response = await fetch(`${API_BASE}/datasets/`);
        const datasets = await response.json();

        const container = document.getElementById('datasetsList');
        container.innerHTML = datasets.map(ds => `
            <div class="border border-gray-200 rounded p-4 hover:bg-gray-50">
                <div class="flex justify-between items-start">
                    <div>
                        <h3 class="font-semibold text-lg">${ds.name}</h3>
                        <p class="text-sm text-gray-600">${ds.description || 'No description'}</p>
                        <div class="mt-2 text-xs text-gray-500">
                            <p>Rows: ${ds.row_count || 'N/A'} | Channels: ${ds.channel_count || 'N/A'} | Sample Rate: ${ds.sample_rate ? ds.sample_rate.toFixed(0) + ' Hz' : 'N/A'}</p>
                            <p>ID: ${ds.id}</p>
                        </div>
                    </div>
                    <button onclick="previewDataset('${ds.id}')" class="bg-blue-500 hover:bg-blue-700 text-white text-sm font-bold py-1 px-3 rounded">
                        Preview
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading datasets:', error);
    }
}

async function previewDataset(datasetId) {
    try {
        const response = await fetch(`${API_BASE}/datasets/${datasetId}/preview?limit=10`);
        const preview = await response.json();

        const previewText = JSON.stringify(preview.data.slice(0, 5), null, 2);
        alert(`Dataset Preview:\n\nColumns: ${preview.columns.join(', ')}\n\nFirst rows:\n${previewText}`);
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Workflow functions
async function createWorkflow() {
    const name = document.getElementById('workflowName').value;

    if (!name) {
        alert('Please enter a workflow name');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/workflows/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });

        if (!response.ok) throw new Error('Failed to create workflow');

        const workflow = await response.json();
        alert(`Workflow created! ID: ${workflow.id}`);
        document.getElementById('workflowName').value = '';
        loadWorkflows();
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function loadWorkflows() {
    try {
        const response = await fetch(`${API_BASE}/workflows/`);
        const workflows = await response.json();

        const container = document.getElementById('workflowsList');
        container.innerHTML = workflows.map(wf => `
            <div class="border border-gray-200 rounded p-4 hover:bg-gray-50">
                <div class="flex justify-between items-start">
                    <div>
                        <h3 class="font-semibold text-lg">${wf.name}</h3>
                        <p class="text-sm text-gray-600">${wf.description || 'No description'}</p>
                        <div class="mt-2 text-xs text-gray-500">
                            <p>Status: <span class="font-semibold ${getStatusColor(wf.status)}">${wf.status}</span></p>
                            <p>ID: ${wf.id}</p>
                        </div>
                    </div>
                    <div class="space-x-2">
                        <button onclick="executeWorkflow('${wf.id}')" class="bg-green-500 hover:bg-green-700 text-white text-sm font-bold py-1 px-3 rounded">
                            Execute
                        </button>
                        <button onclick="viewWorkflow('${wf.id}')" class="bg-blue-500 hover:bg-blue-700 text-white text-sm font-bold py-1 px-3 rounded">
                            View
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading workflows:', error);
    }
}

function getStatusColor(status) {
    const colors = {
        'draft': 'text-gray-600',
        'running': 'text-blue-600',
        'completed': 'text-green-600',
        'failed': 'text-red-600'
    };
    return colors[status] || 'text-gray-600';
}

async function executeWorkflow(workflowId) {
    if (!confirm('Execute this workflow?')) return;

    try {
        const response = await fetch(`${API_BASE}/workflows/${workflowId}/execute`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Execution failed');

        const result = await response.json();
        alert(`Workflow executed!\nStatus: ${result.status}\nNodes executed: ${result.nodes_executed}`);
        loadWorkflows();
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

function viewWorkflow(workflowId) {
    showTab('visualization');
    document.getElementById('vizWorkflowSelect').value = workflowId;
    loadWorkflowDAG();
}

// Visualization functions
async function populateWorkflowSelect() {
    try {
        const response = await fetch(`${API_BASE}/workflows/`);
        const workflows = await response.json();

        const select = document.getElementById('vizWorkflowSelect');
        select.innerHTML = '<option value="">Select a workflow...</option>' +
            workflows.map(wf => `<option value="${wf.id}">${wf.name}</option>`).join('');
    } catch (error) {
        console.error('Error loading workflows:', error);
    }
}

async function loadWorkflowDAG() {
    const workflowId = document.getElementById('vizWorkflowSelect').value;
    if (!workflowId) return;

    try {
        const response = await fetch(`${API_BASE}/workflows/${workflowId}/dag`);
        const dag = await response.json();

        currentWorkflow = workflowId;
        currentDAG = dag;

        // Render DAG
        renderDAG(dag);

        // Populate node select
        const nodeSelect = document.getElementById('nodeSelect');
        nodeSelect.innerHTML = '<option value="">Select a node...</option>' +
            dag.nodes.map(node => `<option value="${node.id}">${node.name}</option>`).join('');

        // Load comparison plots
        loadComparisonPlots(dag);
    } catch (error) {
        console.error('Error loading DAG:', error);
    }
}

function renderDAG(dag) {
    const container = document.getElementById('dagViz');
    container.innerHTML = '';

    // Create simple DAG visualization using HTML/CSS
    const nodeMap = {};
    dag.nodes.forEach((node, idx) => {
        nodeMap[node.id] = { ...node, y: idx };
    });

    // Calculate positions
    const positions = calculateDAGLayout(dag.nodes, dag.edges);

    // Create SVG
    const svg = d3.select('#dagViz')
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%');

    const width = container.clientWidth;
    const height = container.clientHeight;

    // Draw edges
    svg.selectAll('line')
        .data(dag.edges)
        .enter()
        .append('line')
        .attr('x1', d => positions[d.from_node].x * width)
        .attr('y1', d => positions[d.from_node].y * height)
        .attr('x2', d => positions[d.to_node].x * width)
        .attr('y2', d => positions[d.to_node].y * height)
        .attr('stroke', '#999')
        .attr('stroke-width', 2)
        .attr('marker-end', 'url(#arrowhead)');

    // Add arrowhead marker
    svg.append('defs')
        .append('marker')
        .attr('id', 'arrowhead')
        .attr('markerWidth', 10)
        .attr('markerHeight', 10)
        .attr('refX', 8)
        .attr('refY', 3)
        .attr('orient', 'auto')
        .append('polygon')
        .attr('points', '0 0, 10 3, 0 6')
        .attr('fill', '#999');

    // Draw nodes
    const nodes = svg.selectAll('g.node')
        .data(dag.nodes)
        .enter()
        .append('g')
        .attr('class', 'node')
        .attr('transform', d => `translate(${positions[d.id].x * width},${positions[d.id].y * height})`);

    nodes.append('rect')
        .attr('x', -60)
        .attr('y', -20)
        .attr('width', 120)
        .attr('height', 40)
        .attr('rx', 5)
        .attr('fill', d => getNodeColor(d.status))
        .attr('stroke', '#333')
        .attr('stroke-width', 2);

    nodes.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', -5)
        .attr('fill', 'white')
        .attr('font-size', '12px')
        .attr('font-weight', 'bold')
        .text(d => d.operation_type);

    nodes.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', 10)
        .attr('fill', 'white')
        .attr('font-size', '10px')
        .text(d => d.status);
}

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

function getNodeColor(status) {
    const colors = {
        'pending': '#6B7280',
        'running': '#3B82F6',
        'completed': '#10B981',
        'failed': '#EF4444'
    };
    return colors[status] || '#6B7280';
}

async function loadPlot() {
    const nodeId = document.getElementById('nodeSelect').value;
    if (!nodeId) return;

    try {
        const response = await fetch(`${API_BASE}/nodes/${nodeId}/plot?channel_id=0&limit=1000`);
        const plotData = await response.json();

        const trace = {
            x: plotData.x,
            y: plotData.y,
            type: 'scatter',
            mode: 'lines',
            name: `Channel ${plotData.channel_id}`
        };

        const layout = {
            title: plotData.title,
            xaxis: { title: plotData.x_label },
            yaxis: { title: plotData.y_label },
            height: 400
        };

        Plotly.newPlot('plotViz', [trace], layout);
    } catch (error) {
        console.error('Error loading plot:', error);
    }
}

async function loadComparisonPlots(dag) {
    const container = document.getElementById('comparisonPlots');
    container.innerHTML = '';

    // Get completed nodes only
    const completedNodes = dag.nodes.filter(node => node.status === 'completed');

    for (const node of completedNodes) {
        try {
            const response = await fetch(`${API_BASE}/nodes/${node.id}/plot?channel_id=0&limit=500`);
            const plotData = await response.json();

            const plotDiv = document.createElement('div');
            plotDiv.id = `plot-${node.id}`;
            container.appendChild(plotDiv);

            const trace = {
                x: plotData.x,
                y: plotData.y,
                type: 'scatter',
                mode: 'lines',
                name: node.name
            };

            const layout = {
                title: `${node.name} - ${plotData.title}`,
                xaxis: { title: plotData.x_label },
                yaxis: { title: plotData.y_label },
                height: 300,
                margin: { t: 40, r: 20, b: 40, l: 60 }
            };

            Plotly.newPlot(plotDiv, [trace], layout);
        } catch (error) {
            console.error(`Error loading plot for node ${node.id}:`, error);
        }
    }
}

// Initialize
loadDatasets();
