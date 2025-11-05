"""DuckDB client with Ibis integration for time series operations."""

import duckdb
import ibis
from ibis import _
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from src.config import get_settings

logger = logging.getLogger(__name__)


class DuckDBClient:
    """Client for DuckDB operations using Ibis."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize DuckDB client.

        Args:
            db_path: Path to DuckDB file (None for in-memory)
        """
        settings = get_settings()
        self.db_path = db_path or settings.duckdb_path

        # Ensure directory exists
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Create Ibis connection
        self.con = ibis.duckdb.connect(self.db_path)
        logger.info(f"Connected to DuckDB at: {self.db_path}")

    def load_csv(
        self,
        csv_path: str,
        table_name: str,
        schema: Optional[Dict[str, str]] = None
    ) -> ibis.expr.types.Table:
        """Load CSV file into DuckDB table.

        Args:
            csv_path: Path to CSV file
            table_name: Name for the table
            schema: Optional schema definition

        Returns:
            Ibis table expression
        """
        try:
            # Read CSV into pandas first for easier handling
            df = pd.read_csv(csv_path, parse_dates=['timestamp'])

            # Create or replace table
            self.con.create_table(
                table_name,
                df,
                overwrite=True
            )

            logger.info(f"Loaded {len(df)} rows from {csv_path} into table '{table_name}'")
            return self.con.table(table_name)

        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise

    def create_table_from_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        overwrite: bool = True
    ) -> ibis.expr.types.Table:
        """Create table from pandas DataFrame.

        Args:
            df: Pandas DataFrame
            table_name: Name for the table
            overwrite: Whether to overwrite existing table

        Returns:
            Ibis table expression
        """
        try:
            self.con.create_table(
                table_name,
                df,
                overwrite=overwrite
            )
            logger.info(f"Created table '{table_name}' with {len(df)} rows")
            return self.con.table(table_name)

        except Exception as e:
            logger.error(f"Error creating table: {e}")
            raise

    def get_table(self, table_name: str) -> ibis.expr.types.Table:
        """Get table by name.

        Args:
            table_name: Name of the table

        Returns:
            Ibis table expression
        """
        return self.con.table(table_name)

    def query(self, sql: str) -> pd.DataFrame:
        """Execute SQL query and return results.

        Args:
            sql: SQL query string

        Returns:
            Query results as pandas DataFrame
        """
        try:
            result = self.con.sql(sql).execute()
            return result
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def get_channel_data(
        self,
        table_name: str,
        channel_id: int,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Get data for a specific channel.

        Args:
            table_name: Name of the table
            channel_id: Channel ID to filter
            start_time: Optional start timestamp
            end_time: Optional end timestamp
            limit: Optional row limit

        Returns:
            Filtered data as pandas DataFrame
        """
        try:
            table = self.get_table(table_name)

            # Filter by channel
            filtered = table.filter(_.channel_id == channel_id)

            # Filter by time range if provided
            if start_time:
                filtered = filtered.filter(_.timestamp >= start_time)
            if end_time:
                filtered = filtered.filter(_.timestamp <= end_time)

            # Apply limit if provided
            if limit:
                filtered = filtered.limit(limit)

            # Order by timestamp
            filtered = filtered.order_by(_.timestamp)

            return filtered.execute()

        except Exception as e:
            logger.error(f"Error getting channel data: {e}")
            raise

    def get_all_channels(
        self,
        table_name: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Get data for all channels.

        Args:
            table_name: Name of the table
            start_time: Optional start timestamp
            end_time: Optional end timestamp
            limit: Optional row limit per channel

        Returns:
            Data as pandas DataFrame
        """
        try:
            table = self.get_table(table_name)

            # Filter by time range if provided
            if start_time:
                table = table.filter(_.timestamp >= start_time)
            if end_time:
                table = table.filter(_.timestamp <= end_time)

            # Apply limit if provided
            if limit:
                table = table.limit(limit)

            # Order by timestamp and channel
            table = table.order_by([_.timestamp, _.channel_id])

            return table.execute()

        except Exception as e:
            logger.error(f"Error getting all channels data: {e}")
            raise

    def get_statistics(self, table_name: str, channel_id: Optional[int] = None) -> Dict[str, Any]:
        """Get basic statistics for a dataset.

        Args:
            table_name: Name of the table
            channel_id: Optional channel ID to filter

        Returns:
            Dictionary with statistics
        """
        try:
            table = self.get_table(table_name)

            if channel_id is not None:
                table = table.filter(_.channel_id == channel_id)

            stats = {
                'count': table.count().execute(),
                'mean': table.value.mean().execute(),
                'std': table.value.std().execute(),
                'min': table.value.min().execute(),
                'max': table.value.max().execute(),
            }

            # Get time range
            time_stats = table.aggregate([
                _.timestamp.min().name('start_time'),
                _.timestamp.max().name('end_time')
            ]).execute()

            stats.update({
                'start_time': time_stats['start_time'].iloc[0],
                'end_time': time_stats['end_time'].iloc[0]
            })

            if channel_id is None:
                stats['num_channels'] = table.channel_id.nunique().execute()

            return stats

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise

    def list_tables(self) -> List[str]:
        """List all tables in the database.

        Returns:
            List of table names
        """
        return self.con.list_tables()

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists.

        Args:
            table_name: Name of the table

        Returns:
            True if table exists
        """
        return table_name in self.list_tables()

    def drop_table(self, table_name: str):
        """Drop a table.

        Args:
            table_name: Name of the table to drop
        """
        try:
            self.con.drop_table(table_name, force=True)
            logger.info(f"Dropped table: {table_name}")
        except Exception as e:
            logger.error(f"Error dropping table: {e}")
            raise

    def close(self):
        """Close database connection."""
        if hasattr(self, 'con'):
            self.con.disconnect()
            logger.info("Closed DuckDB connection")
