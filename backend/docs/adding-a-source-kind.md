# Documentation & Extensibility Guide: Adding a Source Kind

This guide explains how to add a new source kind to Findr without changing any existing core code, routers, services, or database schemas.

## Architecture Rule
**Open/Closed Principle:** New features are new modules, not edits to old ones. Adding a data source (e.g., PostgreSQL, SQLite, MongoDB, Google Sheets) requires:
1. A new config model (member of `SourceConfig`).
2. A new connector class implementing the `SourceConnector` protocol.
3. One `register(...)` call in `container.py`.

---

## Step-by-Step Guide

### Step 1: Create the Config Model
Create `src/app/modules/sources/configs/my_kind.py` (or add to `configs.py`):

```python
from typing import Literal
from pydantic import BaseModel, field_validator

class MyKindConfig(BaseModel):
    kind: Literal["my_kind"]
    connection_string: str

    @field_validator("connection_string")
    @classmethod
    def validate_conn(cls, v: str) -> str:
        if not v.startswith("myprotocol://"):
            raise ValueError("Invalid connection string protocol")
        return v

    def identity(self) -> str:
        """Normalized identity for duplicate registration checks."""
        return f"my_kind:{self.connection_string.lower()}"
```

Add `MyKindConfig` to the `SourceConfig` discriminated union in `configs.py`:
```python
SourceConfig = Annotated[CsvConfig | XlsxConfig | MyKindConfig, Field(discriminator="kind")]
```

### Step 2: Implement the Connector
Create `src/app/modules/sources/connectors/my_kind.py`:

```python
from typing import ClassVar
from pydantic import BaseModel
from src.app.modules.sources.configs import MyKindConfig
from src.app.modules.sources.protocols import Capability, SourceConnector, SourceSchema

class MyKindConnector(SourceConnector):
    kind: ClassVar[str] = "my_kind"
    capabilities: ClassVar[Capability] = Capability.READ | Capability.SQL
    config_model: ClassVar[type[BaseModel]] = MyKindConfig

    async def validate(self, config: BaseModel) -> None:
        if not isinstance(config, MyKindConfig):
            raise ValueError("Invalid config")
        # Validate connection works

    async def get_schema(self, config: BaseModel) -> SourceSchema:
        # Return normalized schema
        return SourceSchema(entities=[...])

    async def fingerprint(self, config: BaseModel) -> str:
        # Return content hash or status hash
        return "hash-value"
```

### Step 3: Register in Container
In `src/app/container.py`:

```python
from src.app.modules.sources.connectors.my_kind import MyKindConnector

connector_registry.register("my_kind", MyKindConnector())
```

### Step 4: Test
That's it! You can now send `POST /api/v1/sources` with `kind: "my_kind"` and it will be fully supported across list, get, update, delete, schema inspection, and `/api/v1/source-kinds`.
