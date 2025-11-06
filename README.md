# Time Series Data Management Platform - POC

A proof-of-concept platform for managing gigabytes of time series data with reproducible computation graphs (DAGs), visualization capabilities, and a Python SDK.

## Features

- **Time Series Data Storage**: Store and manage large time series datasets using MinIO (S3-compatible) and DuckDB
- **Computation Graphs**: Build reproducible workflows as DAGs with operation lineage tracking
- **Pre-built Operations**: FFT, filtering (low-pass, high-pass, band-pass), unit conversion
- **Custom Operations**: Extend the platform with custom Python functions
- **Visualization**: Web-based DAG visualization and side-by-side data plots
- **Python SDK**: High-level abstraction layer for easy interaction without knowing REST APIs
- **Containerized**: Everything runs in Docker containers for easy deployment

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Client                           │
│              (DAG Viz + Plot Viz + Workflow Builder)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
│              (REST API for workflows & data)                │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   MinIO      │  │  PostgreSQL  │  │   DuckDB     │
    │ (Raw Data)   │  │  (Metadata)  │  │ (Analytics)  │
    └──────────────┘  └──────────────┘  └──────────────┘
```

**Components**:
- **MinIO**: S3-compatible object storage for raw CSV files
- **PostgreSQL**: Metadata storage (workflows, nodes, datasets, lineage)
- **DuckDB**: In-process analytical database with Ibis interface
- **Prefect**: Workflow orchestration and task management
- **FastAPI**: REST API backend
- **Web Client**: Simple HTML/JS interface with Plotly and D3.js

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)
- 2GB+ free disk space

### 1. Start the Platform

```bash
# Build and start all services
docker-compose up --build -d

# Check service status
docker-compose ps
```

Services will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Web Client**: http://localhost:3000
- **MinIO Console**: http://localhost:9001

### 2. Generate Sample Data

```bash
# Generate sample time series dataset
python scripts/generate_sample_data.py
```

This creates `data/sample_timeseries.csv` with:
- 10 channels
- 100 seconds at 1kHz (1,000,000 total samples)
- Mix of sine waves, noise, and transient events

### 3. Run Example Workflow

```bash
# Install dependencies locally (for SDK)
pip install -e .

# Run example workflow
python examples/basic_workflow.py
```

This example:
1. Uploads the sample dataset
2. Creates a workflow with filter → FFT operations
3. Executes the workflow
4. Retrieves and displays results

## Usage

### Using the Python SDK

```python
from sdk.client import TimeSeriesClient

# Initialize client
client = TimeSeriesClient("http://localhost:8000")

# Upload dataset
dataset_id = client.upload_dataset(
    "data/sample_timeseries.csv",
    name="My Data"
)

# Create workflow
workflow_id = client.create_workflow("Signal Processing")

# Add operations
filter_node = client.add_operation(
    workflow_id,
    operation_type="filter",
    config={
        "filter_type": "lowpass",
        "cutoff": 50,
        "order": 4
    },
    dataset_id=dataset_id
)

fft_node = client.add_operation(
    workflow_id,
    operation_type="fft",
    config={"normalize": True}
)

# Connect operations
client.connect_nodes(workflow_id, filter_node, fft_node)

# Execute workflow
result = client.execute_workflow(workflow_id)

# Get results
fft_output = client.get_node_output(fft_node)
plot_data = client.get_node_plot(fft_node, channel_id=0)
```

### Using the Web Interface

1. Open http://localhost:3000
2. **Datasets Tab**: Upload and manage CSV files
3. **Workflows Tab**:
   - Create new workflows
   - Use the **Workflow Builder** to add operation nodes (filter, FFT, unit conversion, time shift)
   - Configure each operation with specific parameters
   - Connect nodes to build your processing pipeline
4. **Visualization Tab**:
   - View interactive workflow DAG (click nodes to view their data)
   - Execute or rerun workflows with one click
   - View individual node data with customizable channels
   - See all node data snapshots at once
   - Compare multiple nodes side-by-side with selective plotting

### Using the REST API

Access the interactive API documentation at http://localhost:8000/docs

Example API calls:

```bash
# Upload dataset
curl -X POST "http://localhost:8000/api/datasets/upload" \
  -F "file=@data/sample_timeseries.csv" \
  -F "name=Test Data"

# Create workflow
curl -X POST "http://localhost:8000/api/workflows/" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Workflow"}'

# Get workflow DAG
curl "http://localhost:8000/api/workflows/{workflow_id}/dag"
```

## Creating Workflows via Web UI

The web interface provides a complete workflow builder for creating data processing pipelines:

### Step-by-Step Workflow Creation:

1. **Upload Dataset** (Datasets Tab):
   - Click "Choose File" and select your CSV file
   - Click "Upload" to store the dataset

2. **Create Workflow** (Workflows Tab):
   - Enter a workflow name
   - Click "Create Workflow"

3. **Build Pipeline** (Workflow Builder):
   - Select your workflow from the dropdown
   - For each operation node:
     - Enter a descriptive name (e.g., "Low-pass Filter 50Hz")
     - Select operation type (Filter, FFT, Unit Conversion, Time Shift)
     - Configure operation-specific parameters
     - Select input dataset (for first node only)
     - Click "Add Node"
   - Connect nodes:
     - Select "From Node" (parent)
     - Select "To Node" (child)
     - Click "Connect Nodes"

4. **Execute Workflow** (Visualization Tab):
   - Select your workflow from the dropdown
   - View the DAG structure
   - Click "Execute" to run the workflow
   - Click "Rerun" to re-execute after changes

5. **View Results**:
   - Click any node in the DAG to view its output data
   - Scroll down to see all node snapshots
   - Select nodes to compare in the side-by-side plotter
   - Change channels to view different data streams

## Available Operations

### 1. FFT (Fast Fourier Transform)

Converts time-domain signals to frequency domain.

```python
{
    "operation_type": "fft",
    "config": {
        "window": "hann",      # Optional: hann, hamming, blackman
        "normalize": true      # Normalize magnitude
    }
}
```

### 2. Filter

Apply digital filters to time series.

```python
{
    "operation_type": "filter",
    "config": {
        "filter_type": "lowpass",  # lowpass, highpass, bandpass
        "cutoff": 50,              # Cutoff frequency (Hz)
        "order": 4                 # Filter order
    }
}
```

For bandpass filters:
```python
{
    "filter_type": "bandpass",
    "cutoff": [10, 100],  # [low, high] frequencies
    "order": 4
}
```

### 3. Unit Conversion

Convert units of time series values.

```python
{
    "operation_type": "unit_conversion",
    "config": {
        "conversion": "celsius_to_fahrenheit"
        # Supported: celsius_to_fahrenheit, meters_to_feet,
        # mps_to_mph, pa_to_psi, mv_to_v, scale, offset, etc.
    }
}
```

### 4. Custom Operations

Extend the platform with custom Python functions using the Prefect API (see examples).

## Data Format

Input CSV files should have the following structure:

```csv
timestamp,channel_id,value
2024-01-01 00:00:00.000,0,1.234
2024-01-01 00:00:00.001,0,1.245
2024-01-01 00:00:00.002,0,1.256
...
```

- **timestamp**: ISO format timestamp
- **channel_id**: Integer channel identifier
- **value**: Numeric value

## Development

### Project Structure

```
.
├── src/
│   ├── api/              # FastAPI application
│   ├── data_layer/       # DuckDB and MinIO clients
│   ├── operations/       # Time series operations
│   ├── workflow/         # Prefect workflow executor
│   ├── models.py         # SQLAlchemy models
│   ├── database.py       # Database connection
│   └── config.py         # Configuration
├── sdk/                  # Python SDK
├── web/                  # Web client
├── db/                   # Database schemas
├── scripts/              # Utility scripts
├── examples/             # Example workflows
├── tests/                # Test suite
├── docker-compose.yml    # Container orchestration
└── README.md
```

### Running Tests

```bash
# Install dev dependencies
pip install -e .[dev]

# Run tests
pytest tests/

# Run specific test
pytest tests/test_operations.py -v
```

### Adding Custom Operations

1. Create a new operation class in `src/operations/`:

```python
from src.operations.base import Operation

class MyOperation(Operation):
    @property
    def operation_type(self) -> str:
        return "my_operation"

    def _validate_config(self):
        # Validate configuration
        pass

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        # Transform data
        return transformed_data
```

2. Register in `src/operations/__init__.py`:

```python
OPERATIONS = {
    'my_operation': MyOperation,
    # ... existing operations
}
```

## Stopping the Platform

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v
```

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs api
docker-compose logs postgres
docker-compose logs minio

# Restart specific service
docker-compose restart api
```

### Database connection errors

```bash
# Ensure PostgreSQL is healthy
docker-compose ps postgres

# Reinitialize database
docker-compose down -v
docker-compose up -d
```

### Port conflicts

If ports 8000, 3000, 5432, or 9000 are in use:

1. Edit `docker-compose.yml`
2. Change port mappings (e.g., `8001:8000`)
3. Update `API_BASE` in `web/public/app.js`

## Performance Notes

This is a POC focused on demonstrating features, not production performance:

- DuckDB runs in-process (single file)
- No connection pooling optimization
- Minimal caching
- Synchronous workflow execution

For production use, consider:
- Distributed DuckDB or ClickHouse
- Redis caching layer
- Async workflow execution
- Horizontal scaling with Kubernetes

## License

MIT License - This is a proof of concept for demonstration purposes.

## Next Steps

After testing the POC, consider:

1. **Authentication**: Add user authentication and authorization
2. **Scheduling**: Add scheduled workflow execution
3. **Monitoring**: Add metrics and logging (Prometheus, Grafana)
4. **Scalability**: Move to distributed architecture
5. **UI Enhancement**: Build full-featured React application
6. **Data Validation**: Add schema validation and data quality checks
7. **Versioning**: Track dataset and operation versions

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review API docs: http://localhost:8000/docs
- Inspect database: Connect to PostgreSQL on port 5432

---

Built with FastAPI, DuckDB, Prefect, and ❤️
