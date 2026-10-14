"""XLSX source connector using DuckDB."""

import os
from typing import ClassVar

import duckdb
from pydantic import BaseModel

from src.app.modules.sources.configs import XlsxConfig
from src.app.modules.sources.connectors.base import BaseConnector
from src.app.modules.sources.protocols import Capability, SourceSchema


class XlsxConnector(BaseConnector):
    """XLSX source connector."""

    kind: ClassVar[str] = "xlsx"
    capabilities: ClassVar[Capability] = Capability.READ
    config_model: ClassVar[type[BaseModel]] = XlsxConfig

    async def validate(self, config: BaseModel) -> None:
        """Validate that the XLSX file exists, is readable, and can be parsed.

        Args:
            config: XlsxConfig instance.

        Raises:
            ValueError: If file is missing, unreadable, or invalid XLSX.
        """
        if not isinstance(config, XlsxConfig):
            raise ValueError("Invalid config type for XlsxConnector")

        # Check path exists and is readable
        path_obj = self._validate_path_exists(config.path)

        # Try parsing with DuckDB (requires spatial or excel extension, or standard read)
        try:
            path_str = str(path_obj).replace("'", "''")

            # Check if spatial/excel extension is needed or available
            # DuckDB reads excel via spatial extension or read_xlsx
            query = f"SELECT * FROM st_read('{path_str}') LIMIT 5"
            try:
                duckdb.sql(query)
            except Exception:
                # Fallback or install spatial extension if possible
                try:
                    duckdb.sql("INSTALL spatial; LOAD spatial;")
                    duckdb.sql(query)
                except Exception as ex:
                    raise ValueError(
                        f"DuckDB cannot read Excel file. Ensure spatial extension is available: {ex}"
                    )
        except Exception as e:
            raise ValueError(f"Failed to parse XLSX file {config.path}: {e}")

    async def get_schema(self, config: BaseModel) -> SourceSchema:
        """Get normalized schema from XLSX file using DuckDB.

        Args:
            config: XlsxConfig instance.

        Returns:
            SourceSchema: Normalized schema with entities and fields.

        Raises:
            ValueError: If schema cannot be determined.
        """
        if not isinstance(config, XlsxConfig):
            raise ValueError("Invalid config type for XlsxConnector")

        path_obj = self._validate_path_exists(config.path)
        path_str = str(path_obj).replace("'", "''")

        try:
            sheet_filter = f" WHERE sheet_name = '{config.sheet}'" if config.sheet else ""

            describe_query = f"DESCRIBE SELECT * FROM st_read('{path_str}'){sheet_filter}"
            columns = duckdb.sql(describe_query).fetchall()

            sample_query = f"SELECT * FROM st_read('{path_str}'){sheet_filter} LIMIT 5"
            sample_df = duckdb.sql(sample_query).df()

            fields = []
            for col in columns:
                col_name = col[0]
                col_type = col[1]

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

            entity_name = config.sheet or path_obj.stem
            entity = SourceSchema.Entity(name=entity_name, fields=fields)
            return SourceSchema(entities=[entity])

        except Exception as e:
            raise ValueError(f"Failed to get schema for XLSX {config.path}: {e}")

    async def fingerprint(self, config: BaseModel) -> str:
        """Compute content hash for XLSX file.

        Args:
            config: XlsxConfig instance.

        Returns:
            str: SHA-256 hex digest.
        """
        if not isinstance(config, XlsxConfig):
            raise ValueError("Invalid config type for XlsxConnector")

        path_obj = self._validate_path_exists(config.path)
        stat = path_obj.stat()
        if stat.st_size > 10 * 1024 * 1024:
            return self._compute_fast_fingerprint(str(path_obj))

        return self._compute_sha256(str(path_obj))
