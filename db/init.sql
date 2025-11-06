-- Time Series Data Management Platform - Database Schema
-- This schema tracks metadata for datasets, workflows, and computation graphs

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Datasets table: tracks uploaded time series datasets
CREATE TABLE IF NOT EXISTS datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    file_location VARCHAR(500) NOT NULL,  -- MinIO object key
    schema_info JSONB,  -- Column definitions, data types
    row_count BIGINT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    channel_count INTEGER,
    sample_rate FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflows table: represents computation graphs
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft',  -- draft, running, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Nodes table: individual operations in a workflow
CREATE TABLE IF NOT EXISTS nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    operation_type VARCHAR(100) NOT NULL,  -- fft, filter, unit_conversion, custom
    operation_config JSONB,  -- Operation-specific parameters
    input_dataset_id UUID REFERENCES datasets(id),
    output_dataset_id UUID REFERENCES datasets(id),
    status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Edges table: connections between nodes in the DAG
CREATE TABLE IF NOT EXISTS edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    from_node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    to_node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workflow_id, from_node_id, to_node_id)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_nodes_workflow_id ON nodes(workflow_id);
CREATE INDEX IF NOT EXISTS idx_edges_workflow_id ON edges(workflow_id);
CREATE INDEX IF NOT EXISTS idx_edges_from_node ON edges(from_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_to_node ON edges(to_node_id);
CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON datasets(created_at);
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_datasets_updated_at BEFORE UPDATE ON datasets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_nodes_updated_at BEFORE UPDATE ON nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert a sample dataset for testing (will be replaced by actual data)
-- This is just a placeholder to verify the schema works
COMMENT ON TABLE datasets IS 'Stores metadata for time series datasets stored in MinIO';
COMMENT ON TABLE workflows IS 'Represents computation graphs (DAGs) for data processing';
COMMENT ON TABLE nodes IS 'Individual operations/transformations in a workflow';
COMMENT ON TABLE edges IS 'Connections between nodes forming the DAG structure';
