"""API routes for dataset management."""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pathlib import Path
import pandas as pd
import logging

from src.database import get_db_session
from src.models import Dataset
from src.api.schemas import DatasetCreate, DatasetResponse, DataPreview
from src.data_layer import MinIOClient, DuckDBClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db_session)
):
    """Upload a time series dataset (CSV file).

    Args:
        file: CSV file to upload
        name: Dataset name (defaults to filename)
        description: Optional description
        db: Database session

    Returns:
        Created dataset metadata
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    try:
        # Save file temporarily
        temp_path = Path(f"/tmp/{file.filename}")
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Load CSV to analyze
        df = pd.read_csv(temp_path, parse_dates=['timestamp'] if 'timestamp' in pd.read_csv(temp_path, nrows=1).columns else [])

        # Upload to MinIO
        minio_client = MinIOClient()
        object_name = f"datasets/{file.filename}"
        minio_client.upload_file(temp_path, object_name)

        # Extract metadata
        row_count = len(df)
        channel_count = df['channel_id'].nunique() if 'channel_id' in df.columns else None

        start_time = None
        end_time = None
        sample_rate = None

        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            start_time = df['timestamp'].min()
            end_time = df['timestamp'].max()

            # Calculate sample rate
            time_diffs = df['timestamp'].diff().dt.total_seconds().dropna()
            if len(time_diffs) > 0:
                sample_rate = float(1.0 / time_diffs.mean())

        # Create dataset record
        dataset = Dataset(
            name=name or file.filename,
            description=description,
            file_location=object_name,
            row_count=int(row_count) if row_count is not None else None,
            start_time=start_time,
            end_time=end_time,
            channel_count=int(channel_count) if channel_count is not None else None,
            sample_rate=sample_rate
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        logger.info(f"Uploaded dataset {dataset.id}: {dataset.name}")

        return dataset

    except Exception as e:
        logger.error(f"Error uploading dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[DatasetResponse])
def list_datasets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """List all datasets.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of datasets
    """
    datasets = db.query(Dataset).offset(skip).limit(limit).all()
    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Get dataset by ID.

    Args:
        dataset_id: Dataset UUID
        db: Database session

    Returns:
        Dataset metadata
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.get("/{dataset_id}/preview", response_model=DataPreview)
def preview_dataset(
    dataset_id: UUID,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """Get preview of dataset.

    Args:
        dataset_id: Dataset UUID
        limit: Number of rows to preview
        db: Database session

    Returns:
        Data preview
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        # Download from MinIO
        minio_client = MinIOClient()
        temp_path = Path(f"/tmp/preview_{dataset_id}.csv")
        minio_client.download_file(dataset.file_location, temp_path)

        # Load and preview
        df = pd.read_csv(temp_path, nrows=limit)

        return DataPreview(
            columns=df.columns.tolist(),
            data=df.to_dict('records'),
            total_rows=dataset.row_count or 0,
            preview_rows=len(df)
        )

    except Exception as e:
        logger.error(f"Error previewing dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Delete a dataset.

    Args:
        dataset_id: Dataset UUID
        db: Database session
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        # Delete from MinIO
        minio_client = MinIOClient()
        minio_client.delete_object(dataset.file_location)

        # Delete from database
        db.delete(dataset)
        db.commit()

        logger.info(f"Deleted dataset {dataset_id}")

    except Exception as e:
        logger.error(f"Error deleting dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))
