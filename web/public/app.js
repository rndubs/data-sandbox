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
        populateBuilderWorkflowSelect();
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

async function viewWorkflow(workflowId) {
    showTab('visualization');
    await populateWorkflowSelect();
    document.getElementById('vizWorkflowSelect').value = workflowId;
    loadWorkflowDAG();
}

// Workflow Builder Functions
async function loadWorkflowBuilder() {
    const workflowId = document.getElementById('builderWorkflowSelect').value;
    if (!workflowId) {
        document.getElementById('workflowBuilderContent').classList.add('hidden');
        return;
    }

    document.getElementById('workflowBuilderContent').classList.remove('hidden');

    // Load datasets for the dropdown
    await loadDatasetsForBuilder();

    // Load current nodes
    await loadCurrentWorkflowNodes(workflowId);
}

async function loadDatasetsForBuilder() {
    try {
        const response = await fetch(`${API_BASE}/datasets/`);
        const datasets = await response.json();

        const select = document.getElementById('inputDataset');
        select.innerHTML = '<option value="">No dataset (connect to another node)</option>' +
            datasets.map(ds => `<option value="${ds.id}">${ds.name}</option>`).join('');
    } catch (error) {
        console.error('Error loading datasets:', error);
    }
}

async function loadCurrentWorkflowNodes(workflowId) {
    try {
        const response = await fetch(`${API_BASE}/workflows/${workflowId}/dag`);
        const dag = await response.json();

        // Update node lists
        const fromSelect = document.getElementById('fromNode');
        const toSelect = document.getElementById('toNode');

        const nodeOptions = dag.nodes.map(node =>
            `<option value="${node.id}">${node.name}</option>`
        ).join('');

        fromSelect.innerHTML = '<option value="">Select node...</option>' + nodeOptions;
        toSelect.innerHTML = '<option value="">Select node...</option>' + nodeOptions;

        // Display current nodes
        const nodesContainer = document.getElementById('currentNodes');
        if (dag.nodes.length === 0) {
            nodesContainer.innerHTML = '<p class="text-gray-500 text-sm">No nodes yet. Add operations above.</p>';
        } else {
            nodesContainer.innerHTML = dag.nodes.map(node => `
                <div class="border border-gray-200 rounded p-3 bg-gray-50">
                    <div class="font-semibold">${node.name}</div>
                    <div class="text-sm text-gray-600">Type: ${node.operation_type} | Status: <span class="${getStatusColor(node.status)}">${node.status}</span></div>
                    <div class="text-xs text-gray-500">ID: ${node.id}</div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading workflow nodes:', error);
    }
}

function showOperationConfig() {
    const operationType = document.getElementById('operationType').value;
    const configDiv = document.getElementById('operationConfig');

    if (!operationType) {
        configDiv.classList.add('hidden');
        return;
    }

    configDiv.classList.remove('hidden');

    let configHTML = '';

    switch (operationType) {
        case 'filter':
            configHTML = `
                <h4 class="font-semibold mb-2">Filter Configuration</h4>
                <div class="space-y-2">
                    <div>
                        <label class="block text-sm text-gray-700">Filter Type:</label>
                        <select id="filter_type" class="w-full px-2 py-1 border border-gray-300 rounded">
                            <option value="lowpass">Low-pass</option>
                            <option value="highpass">High-pass</option>
                            <option value="bandpass">Band-pass</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm text-gray-700">Cutoff Frequency (Hz):</label>
                        <input type="number" id="filter_cutoff" value="50" class="w-full px-2 py-1 border border-gray-300 rounded">
                        <p class="text-xs text-gray-500">For bandpass: enter as "10,100" (low,high)</p>
                    </div>
                    <div>
                        <label class="block text-sm text-gray-700">Filter Order:</label>
                        <input type="number" id="filter_order" value="4" class="w-full px-2 py-1 border border-gray-300 rounded">
                    </div>
                </div>
            `;
            break;

        case 'fft':
            configHTML = `
                <h4 class="font-semibold mb-2">FFT Configuration</h4>
                <div class="space-y-2">
                    <div>
                        <label class="block text-sm text-gray-700">Window Function:</label>
                        <select id="fft_window" class="w-full px-2 py-1 border border-gray-300 rounded">
                            <option value="">None</option>
                            <option value="hann">Hann</option>
                            <option value="hamming">Hamming</option>
                            <option value="blackman">Blackman</option>
                        </select>
                    </div>
                    <div>
                        <label class="flex items-center text-sm text-gray-700">
                            <input type="checkbox" id="fft_normalize" checked class="mr-2">
                            Normalize magnitude
                        </label>
                    </div>
                </div>
            `;
            break;

        case 'unit_conversion':
            configHTML = `
                <h4 class="font-semibold mb-2">Unit Conversion Configuration</h4>
                <div>
                    <label class="block text-sm text-gray-700">Conversion Type:</label>
                    <select id="conversion_type" class="w-full px-2 py-1 border border-gray-300 rounded">
                        <option value="celsius_to_fahrenheit">Celsius to Fahrenheit</option>
                        <option value="meters_to_feet">Meters to Feet</option>
                        <option value="mps_to_mph">m/s to mph</option>
                        <option value="pa_to_psi">Pascal to PSI</option>
                        <option value="mv_to_v">mV to V</option>
                    </select>
                </div>
            `;
            break;

        case 'time_shift':
            configHTML = `
                <h4 class="font-semibold mb-2">Time Shift Configuration</h4>
                <div>
                    <label class="block text-sm text-gray-700">Shift Amount (seconds):</label>
                    <input type="number" id="shift_seconds" value="1.0" step="0.1" class="w-full px-2 py-1 border border-gray-300 rounded">
                    <p class="text-xs text-gray-500">Positive values shift forward, negative backward</p>
                </div>
            `;
            break;
    }

    configDiv.innerHTML = configHTML;
}

function getOperationConfig() {
    const operationType = document.getElementById('operationType').value;
    let config = {};

    switch (operationType) {
        case 'filter':
            const cutoffValue = document.getElementById('filter_cutoff').value;
            const cutoff = cutoffValue.includes(',')
                ? cutoffValue.split(',').map(v => parseFloat(v.trim()))
                : parseFloat(cutoffValue);

            config = {
                filter_type: document.getElementById('filter_type').value,
                cutoff: cutoff,
                order: parseInt(document.getElementById('filter_order').value)
            };
            break;

        case 'fft':
            const window = document.getElementById('fft_window').value;
            config = {
                normalize: document.getElementById('fft_normalize').checked
            };
            if (window) config.window = window;
            break;

        case 'unit_conversion':
            config = {
                conversion: document.getElementById('conversion_type').value
            };
            break;

        case 'time_shift':
            config = {
                shift_seconds: parseFloat(document.getElementById('shift_seconds').value)
            };
            break;
    }

    return config;
}

async function addNodeToWorkflow() {
    const workflowId = document.getElementById('builderWorkflowSelect').value;
    const name = document.getElementById('nodeName').value;
    const operationType = document.getElementById('operationType').value;
    const datasetId = document.getElementById('inputDataset').value;

    if (!workflowId || !name || !operationType) {
        alert('Please fill in all required fields (workflow, name, operation type)');
        return;
    }

    const config = getOperationConfig();

    try {
        const nodeData = {
            workflow_id: workflowId,
            name: name,
            operation_type: operationType,
            operation_config: config
        };

        if (datasetId) {
            nodeData.input_dataset_id = datasetId;
        }

        const response = await fetch(`${API_BASE}/nodes/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(nodeData)
        });

        if (!response.ok) throw new Error('Failed to create node');

        const node = await response.json();
        alert(`Node created successfully! ID: ${node.id}`);

        // Clear form
        document.getElementById('nodeName').value = '';
        document.getElementById('operationType').value = '';
        document.getElementById('inputDataset').value = '';
        document.getElementById('operationConfig').classList.add('hidden');

        // Reload workflow nodes
        await loadCurrentWorkflowNodes(workflowId);

        // Update builder workflow select
        await populateBuilderWorkflowSelect();

    } catch (error) {
        alert(`Error creating node: ${error.message}`);
    }
}

async function connectWorkflowNodes() {
    const workflowId = document.getElementById('builderWorkflowSelect').value;
    const fromNodeId = document.getElementById('fromNode').value;
    const toNodeId = document.getElementById('toNode').value;

    if (!fromNodeId || !toNodeId) {
        alert('Please select both nodes to connect');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/workflows/${workflowId}/edges`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                from_node_id: fromNodeId,
                to_node_id: toNodeId
            })
        });

        if (!response.ok) throw new Error('Failed to create edge');

        alert('Nodes connected successfully!');

        // Reload workflow nodes
        await loadCurrentWorkflowNodes(workflowId);

    } catch (error) {
        alert(`Error connecting nodes: ${error.message}`);
    }
}

async function populateBuilderWorkflowSelect() {
    try {
        const response = await fetch(`${API_BASE}/workflows/`);
        const workflows = await response.json();

        const select = document.getElementById('builderWorkflowSelect');
        const currentValue = select.value;
        select.innerHTML = '<option value="">Select a workflow...</option>' +
            workflows.map(wf => `<option value="${wf.id}">${wf.name}</option>`).join('');

        if (currentValue) {
            select.value = currentValue;
        }
    } catch (error) {
        console.error('Error loading workflows:', error);
    }
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
    if (!workflowId) {
        document.getElementById('workflowActions').classList.add('hidden');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/workflows/${workflowId}/dag`);
        const dag = await response.json();

        // Get workflow details
        const workflowResponse = await fetch(`${API_BASE}/workflows/${workflowId}`);
        const workflow = await workflowResponse.json();

        currentWorkflow = workflowId;
        currentDAG = dag;

        // Show workflow actions and status
        document.getElementById('workflowActions').classList.remove('hidden');
        const statusDiv = document.getElementById('workflowStatus');
        statusDiv.innerHTML = `
            <span class="font-semibold">Status:</span>
            <span class="${getStatusColor(workflow.status)}">${workflow.status}</span>
            <span class="ml-4 text-gray-600">Nodes: ${dag.nodes.length}</span>
            <span class="ml-4 text-gray-600">Completed: ${dag.nodes.filter(n => n.status === 'completed').length}</span>
        `;

        // Render DAG
        renderDAG(dag);

        // Populate node select
        const nodeSelect = document.getElementById('nodeSelect');
        nodeSelect.innerHTML = '<option value="">Select a node...</option>' +
            dag.nodes.map(node => `<option value="${node.id}">${node.name}</option>`).join('');

        // Populate comparison node checkboxes
        const comparisonNodeSelect = document.getElementById('comparisonNodeSelect');
        comparisonNodeSelect.innerHTML = dag.nodes.map(node => `
            <label class="flex items-center">
                <input type="checkbox" class="comparison-node-checkbox mr-2" value="${node.id}">
                <span>${node.name} (${node.operation_type})</span>
            </label>
        `).join('');

        // Load all node plots
        loadAllNodePlots(dag);

        // Load initial comparison (first 2 completed nodes)
        updateComparisonPlots();
    } catch (error) {
        console.error('Error loading DAG:', error);
    }
}

async function executeCurrentWorkflow() {
    if (!currentWorkflow) return;
    await executeWorkflow(currentWorkflow);
    // Reload DAG to show updated status
    await loadWorkflowDAG();
}

async function rerunCurrentWorkflow() {
    if (!confirm('Re-execute this workflow? This will recompute all nodes.')) return;
    await executeCurrentWorkflow();
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

    // Make nodes clickable
    nodes.style('cursor', 'pointer')
        .on('click', (event, d) => {
            event.stopPropagation();
            selectNodeInDAG(d.id);
        })
        .on('mouseover', function() {
            d3.select(this).select('rect')
                .attr('stroke-width', 3);
        })
        .on('mouseout', function() {
            d3.select(this).select('rect')
                .attr('stroke-width', 2);
        });
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

    const channelId = parseInt(document.getElementById('channelSelect').value) || 0;

    try {
        const response = await fetch(`${API_BASE}/nodes/${nodeId}/plot?channel_id=${channelId}&limit=1000`);
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
        document.getElementById('plotViz').innerHTML = '<p class="text-red-500">Error loading plot. Node may not have output data yet.</p>';
    }
}

function selectNodeInDAG(nodeId) {
    // Update the node selector
    document.getElementById('nodeSelect').value = nodeId;
    // Load the plot for this node
    loadPlot();
    // Scroll to the plot visualization
    document.getElementById('plotViz').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function loadAllNodePlots(dag) {
    const container = document.getElementById('allNodePlots');
    container.innerHTML = '';

    // Get all nodes (completed or not - show them all with status)
    const nodes = dag.nodes;

    if (nodes.length === 0) {
        container.innerHTML = '<p class="text-gray-500 col-span-full">No nodes in workflow yet.</p>';
        return;
    }

    for (const node of nodes) {
        const plotDiv = document.createElement('div');
        plotDiv.className = 'border border-gray-200 rounded p-3';
        plotDiv.id = `snapshot-${node.id}`;

        const header = document.createElement('div');
        header.className = 'font-semibold mb-2 text-sm';
        header.innerHTML = `${node.name} <span class="${getStatusColor(node.status)} text-xs">(${node.status})</span>`;
        plotDiv.appendChild(header);

        if (node.status === 'completed') {
            try {
                const response = await fetch(`${API_BASE}/nodes/${node.id}/plot?channel_id=0&limit=500`);
                const plotData = await response.json();

                const miniPlotDiv = document.createElement('div');
                miniPlotDiv.id = `mini-plot-${node.id}`;
                plotDiv.appendChild(miniPlotDiv);

                const trace = {
                    x: plotData.x,
                    y: plotData.y,
                    type: 'scatter',
                    mode: 'lines',
                    name: node.name,
                    line: { width: 1 }
                };

                const layout = {
                    title: { text: plotData.title, font: { size: 10 } },
                    xaxis: { title: { text: plotData.x_label, font: { size: 9 } } },
                    yaxis: { title: { text: plotData.y_label, font: { size: 9 } } },
                    height: 200,
                    margin: { t: 30, r: 20, b: 40, l: 50 },
                    showlegend: false
                };

                Plotly.newPlot(miniPlotDiv, [trace], layout, { displayModeBar: false });
            } catch (error) {
                plotDiv.innerHTML += '<p class="text-sm text-red-500">Error loading plot data</p>';
            }
        } else {
            const statusMsg = document.createElement('p');
            statusMsg.className = 'text-sm text-gray-500 italic';
            statusMsg.textContent = node.status === 'pending' ? 'Not executed yet' : 'Execution in progress...';
            plotDiv.appendChild(statusMsg);
        }

        container.appendChild(plotDiv);
    }
}

async function updateComparisonPlots() {
    const container = document.getElementById('comparisonPlots');
    container.innerHTML = '';

    if (!currentDAG) {
        container.innerHTML = '<p class="text-gray-500 col-span-full">No workflow selected.</p>';
        return;
    }

    // Get selected nodes from checkboxes
    const checkboxes = document.querySelectorAll('.comparison-node-checkbox:checked');
    const selectedNodeIds = Array.from(checkboxes).map(cb => cb.value);

    if (selectedNodeIds.length === 0) {
        container.innerHTML = '<p class="text-gray-500 col-span-full">Select nodes to compare using the checkboxes above.</p>';
        return;
    }

    // Get the selected nodes
    const selectedNodes = currentDAG.nodes.filter(node => selectedNodeIds.includes(node.id));

    for (const node of selectedNodes) {
        if (node.status !== 'completed') {
            const plotDiv = document.createElement('div');
            plotDiv.className = 'border border-gray-200 rounded p-4 bg-gray-50';
            plotDiv.innerHTML = `
                <h3 class="font-semibold mb-2">${node.name}</h3>
                <p class="text-sm text-gray-500">Node status: ${node.status}</p>
                <p class="text-sm text-gray-500 italic">Execute the workflow to see data.</p>
            `;
            container.appendChild(plotDiv);
            continue;
        }

        try {
            const response = await fetch(`${API_BASE}/nodes/${node.id}/plot?channel_id=0&limit=500`);
            const plotData = await response.json();

            const plotDiv = document.createElement('div');
            plotDiv.id = `comparison-plot-${node.id}`;
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
            const errorDiv = document.createElement('div');
            errorDiv.className = 'border border-red-200 rounded p-4 bg-red-50';
            errorDiv.innerHTML = `
                <h3 class="font-semibold mb-2 text-red-700">${node.name}</h3>
                <p class="text-sm text-red-600">Error loading plot data</p>
            `;
            container.appendChild(errorDiv);
        }
    }
}

// Initialize
loadDatasets();
