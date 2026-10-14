"""CSV source connector using DuckDB."""

import os
from typing import ClassVar

import duckdb
from pydantic import BaseModel

from src.app.modules.sources.configs import CsvConfig
from src.app.modules.sources.connectors.base import BaseConnector
from src.app.modules.sources.protocols import Capability, SourceSchema


class CsvConnector(BaseConnector):
    """CSV source connector."""

    kind: ClassVar[str] = "csv"
    capabilities: ClassVar[Capability] = Capability.READ
    config_model: ClassVar[type[BaseModel]] = CsvConfig

    async def validate(self, config: BaseModel) -> None:
        """Validate that the CSV file exists, is readable, and can be parsed.

        Args:
            config: CsvConfig instance.

        Raises:
            ValueError: If file is missing, unreadable, or invalid CSV.
        """
        if not isinstance(config, CsvConfig):
            raise ValueError("Invalid config type for CsvConnector")

        # Check path exists and is readable
        path_obj = self._validate_path_exists(config.path)

        # Try parsing first few rows with DuckDB
        try:
            # Escape path for SQL string literal
            path_str = str(path_obj).replace("'", "''")
            query = (
                f"SELECT * FROM read_csv('{path_str}', "
                f"delim='{config.delimiter}', "
                f"encoding='{config.encoding}', "
                f"header={1 if config.header_row >= 0 else 0}, "
                f"sample_size=100) LIMIT 5"
            )
            duckdb.sql(query)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV file {config.path}: {e}")

    async def get_schema(self, config: BaseModel) -> SourceSchema:
        """Get normalized schema from CSV file using DuckDB.

        Args:
            config: CsvConfig instance.

        Returns:
            SourceSchema: Normalized schema with entities and fields.

        Raises:
            ValueError: If schema cannot be determined.
        """
        if not isinstance(config, CsvConfig):
            raise ValueError("Invalid config type for CsvConnector")

        path_obj = self._validate_path_exists(config.path)
        path_str = str(path_obj).replace("'", "''")

        try:
            # Get column types and names using DESCRIBE
            describe_query = (
                f"DESCRIBE SELECT * FROM read_csv('{path_str}', "
                f"delim='{config.delimiter}', "
                f"encoding='{config.encoding}', "
                f"header={1 if config.header_row >= 0 else 0})"
            )
            columns = duckdb.sql(describe_query).fetchall()

            # Get sample rows for sample values
            sample_query = (
                f"SELECT * FROM read_csv('{path_str}', "
                f"delim='{config.delimiter}', "
                f"encoding='{config.encoding}', "
                f"header={1 if config.header_row >= 0 else 0}) LIMIT 5"
            )
            sample_df = duckdb.sql(sample_query).df()

            fields = []
            for col in columns:
                col_name = col[0]
                col_type = col[1]

                # Get sample values for this column
                samples = []
                if col_name in sample_df.columns:
                    samples = sample_df[col_name].dropna().head(3).tolist()

                fields.append(
                    SourceSchema.Field(
                        name=str(col_name),
                        type=str(col_type).lower(),
                        nullable=True,
                        samples=samples,
                    )
                )

            # Use filename (without extension) as entity name
            entity_name = path_obj.stem

            entity = SourceSchema.Entity(name=entity_name, fields=fields)
            return SourceSchema(entities=[entity])

        except Exception as e:
            raise ValueError(f"Failed to get schema for CSV {config.path}: {e}")

    async def fingerprint(self, config: BaseModel) -> str:
        """Compute content hash for CSV file.

        Args:
            config: CsvConfig instance.

        Returns:
            str: SHA-256 hex digest.
        """
        if not isinstance(config, CsvConfig):
            raise ValueError("Invalid config type for CsvConnector")

        path_obj = self._validate_path_exists(config.path)

        # For large files (>10MB), use fast metadata fingerprint; otherwise hash contents
        stat = path_obj.stat()
        if stat.st_size > 10 * 1024 * 1024:
            return self._compute_fast_fingerprint(str(path_obj))

        return self._compute_sha256(str(path_obj))
