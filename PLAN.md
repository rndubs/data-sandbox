# Time Series Data Management Platform - POC Implementation Plan

## Overview
A proof-of-concept platform for managing gigabytes of time series data with reproducible computation graphs (DAGs), visualization, and a Python SDK.

## Architecture

### Components
1. **Storage Layer**
   - MinIO: S3-compatible storage for raw CSV files
   - DuckDB: In-process analytical database for time series operations
   - Postgres: Metadata storage (workflows, nodes, datasets, lineage)

2. **Computation Layer**
   - Prefect: Workflow orchestration and task management
   - Ibis: SQL abstraction layer over DuckDB
   - Pre-defined operations: FFT, unit conversion, filtering
   - Support for custom Python functions

3. **API Layer**
   - FastAPI: REST API for workflow management and execution
   - Endpoints for DAG operations, data querying, visualization

4. **Client Layer**
   - Web UI: React-based dashboard
   - DAG visualization using D3.js or similar
   - Plot visualization using Plotly.js
   - Workflow builder interface

5. **Python SDK**
   - High-level abstraction layer
   - User-friendly API hiding REST/storage details

## Implementation Phases

### Phase 1: Core Infrastructure ✓ (In Progress)
**Goal**: Set up containerized environment and project structure

- [ ] Create project directory structure
- [ ] Docker Compose configuration
  - [ ] MinIO service
  - [ ] Postgres service
  - [ ] Prefect server (optional for POC)
  - [ ] API service
  - [ ] Web client service
- [ ] Initialize Python project with dependencies
- [ ] Create .env file for configuration

**Deliverables**:
- `docker-compose.yml`
- `requirements.txt` or `pyproject.toml`
- Basic project structure

---

### Phase 2: Database Schemas & Storage Setup
**Goal**: Define metadata schemas and initialize storage

- [ ] Postgres schema design
  - [ ] `datasets` table (id, name, location, schema, created_at)
  - [ ] `workflows` table (id, name, description, created_at)
  - [ ] `nodes` table (id, workflow_id, operation_type, config, input_dataset_id, output_dataset_id)
  - [ ] `edges` table (id, workflow_id, from_node_id, to_node_id)
- [ ] Create Alembic migrations or SQL scripts
- [ ] MinIO bucket initialization script
- [ ] DuckDB file location and initialization

**Deliverables**:
- `db/schema.sql` or Alembic migrations
- `db/init_storage.py`

---

### Phase 3: Sample Data Generation
**Goal**: Create realistic demo dataset

- [ ] Generate synthetic time series data
  - 10 channels
  - 100 seconds at 1kHz (100,000 samples per channel)
  - CSV format with columns: timestamp, channel_id, value
- [ ] Upload to MinIO
- [ ] Register in Postgres metadata

**Deliverables**:
- `scripts/generate_sample_data.py`
- Sample CSV files in MinIO

---

### Phase 4: Data Layer Implementation
**Goal**: Build data access and query layer

- [ ] DuckDB connector module
- [ ] Ibis integration for DataFrame operations
- [ ] Data loader: MinIO → DuckDB
- [ ] Query functions:
  - Load dataset by ID
  - Get time range
  - Get channel data
- [ ] Basic operations test

**Deliverables**:
- `src/data_layer/duckdb_client.py`
- `src/data_layer/data_loader.py`
- `tests/test_data_layer.py`

---

### Phase 5: Computation Layer
**Goal**: Implement operations and Prefect integration

- [ ] Define operation interface/base class
- [ ] Implement core operations:
  - [ ] FFT operation (time → frequency domain)
  - [ ] Unit conversion operation
  - [ ] Filter operation (low-pass, high-pass, band-pass)
- [ ] Prefect task wrappers
- [ ] DAG executor:
  - Parse workflow from Postgres
  - Build Prefect flow
  - Execute and track results
- [ ] Custom operation support

**Deliverables**:
- `src/operations/base.py`
- `src/operations/fft.py`
- `src/operations/filter.py`
- `src/operations/unit_conversion.py`
- `src/workflow/executor.py`
- `tests/test_operations.py`

---

### Phase 6: API Layer
**Goal**: REST API for platform interaction

- [ ] FastAPI application setup
- [ ] Endpoints:
  - `POST /datasets/upload` - Upload CSV to MinIO
  - `GET /datasets/{id}` - Get dataset metadata
  - `GET /datasets/{id}/preview` - Get sample data
  - `POST /workflows` - Create new workflow
  - `GET /workflows/{id}` - Get workflow details
  - `GET /workflows/{id}/dag` - Get DAG structure
  - `POST /workflows/{id}/nodes` - Add node to workflow
  - `POST /workflows/{id}/execute` - Execute workflow
  - `GET /nodes/{id}/data` - Get output data from node
  - `GET /nodes/{id}/plot` - Get plot data for visualization
- [ ] Error handling and validation
- [ ] API documentation (OpenAPI/Swagger)

**Deliverables**:
- `src/api/main.py`
- `src/api/routes/`
- `tests/test_api.py`

---

### Phase 7: Python SDK
**Goal**: User-friendly abstraction layer

- [ ] SDK client class
- [ ] Methods:
  - `upload_dataset(file_path)`
  - `create_workflow(name)`
  - `add_operation(workflow_id, operation_type, config)`
  - `execute_workflow(workflow_id)`
  - `get_results(node_id)`
  - `visualize_dag(workflow_id)`
- [ ] Context manager support
- [ ] Example notebooks/scripts

**Deliverables**:
- `sdk/client.py`
- `examples/basic_workflow.py`
- `examples/custom_operation.py`
- `README.md` for SDK

---

### Phase 8: Web Client
**Goal**: Visual workflow builder and visualization

- [ ] Frontend setup (React + Vite or simple HTML/JS)
- [ ] Components:
  - [ ] Workflow list view
  - [ ] DAG visualization (using reactflow or D3.js)
  - [ ] Node configuration panel
  - [ ] Plot viewer (Plotly.js)
  - [ ] Side-by-side comparison view
- [ ] Workflow builder:
  - Drag-and-drop operations
  - Configure operation parameters
  - Connect nodes
  - Execute workflow
- [ ] Basic styling (Tailwind CSS or similar)

**Deliverables**:
- `web/src/`
- `web/package.json`
- `web/Dockerfile`

---

### Phase 9: Integration & Testing
**Goal**: End-to-end validation

- [ ] Integration test suite:
  - [ ] Upload dataset → Execute FFT → Visualize
  - [ ] Multi-step workflow (filter → FFT → unit conversion)
  - [ ] Custom operation workflow
- [ ] Docker Compose smoke tests
- [ ] Example workflows for demo:
  - Signal processing pipeline
  - Multi-channel analysis
- [ ] Documentation:
  - [ ] Setup instructions (README.md)
  - [ ] Architecture diagram
  - [ ] API documentation
  - [ ] SDK examples

**Deliverables**:
- `tests/integration/`
- `examples/demo_workflows.py`
- `README.md`
- `ARCHITECTURE.md`

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Storage | MinIO (S3-compatible) |
| Time Series DB | DuckDB + Ibis |
| Metadata DB | PostgreSQL |
| Workflow Engine | Prefect |
| API | FastAPI |
| Web Client | React + Plotly.js |
| Containerization | Docker Compose |
| Python SDK | Python 3.10+ |

## Success Criteria

- ✅ Upload CSV time series data
- ✅ Create workflow with 3+ operations
- ✅ Execute workflow and track lineage
- ✅ Visualize DAG in web UI
- ✅ View side-by-side plots at each stage
- ✅ Use Python SDK without knowing REST API
- ✅ Add custom operation via Python function
- ✅ Run entire stack with `docker-compose up`

## Out of Scope (for POC)

- Authentication/authorization
- Production deployment configuration
- Horizontal scaling
- Advanced error recovery
- Real-time streaming data
- Complex permission models
- Multi-tenancy
- Production-grade monitoring/logging

## Timeline Estimate

Approximate development time per phase:
- Phase 1-3: 2-3 hours (infrastructure + data)
- Phase 4-5: 3-4 hours (data + computation layers)
- Phase 6-7: 2-3 hours (API + SDK)
- Phase 8: 3-4 hours (web client)
- Phase 9: 1-2 hours (testing + docs)

**Total**: ~12-16 hours for minimal POC

---

## Next Steps

1. ✓ Set up project structure
2. Create Docker Compose configuration
3. Implement database schemas
4. Generate sample data
5. Build data layer
6. Implement operations
7. Create API
8. Develop SDK
9. Build web client
10. Test and document

---

*Last Updated: 2025-11-05*
