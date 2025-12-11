# Development Standards V9

> Standards #34-36: Data Import/Export, Email Templates, Offline/PWA Support

---

## Table of Contents

- [Standard #34: Data Import/Export](#standard-34-data-importexport)
- [Standard #35: Email Templates](#standard-35-email-templates)
- [Standard #36: Offline/PWA Support](#standard-36-offlinepwa-support)

---

## Standard #34: Data Import/Export

### 34.1 Overview

Data Import/Export memungkinkan user untuk mengimpor data bulk dari file eksternal dan mengekspor data sistem ke format yang dapat digunakan di aplikasi lain.

### 34.2 Import/Export Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATA IMPORT/EXPORT ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                          IMPORT FLOW                               │  │
│  │                                                                     │  │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐           │  │
│  │  │ Upload  │──►│ Validate│──►│Transform│──►│ Insert  │           │  │
│  │  │  File   │   │  Schema │   │  Data   │   │   DB    │           │  │
│  │  └─────────┘   └─────────┘   └─────────┘   └─────────┘           │  │
│  │       │             │             │             │                  │  │
│  │       ▼             ▼             ▼             ▼                  │  │
│  │  [CSV/XLSX]   [Validation   [Data Type    [Batch        ]         │  │
│  │               Errors]       Conversion]   Insert/Update]          │  │
│  │                                                                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                          EXPORT FLOW                               │  │
│  │                                                                     │  │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐           │  │
│  │  │ Query   │──►│ Filter  │──►│ Format  │──►│Download │           │  │
│  │  │  Data   │   │ & Sort  │   │  Output │   │  File   │           │  │
│  │  └─────────┘   └─────────┘   └─────────┘   └─────────┘           │  │
│  │       │             │             │             │                  │  │
│  │       ▼             ▼             ▼             ▼                  │  │
│  │  [Select     [User-defined  [CSV/XLSX/   [Stream or    ]         │  │
│  │   Fields]    Filters]       JSON]        Async Download]          │  │
│  │                                                                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 34.3 Supported Formats

| Format | Import | Export | Use Case |
|--------|--------|--------|----------|
| CSV | ✅ | ✅ | Simple tabular data, universal compatibility |
| XLSX | ✅ | ✅ | Excel users, multiple sheets, formatting |
| JSON | ✅ | ✅ | API integration, nested data |
| XML | ✅ | ✅ | Legacy system integration |

### 34.4 Database Schema

```sql
-- Import job tracking
CREATE TABLE import_jobs (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Job info
    entity_type VARCHAR(100) NOT NULL,  -- guests, rooms, inventory, etc.
    file_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size_bytes BIGINT,
    file_format VARCHAR(20) NOT NULL,

    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- pending, validating, validated, importing, completed, failed, cancelled

    -- Progress
    total_rows INTEGER,
    processed_rows INTEGER DEFAULT 0,
    success_rows INTEGER DEFAULT 0,
    error_rows INTEGER DEFAULT 0,
    skipped_rows INTEGER DEFAULT 0,

    -- Mapping configuration
    column_mapping JSONB NOT NULL,  -- {file_column: db_column}
    import_options JSONB DEFAULT '{}',  -- {skip_duplicates, update_existing, etc}

    -- Results
    error_details JSONB DEFAULT '[]',  -- [{row: 5, errors: [...]}]
    summary JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'validating', 'validated', 'importing',
        'completed', 'failed', 'cancelled'
    ))
);

-- Export job tracking
CREATE TABLE export_jobs (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Job info
    entity_type VARCHAR(100) NOT NULL,
    export_format VARCHAR(20) NOT NULL,
    file_name VARCHAR(500),
    file_path VARCHAR(1000),
    file_size_bytes BIGINT,

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- pending, processing, completed, failed, expired

    -- Configuration
    filters JSONB DEFAULT '{}',
    columns TEXT[],  -- Selected columns to export
    sort_by VARCHAR(100),
    sort_order VARCHAR(4) DEFAULT 'asc',

    -- Progress
    total_rows INTEGER,
    processed_rows INTEGER DEFAULT 0,

    -- Download
    download_url VARCHAR(2000),
    download_expires_at TIMESTAMP WITH TIME ZONE,
    download_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'processing', 'completed', 'failed', 'expired'
    ))
);

-- Import templates (saved mappings)
CREATE TABLE import_templates (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    entity_type VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    column_mapping JSONB NOT NULL,
    import_options JSONB DEFAULT '{}',
    validation_rules JSONB DEFAULT '{}',

    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    UNIQUE(organization_id, entity_type, name)
);

-- Indexes
CREATE INDEX idx_import_jobs_org ON import_jobs(organization_id);
CREATE INDEX idx_import_jobs_status ON import_jobs(status);
CREATE INDEX idx_export_jobs_org ON export_jobs(organization_id);
CREATE INDEX idx_export_jobs_status ON export_jobs(status);
```

### 34.5 Import Configuration

```python
# services/import_export/config.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

class ColumnType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    CURRENCY = "currency"
    ENUM = "enum"
    FOREIGN_KEY = "foreign_key"

@dataclass
class ColumnDefinition:
    """Definition of an importable column"""
    name: str
    label: str
    type: ColumnType
    required: bool = False
    unique: bool = False
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    enum_values: Optional[List[str]] = None
    foreign_key_table: Optional[str] = None
    foreign_key_column: Optional[str] = None
    default_value: Any = None
    transform: Optional[str] = None  # Function name for transformation

@dataclass
class ImportConfig:
    """Configuration for an entity type import"""
    entity_type: str
    table_name: str
    display_name: str
    columns: List[ColumnDefinition]
    required_permission: str
    max_rows: int = 10000
    batch_size: int = 500
    allow_update: bool = True
    unique_columns: List[str] = field(default_factory=list)
    pre_import_hook: Optional[str] = None
    post_import_hook: Optional[str] = None

# Import configurations for different entities
IMPORT_CONFIGS: Dict[str, ImportConfig] = {
    "guests": ImportConfig(
        entity_type="guests",
        table_name="guests",
        display_name="Guests",
        required_permission="guests.import",
        unique_columns=["email", "id_number"],
        columns=[
            ColumnDefinition(
                name="name",
                label="Full Name",
                type=ColumnType.STRING,
                required=True,
                max_length=200
            ),
            ColumnDefinition(
                name="email",
                label="Email",
                type=ColumnType.EMAIL,
                required=True,
                unique=True
            ),
            ColumnDefinition(
                name="phone",
                label="Phone Number",
                type=ColumnType.PHONE,
                required=False
            ),
            ColumnDefinition(
                name="id_type",
                label="ID Type",
                type=ColumnType.ENUM,
                enum_values=["KTP", "PASSPORT", "SIM", "OTHER"]
            ),
            ColumnDefinition(
                name="id_number",
                label="ID Number",
                type=ColumnType.STRING,
                max_length=50
            ),
            ColumnDefinition(
                name="nationality",
                label="Nationality",
                type=ColumnType.STRING,
                max_length=100,
                default_value="Indonesia"
            ),
            ColumnDefinition(
                name="date_of_birth",
                label="Date of Birth",
                type=ColumnType.DATE
            ),
            ColumnDefinition(
                name="address",
                label="Address",
                type=ColumnType.STRING,
                max_length=500
            ),
            ColumnDefinition(
                name="vip_level",
                label="VIP Level",
                type=ColumnType.ENUM,
                enum_values=["NONE", "SILVER", "GOLD", "PLATINUM"],
                default_value="NONE"
            ),
        ]
    ),

    "rooms": ImportConfig(
        entity_type="rooms",
        table_name="rooms",
        display_name="Rooms",
        required_permission="rooms.import",
        unique_columns=["room_number"],
        columns=[
            ColumnDefinition(
                name="room_number",
                label="Room Number",
                type=ColumnType.STRING,
                required=True,
                unique=True,
                max_length=20
            ),
            ColumnDefinition(
                name="room_type_id",
                label="Room Type",
                type=ColumnType.FOREIGN_KEY,
                required=True,
                foreign_key_table="room_types",
                foreign_key_column="code"
            ),
            ColumnDefinition(
                name="floor",
                label="Floor",
                type=ColumnType.INTEGER,
                min_value=1,
                max_value=100
            ),
            ColumnDefinition(
                name="building",
                label="Building",
                type=ColumnType.STRING,
                max_length=100
            ),
            ColumnDefinition(
                name="status",
                label="Status",
                type=ColumnType.ENUM,
                enum_values=["AVAILABLE", "OCCUPIED", "MAINTENANCE", "OUT_OF_ORDER"],
                default_value="AVAILABLE"
            ),
            ColumnDefinition(
                name="is_smoking",
                label="Smoking Allowed",
                type=ColumnType.BOOLEAN,
                default_value=False
            ),
            ColumnDefinition(
                name="max_occupancy",
                label="Max Occupancy",
                type=ColumnType.INTEGER,
                default_value=2
            ),
        ]
    ),

    "inventory_items": ImportConfig(
        entity_type="inventory_items",
        table_name="inventory_items",
        display_name="Inventory Items",
        required_permission="inventory.import",
        unique_columns=["sku"],
        columns=[
            ColumnDefinition(
                name="sku",
                label="SKU",
                type=ColumnType.STRING,
                required=True,
                unique=True,
                max_length=50
            ),
            ColumnDefinition(
                name="name",
                label="Item Name",
                type=ColumnType.STRING,
                required=True,
                max_length=200
            ),
            ColumnDefinition(
                name="category_id",
                label="Category",
                type=ColumnType.FOREIGN_KEY,
                foreign_key_table="inventory_categories",
                foreign_key_column="code"
            ),
            ColumnDefinition(
                name="unit",
                label="Unit",
                type=ColumnType.STRING,
                required=True,
                max_length=20
            ),
            ColumnDefinition(
                name="unit_price",
                label="Unit Price",
                type=ColumnType.CURRENCY,
                min_value=0
            ),
            ColumnDefinition(
                name="reorder_level",
                label="Reorder Level",
                type=ColumnType.INTEGER,
                min_value=0,
                default_value=10
            ),
            ColumnDefinition(
                name="current_stock",
                label="Current Stock",
                type=ColumnType.INTEGER,
                min_value=0,
                default_value=0
            ),
        ]
    ),
}
```

### 34.6 Import Service

```python
# services/import_export/import_service.py
import csv
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from io import StringIO
import openpyxl

@dataclass
class ValidationError:
    row: int
    column: str
    value: Any
    message: str

@dataclass
class ImportResult:
    success: bool
    total_rows: int
    success_rows: int
    error_rows: int
    skipped_rows: int
    errors: List[ValidationError]

class ImportService:
    """Service for importing data from files"""

    def __init__(self, db, config_registry, job_repo):
        self.db = db
        self.configs = config_registry
        self.job_repo = job_repo

    async def create_import_job(
        self,
        entity_type: str,
        file_path: str,
        file_format: str,
        column_mapping: Dict[str, str],
        options: Dict[str, Any],
        organization_id: int,
        user_id: int
    ) -> int:
        """Create a new import job"""
        config = self.configs.get(entity_type)
        if not config:
            raise ValueError(f"Unknown entity type: {entity_type}")

        job = await self.job_repo.create({
            "organization_id": organization_id,
            "entity_type": entity_type,
            "file_path": file_path,
            "file_format": file_format,
            "column_mapping": column_mapping,
            "import_options": options,
            "status": "pending",
            "created_by_id": user_id
        })

        # Queue validation task
        from tasks.import_export import validate_import_job
        validate_import_job.delay(job.id)

        return job.id

    async def validate_job(self, job_id: int) -> Tuple[bool, List[ValidationError]]:
        """Validate import file"""
        job = await self.job_repo.get_by_id(job_id)
        config = self.configs.get(job.entity_type)

        # Update status
        job.status = "validating"
        await self.job_repo.update(job)

        errors = []

        # Read file
        rows = await self._read_file(job.file_path, job.file_format)
        job.total_rows = len(rows)

        # Validate each row
        for row_num, row in enumerate(rows, start=2):  # Start from 2 (header is 1)
            row_errors = await self._validate_row(
                row,
                row_num,
                config,
                job.column_mapping,
                job.organization_id
            )
            errors.extend(row_errors)

        # Update job
        job.error_rows = len(set(e.row for e in errors))
        job.error_details = [
            {"row": e.row, "column": e.column, "value": e.value, "message": e.message}
            for e in errors
        ]

        if errors:
            job.status = "validated"  # Has errors but validated
        else:
            job.status = "validated"

        await self.job_repo.update(job)

        return len(errors) == 0, errors

    async def execute_import(self, job_id: int) -> ImportResult:
        """Execute the import"""
        job = await self.job_repo.get_by_id(job_id)
        config = self.configs.get(job.entity_type)

        job.status = "importing"
        job.started_at = datetime.utcnow()
        await self.job_repo.update(job)

        # Read file
        rows = await self._read_file(job.file_path, job.file_format)

        success_count = 0
        error_count = 0
        skipped_count = 0
        errors = []

        # Process in batches
        batch = []
        for row_num, row in enumerate(rows, start=2):
            try:
                # Transform row to entity
                entity = await self._transform_row(
                    row,
                    config,
                    job.column_mapping,
                    job.organization_id
                )

                # Check for duplicates
                if job.import_options.get("skip_duplicates"):
                    exists = await self._check_exists(config, entity, job.organization_id)
                    if exists:
                        if job.import_options.get("update_existing"):
                            await self._update_entity(config, entity, job.organization_id)
                            success_count += 1
                        else:
                            skipped_count += 1
                        continue

                batch.append(entity)

                # Insert batch
                if len(batch) >= config.batch_size:
                    await self._insert_batch(config, batch, job.organization_id)
                    success_count += len(batch)
                    batch = []

                # Update progress
                job.processed_rows = row_num - 1
                job.success_rows = success_count
                await self.job_repo.update(job)

            except Exception as e:
                error_count += 1
                errors.append(ValidationError(
                    row=row_num,
                    column="",
                    value="",
                    message=str(e)
                ))

        # Insert remaining batch
        if batch:
            await self._insert_batch(config, batch, job.organization_id)
            success_count += len(batch)

        # Update final status
        job.status = "completed" if error_count == 0 else "completed"
        job.completed_at = datetime.utcnow()
        job.success_rows = success_count
        job.error_rows = error_count
        job.skipped_rows = skipped_count
        job.error_details = [
            {"row": e.row, "column": e.column, "message": e.message}
            for e in errors
        ]
        await self.job_repo.update(job)

        return ImportResult(
            success=error_count == 0,
            total_rows=len(rows),
            success_rows=success_count,
            error_rows=error_count,
            skipped_rows=skipped_count,
            errors=errors
        )

    async def _read_file(self, file_path: str, format: str) -> List[Dict]:
        """Read file and return list of row dicts"""
        if format == "csv":
            return await self._read_csv(file_path)
        elif format == "xlsx":
            return await self._read_xlsx(file_path)
        elif format == "json":
            return await self._read_json(file_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def _read_csv(self, file_path: str) -> List[Dict]:
        """Read CSV file"""
        rows = []
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows

    async def _read_xlsx(self, file_path: str) -> List[Dict]:
        """Read Excel file"""
        wb = openpyxl.load_workbook(file_path, read_only=True)
        ws = wb.active

        rows = []
        headers = None

        for row_num, row in enumerate(ws.iter_rows(values_only=True)):
            if row_num == 0:
                headers = [str(cell) if cell else f"column_{i}" for i, cell in enumerate(row)]
            else:
                if any(cell is not None for cell in row):
                    rows.append(dict(zip(headers, row)))

        return rows

    async def _validate_row(
        self,
        row: Dict,
        row_num: int,
        config: ImportConfig,
        mapping: Dict[str, str],
        organization_id: int
    ) -> List[ValidationError]:
        """Validate a single row"""
        errors = []

        for col_def in config.columns:
            file_column = next(
                (k for k, v in mapping.items() if v == col_def.name),
                None
            )

            if not file_column:
                if col_def.required and col_def.default_value is None:
                    errors.append(ValidationError(
                        row=row_num,
                        column=col_def.name,
                        value=None,
                        message=f"Required column '{col_def.label}' is not mapped"
                    ))
                continue

            value = row.get(file_column)

            # Required check
            if col_def.required and (value is None or str(value).strip() == ""):
                if col_def.default_value is None:
                    errors.append(ValidationError(
                        row=row_num,
                        column=col_def.name,
                        value=value,
                        message=f"'{col_def.label}' is required"
                    ))
                continue

            if value is None or str(value).strip() == "":
                continue

            # Type validation
            type_error = self._validate_type(value, col_def)
            if type_error:
                errors.append(ValidationError(
                    row=row_num,
                    column=col_def.name,
                    value=value,
                    message=type_error
                ))

            # Foreign key validation
            if col_def.type == ColumnType.FOREIGN_KEY:
                exists = await self._validate_foreign_key(
                    value,
                    col_def,
                    organization_id
                )
                if not exists:
                    errors.append(ValidationError(
                        row=row_num,
                        column=col_def.name,
                        value=value,
                        message=f"Referenced {col_def.foreign_key_table} not found"
                    ))

        return errors

    def _validate_type(self, value: Any, col_def: ColumnDefinition) -> Optional[str]:
        """Validate value type"""
        try:
            if col_def.type == ColumnType.INTEGER:
                int(value)
            elif col_def.type == ColumnType.FLOAT:
                float(value)
            elif col_def.type == ColumnType.BOOLEAN:
                if str(value).lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                    return "Must be true/false"
            elif col_def.type == ColumnType.EMAIL:
                import re
                if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', str(value)):
                    return "Invalid email format"
            elif col_def.type == ColumnType.DATE:
                from dateutil.parser import parse
                parse(str(value))
            elif col_def.type == ColumnType.ENUM:
                if str(value).upper() not in col_def.enum_values:
                    return f"Must be one of: {', '.join(col_def.enum_values)}"
            elif col_def.type == ColumnType.STRING:
                if col_def.max_length and len(str(value)) > col_def.max_length:
                    return f"Max length is {col_def.max_length}"

            return None
        except Exception as e:
            return f"Invalid {col_def.type.value}: {str(e)}"

    async def _transform_row(
        self,
        row: Dict,
        config: ImportConfig,
        mapping: Dict[str, str],
        organization_id: int
    ) -> Dict:
        """Transform file row to database entity"""
        entity = {"organization_id": organization_id}

        for col_def in config.columns:
            file_column = next(
                (k for k, v in mapping.items() if v == col_def.name),
                None
            )

            if file_column:
                value = row.get(file_column)
            else:
                value = col_def.default_value

            if value is not None and str(value).strip() != "":
                # Transform value
                entity[col_def.name] = await self._transform_value(value, col_def)
            elif col_def.default_value is not None:
                entity[col_def.name] = col_def.default_value

        return entity

    async def _transform_value(self, value: Any, col_def: ColumnDefinition) -> Any:
        """Transform value to correct type"""
        if col_def.type == ColumnType.INTEGER:
            return int(value)
        elif col_def.type == ColumnType.FLOAT:
            return float(value)
        elif col_def.type == ColumnType.BOOLEAN:
            return str(value).lower() in ['true', '1', 'yes']
        elif col_def.type == ColumnType.DATE:
            from dateutil.parser import parse
            return parse(str(value)).date()
        elif col_def.type == ColumnType.DATETIME:
            from dateutil.parser import parse
            return parse(str(value))
        elif col_def.type == ColumnType.ENUM:
            return str(value).upper()
        elif col_def.type == ColumnType.CURRENCY:
            # Remove currency symbols and convert
            cleaned = str(value).replace('Rp', '').replace(',', '').replace('.', '').strip()
            return float(cleaned)
        else:
            return str(value).strip()

    async def _insert_batch(
        self,
        config: ImportConfig,
        batch: List[Dict],
        organization_id: int
    ):
        """Insert batch of entities"""
        # Use bulk insert
        from sqlalchemy import insert
        table = self.db.get_table(config.table_name)
        await self.db.execute(insert(table).values(batch))
        await self.db.commit()
```

### 34.7 Export Service

```python
# services/import_export/export_service.py
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import csv
from io import StringIO, BytesIO
import json
import openpyxl

class ExportService:
    """Service for exporting data to files"""

    def __init__(self, db, job_repo, storage_service):
        self.db = db
        self.job_repo = job_repo
        self.storage = storage_service

    async def create_export_job(
        self,
        entity_type: str,
        export_format: str,
        filters: Dict[str, Any],
        columns: Optional[List[str]],
        organization_id: int,
        user_id: int
    ) -> int:
        """Create export job"""
        job = await self.job_repo.create({
            "organization_id": organization_id,
            "entity_type": entity_type,
            "export_format": export_format,
            "filters": filters,
            "columns": columns,
            "status": "pending",
            "created_by_id": user_id
        })

        # Queue export task
        from tasks.import_export import execute_export_job
        execute_export_job.delay(job.id)

        return job.id

    async def execute_export(self, job_id: int) -> str:
        """Execute export and return download URL"""
        job = await self.job_repo.get_by_id(job_id)

        job.status = "processing"
        await self.job_repo.update(job)

        # Query data
        data = await self._query_data(
            job.entity_type,
            job.filters,
            job.columns,
            job.organization_id
        )

        job.total_rows = len(data)

        # Export to format
        if job.export_format == "csv":
            file_bytes = await self._export_csv(data, job.columns)
            content_type = "text/csv"
        elif job.export_format == "xlsx":
            file_bytes = await self._export_xlsx(data, job.columns, job.entity_type)
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif job.export_format == "json":
            file_bytes = await self._export_json(data)
            content_type = "application/json"
        else:
            raise ValueError(f"Unsupported format: {job.export_format}")

        # Upload to storage
        filename = f"exports/{job.entity_type}_{job.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{job.export_format}"
        download_url = await self.storage.upload(
            file_bytes,
            filename,
            content_type=content_type,
            expires_in=timedelta(hours=24)
        )

        # Update job
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.file_path = filename
        job.file_size_bytes = len(file_bytes)
        job.download_url = download_url
        job.download_expires_at = datetime.utcnow() + timedelta(hours=24)
        await self.job_repo.update(job)

        return download_url

    async def _query_data(
        self,
        entity_type: str,
        filters: Dict,
        columns: Optional[List[str]],
        organization_id: int
    ) -> List[Dict]:
        """Query data based on entity type and filters"""
        config = EXPORT_CONFIGS.get(entity_type)
        if not config:
            raise ValueError(f"Unknown entity type: {entity_type}")

        # Build query
        query = config.base_query

        # Add organization filter
        query = query.where(config.table.c.organization_id == organization_id)

        # Add custom filters
        for field, value in filters.items():
            if hasattr(config.table.c, field):
                if isinstance(value, list):
                    query = query.where(config.table.c[field].in_(value))
                elif isinstance(value, dict):
                    if "from" in value:
                        query = query.where(config.table.c[field] >= value["from"])
                    if "to" in value:
                        query = query.where(config.table.c[field] <= value["to"])
                else:
                    query = query.where(config.table.c[field] == value)

        # Select columns
        if columns:
            query = query.with_only_columns([config.table.c[c] for c in columns])

        result = await self.db.execute(query)
        return [dict(row) for row in result.fetchall()]

    async def _export_csv(self, data: List[Dict], columns: Optional[List[str]]) -> bytes:
        """Export data to CSV"""
        if not data:
            return b""

        output = StringIO()
        fieldnames = columns or list(data[0].keys())

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)

        return output.getvalue().encode('utf-8-sig')

    async def _export_xlsx(
        self,
        data: List[Dict],
        columns: Optional[List[str]],
        entity_type: str
    ) -> bytes:
        """Export data to Excel"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = entity_type.replace("_", " ").title()

        if not data:
            return self._workbook_to_bytes(wb)

        # Headers
        fieldnames = columns or list(data[0].keys())
        for col_num, field in enumerate(fieldnames, 1):
            cell = ws.cell(row=1, column=col_num, value=field.replace("_", " ").title())
            cell.font = openpyxl.styles.Font(bold=True)

        # Data rows
        for row_num, row in enumerate(data, 2):
            for col_num, field in enumerate(fieldnames, 1):
                value = row.get(field)
                # Handle datetime
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                ws.cell(row=row_num, column=col_num, value=value)

        # Auto-adjust column widths
        for col_num, field in enumerate(fieldnames, 1):
            max_length = len(field)
            for row in data[:100]:  # Sample first 100 rows
                cell_value = str(row.get(field, ""))
                max_length = max(max_length, len(cell_value))
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = min(max_length + 2, 50)

        return self._workbook_to_bytes(wb)

    async def _export_json(self, data: List[Dict]) -> bytes:
        """Export data to JSON"""
        # Convert datetime to string
        def json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        return json.dumps(data, default=json_serial, indent=2).encode('utf-8')

    def _workbook_to_bytes(self, wb) -> bytes:
        """Convert workbook to bytes"""
        output = BytesIO()
        wb.save(output)
        return output.getvalue()
```

### 34.8 API Endpoints

```python
# services/import_export/routes.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/import-export", tags=["Import/Export"])

# ============ IMPORT ENDPOINTS ============

@router.get("/import/configs")
async def get_import_configs(
    current_user = Depends(get_current_user)
):
    """Get available import configurations"""
    configs = []
    for entity_type, config in IMPORT_CONFIGS.items():
        if config.required_permission in current_user.permissions:
            configs.append({
                "entity_type": entity_type,
                "display_name": config.display_name,
                "columns": [
                    {
                        "name": c.name,
                        "label": c.label,
                        "type": c.type.value,
                        "required": c.required,
                        "enum_values": c.enum_values
                    }
                    for c in config.columns
                ],
                "max_rows": config.max_rows
            })
    return configs

@router.post("/import/upload")
async def upload_import_file(
    entity_type: str,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    storage = Depends(get_storage)
):
    """Upload file for import"""
    # Validate file type
    allowed_extensions = ['.csv', '.xlsx', '.json']
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(400, f"File type not supported. Allowed: {allowed_extensions}")

    # Save file
    file_path = f"imports/{current_user.organization_id}/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    await storage.upload_file(file.file, file_path)

    # Read headers for mapping
    headers = await read_file_headers(file_path, ext[1:])

    return {
        "file_path": file_path,
        "file_name": file.filename,
        "format": ext[1:],
        "headers": headers
    }

@router.post("/import/jobs")
async def create_import_job(
    request: CreateImportJobRequest,
    current_user = Depends(get_current_user),
    import_service: ImportService = Depends()
):
    """Create import job"""
    job_id = await import_service.create_import_job(
        entity_type=request.entity_type,
        file_path=request.file_path,
        file_format=request.file_format,
        column_mapping=request.column_mapping,
        options=request.options,
        organization_id=current_user.organization_id,
        user_id=current_user.id
    )

    return {"job_id": job_id, "status": "pending"}

@router.get("/import/jobs/{job_id}")
async def get_import_job_status(
    job_id: int,
    current_user = Depends(get_current_user),
    job_repo = Depends(get_import_job_repo)
):
    """Get import job status"""
    job = await job_repo.get_by_id(job_id)

    if not job or job.organization_id != current_user.organization_id:
        raise HTTPException(404, "Job not found")

    return {
        "id": job.id,
        "status": job.status,
        "total_rows": job.total_rows,
        "processed_rows": job.processed_rows,
        "success_rows": job.success_rows,
        "error_rows": job.error_rows,
        "skipped_rows": job.skipped_rows,
        "errors": job.error_details[:100] if job.error_details else [],  # Limit errors
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }

@router.post("/import/jobs/{job_id}/execute")
async def execute_import_job(
    job_id: int,
    current_user = Depends(get_current_user),
    import_service: ImportService = Depends()
):
    """Execute validated import job"""
    job = await import_service.job_repo.get_by_id(job_id)

    if not job or job.organization_id != current_user.organization_id:
        raise HTTPException(404, "Job not found")

    if job.status != "validated":
        raise HTTPException(400, f"Job cannot be executed. Status: {job.status}")

    # Queue execution
    from tasks.import_export import execute_import_job
    execute_import_job.delay(job_id)

    return {"status": "importing"}

@router.get("/import/jobs/{job_id}/errors/download")
async def download_import_errors(
    job_id: int,
    current_user = Depends(get_current_user),
    job_repo = Depends(get_import_job_repo)
):
    """Download import errors as CSV"""
    job = await job_repo.get_by_id(job_id)

    if not job or job.organization_id != current_user.organization_id:
        raise HTTPException(404, "Job not found")

    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Row", "Column", "Value", "Error"])

    for error in job.error_details or []:
        writer.writerow([
            error.get("row"),
            error.get("column"),
            error.get("value"),
            error.get("message")
        ])

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=import_errors_{job_id}.csv"}
    )

# ============ EXPORT ENDPOINTS ============

@router.get("/export/configs")
async def get_export_configs(
    current_user = Depends(get_current_user)
):
    """Get available export configurations"""
    # Similar to import configs
    pass

@router.post("/export/jobs")
async def create_export_job(
    request: CreateExportJobRequest,
    current_user = Depends(get_current_user),
    export_service: ExportService = Depends()
):
    """Create export job"""
    job_id = await export_service.create_export_job(
        entity_type=request.entity_type,
        export_format=request.format,
        filters=request.filters,
        columns=request.columns,
        organization_id=current_user.organization_id,
        user_id=current_user.id
    )

    return {"job_id": job_id, "status": "pending"}

@router.get("/export/jobs/{job_id}")
async def get_export_job_status(
    job_id: int,
    current_user = Depends(get_current_user),
    job_repo = Depends(get_export_job_repo)
):
    """Get export job status"""
    job = await job_repo.get_by_id(job_id)

    if not job or job.organization_id != current_user.organization_id:
        raise HTTPException(404, "Job not found")

    return {
        "id": job.id,
        "status": job.status,
        "total_rows": job.total_rows,
        "download_url": job.download_url if job.status == "completed" else None,
        "expires_at": job.download_expires_at,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }
```

### 34.9 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Validate First | Always validate before importing |
| 2 | Batch Processing | Process imports in batches |
| 3 | Error Report | Provide downloadable error report |
| 4 | Column Mapping | Allow flexible column mapping |
| 5 | Async for Large | Use async processing for large files |
| 6 | Progress Updates | Show import progress |
| 7 | Rollback Support | Allow rollback on error |
| 8 | Templates | Save mapping templates for reuse |

---

## Standard #35: Email Templates

### 35.1 Overview

Email Templates memungkinkan sistem mengirim email yang konsisten dan dapat dikustomisasi. Templates menggunakan variable substitution dan dapat di-customize per tenant.

### 35.2 Email Template Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     EMAIL TEMPLATE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      TEMPLATE STRUCTURE                          │   │
│  │                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │  BASE LAYOUT                                             │    │   │
│  │  │  ┌─────────────────────────────────────────────────┐    │    │   │
│  │  │  │  HEADER (logo, organization name)               │    │    │   │
│  │  │  └─────────────────────────────────────────────────┘    │    │   │
│  │  │  ┌─────────────────────────────────────────────────┐    │    │   │
│  │  │  │  CONTENT BLOCK                                  │    │    │   │
│  │  │  │  - Dynamic content from template                │    │    │   │
│  │  │  │  - Variable substitution {{ name }}             │    │    │   │
│  │  │  │  - Conditional blocks {% if %}                  │    │    │   │
│  │  │  │  - Loops {% for %}                              │    │    │   │
│  │  │  └─────────────────────────────────────────────────┘    │    │   │
│  │  │  ┌─────────────────────────────────────────────────┐    │    │   │
│  │  │  │  FOOTER (contact, unsubscribe, social)          │    │    │   │
│  │  │  └─────────────────────────────────────────────────┘    │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  RENDERING FLOW:                                                        │
│  Template + Variables + Tenant Config → Rendered HTML → Send Email     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 35.3 Database Schema

```sql
-- Email templates
CREATE TABLE email_templates (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,  -- NULL = system default

    -- Template info
    code VARCHAR(100) NOT NULL,  -- booking_confirmation, password_reset, etc.
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,  -- transactional, marketing, notification

    -- Content
    subject_template VARCHAR(500) NOT NULL,
    body_html TEXT NOT NULL,
    body_text TEXT,  -- Plain text version

    -- Variables
    available_variables JSONB NOT NULL,  -- [{name, description, example}]

    -- Settings
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    locale VARCHAR(10) DEFAULT 'id',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Unique per org + code + locale
    UNIQUE(organization_id, code, locale)
);

-- Email sending log
CREATE TABLE email_logs (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    template_id INTEGER REFERENCES email_templates(id) ON DELETE SET NULL,

    -- Recipient
    to_email VARCHAR(500) NOT NULL,
    to_name VARCHAR(200),
    cc_emails TEXT[],
    bcc_emails TEXT[],

    -- Content
    subject VARCHAR(500) NOT NULL,
    body_preview TEXT,  -- First 500 chars

    -- Status
    status VARCHAR(50) NOT NULL,  -- queued, sent, delivered, bounced, failed
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,

    -- Provider info
    provider VARCHAR(50),  -- sendgrid, ses, smtp
    provider_message_id VARCHAR(200),
    provider_response JSONB,

    -- Error
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    CONSTRAINT valid_status CHECK (status IN (
        'queued', 'sending', 'sent', 'delivered', 'opened',
        'clicked', 'bounced', 'complained', 'failed'
    ))
);

-- Indexes
CREATE INDEX idx_email_templates_org_code ON email_templates(organization_id, code);
CREATE INDEX idx_email_logs_org ON email_logs(organization_id);
CREATE INDEX idx_email_logs_status ON email_logs(status);
CREATE INDEX idx_email_logs_to ON email_logs(to_email);
```

### 35.4 Template Definitions

```python
# services/email/templates.py
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class EmailCategory(str, Enum):
    TRANSACTIONAL = "transactional"
    NOTIFICATION = "notification"
    MARKETING = "marketing"

@dataclass
class TemplateVariable:
    name: str
    description: str
    example: str
    required: bool = True

@dataclass
class EmailTemplateDefinition:
    code: str
    name: str
    category: EmailCategory
    description: str
    variables: List[TemplateVariable]
    default_subject: str
    default_body_html: str

# System templates
SYSTEM_TEMPLATES: Dict[str, EmailTemplateDefinition] = {
    "booking_confirmation": EmailTemplateDefinition(
        code="booking_confirmation",
        name="Booking Confirmation",
        category=EmailCategory.TRANSACTIONAL,
        description="Sent when a booking is confirmed",
        variables=[
            TemplateVariable("guest_name", "Guest's full name", "John Doe"),
            TemplateVariable("confirmation_number", "Booking confirmation number", "BK-2025-0001"),
            TemplateVariable("check_in_date", "Check-in date", "January 15, 2025"),
            TemplateVariable("check_out_date", "Check-out date", "January 17, 2025"),
            TemplateVariable("room_type", "Type of room booked", "Deluxe Room"),
            TemplateVariable("total_amount", "Total booking amount", "Rp 2,500,000"),
            TemplateVariable("hotel_name", "Hotel name", "Grand Hotel"),
            TemplateVariable("hotel_address", "Hotel address", "Jl. Sudirman No. 1"),
            TemplateVariable("hotel_phone", "Hotel phone number", "+62 21 1234567"),
        ],
        default_subject="Booking Confirmation - {{ confirmation_number }}",
        default_body_html="""
        <h1>Booking Confirmed!</h1>
        <p>Dear {{ guest_name }},</p>
        <p>Thank you for your reservation. Your booking has been confirmed.</p>

        <div class="booking-details">
            <h2>Booking Details</h2>
            <table>
                <tr><td>Confirmation Number:</td><td><strong>{{ confirmation_number }}</strong></td></tr>
                <tr><td>Check-in:</td><td>{{ check_in_date }}</td></tr>
                <tr><td>Check-out:</td><td>{{ check_out_date }}</td></tr>
                <tr><td>Room Type:</td><td>{{ room_type }}</td></tr>
                <tr><td>Total Amount:</td><td>{{ total_amount }}</td></tr>
            </table>
        </div>

        <p>We look forward to welcoming you!</p>

        <div class="hotel-info">
            <p><strong>{{ hotel_name }}</strong><br>
            {{ hotel_address }}<br>
            {{ hotel_phone }}</p>
        </div>
        """
    ),

    "password_reset": EmailTemplateDefinition(
        code="password_reset",
        name="Password Reset",
        category=EmailCategory.TRANSACTIONAL,
        description="Sent when user requests password reset",
        variables=[
            TemplateVariable("user_name", "User's name", "John"),
            TemplateVariable("reset_link", "Password reset URL", "https://app.example.com/reset?token=xxx"),
            TemplateVariable("expiry_hours", "Link expiry time in hours", "24"),
            TemplateVariable("app_name", "Application name", "Hotel PMS"),
        ],
        default_subject="Reset Your Password - {{ app_name }}",
        default_body_html="""
        <h1>Password Reset Request</h1>
        <p>Hi {{ user_name }},</p>
        <p>We received a request to reset your password. Click the button below to create a new password:</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ reset_link }}" class="button">Reset Password</a>
        </div>

        <p>This link will expire in {{ expiry_hours }} hours.</p>

        <p>If you didn't request this, you can safely ignore this email.</p>
        """
    ),

    "welcome_user": EmailTemplateDefinition(
        code="welcome_user",
        name="Welcome New User",
        category=EmailCategory.TRANSACTIONAL,
        description="Sent when a new user is created",
        variables=[
            TemplateVariable("user_name", "User's name", "John"),
            TemplateVariable("email", "User's email", "john@example.com"),
            TemplateVariable("temporary_password", "Temporary password", "TempPass123", required=False),
            TemplateVariable("login_url", "Login page URL", "https://app.example.com/login"),
            TemplateVariable("organization_name", "Organization name", "Grand Hotel"),
            TemplateVariable("app_name", "Application name", "Hotel PMS"),
        ],
        default_subject="Welcome to {{ organization_name }}!",
        default_body_html="""
        <h1>Welcome to {{ organization_name }}!</h1>
        <p>Hi {{ user_name }},</p>
        <p>Your account has been created for {{ app_name }}.</p>

        <div class="account-info">
            <p><strong>Email:</strong> {{ email }}</p>
            {% if temporary_password %}
            <p><strong>Temporary Password:</strong> {{ temporary_password }}</p>
            <p><em>Please change your password after first login.</em></p>
            {% endif %}
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ login_url }}" class="button">Login Now</a>
        </div>
        """
    ),

    "invoice": EmailTemplateDefinition(
        code="invoice",
        name="Invoice",
        category=EmailCategory.TRANSACTIONAL,
        description="Sent with invoice/bill",
        variables=[
            TemplateVariable("guest_name", "Guest's name", "John Doe"),
            TemplateVariable("invoice_number", "Invoice number", "INV-2025-0001"),
            TemplateVariable("invoice_date", "Invoice date", "January 15, 2025"),
            TemplateVariable("due_date", "Payment due date", "January 20, 2025"),
            TemplateVariable("items", "Invoice line items (list)", "[{name, qty, price, total}]"),
            TemplateVariable("subtotal", "Subtotal amount", "Rp 2,000,000"),
            TemplateVariable("tax", "Tax amount", "Rp 220,000"),
            TemplateVariable("total", "Total amount", "Rp 2,220,000"),
            TemplateVariable("payment_instructions", "Payment instructions", "Transfer to..."),
        ],
        default_subject="Invoice {{ invoice_number }} from {{ hotel_name }}",
        default_body_html="""
        <h1>Invoice</h1>
        <p>Dear {{ guest_name }},</p>
        <p>Please find your invoice details below:</p>

        <div class="invoice-header">
            <p><strong>Invoice #:</strong> {{ invoice_number }}<br>
            <strong>Date:</strong> {{ invoice_date }}<br>
            <strong>Due Date:</strong> {{ due_date }}</p>
        </div>

        <table class="invoice-items">
            <thead>
                <tr>
                    <th>Description</th>
                    <th>Qty</th>
                    <th>Price</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                {% for item in items %}
                <tr>
                    <td>{{ item.name }}</td>
                    <td>{{ item.qty }}</td>
                    <td>{{ item.price }}</td>
                    <td>{{ item.total }}</td>
                </tr>
                {% endfor %}
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="3">Subtotal</td>
                    <td>{{ subtotal }}</td>
                </tr>
                <tr>
                    <td colspan="3">Tax (11%)</td>
                    <td>{{ tax }}</td>
                </tr>
                <tr class="total">
                    <td colspan="3"><strong>Total</strong></td>
                    <td><strong>{{ total }}</strong></td>
                </tr>
            </tfoot>
        </table>

        <div class="payment-info">
            <h3>Payment Instructions</h3>
            <p>{{ payment_instructions }}</p>
        </div>
        """
    ),

    "check_in_reminder": EmailTemplateDefinition(
        code="check_in_reminder",
        name="Check-in Reminder",
        category=EmailCategory.NOTIFICATION,
        description="Sent before guest check-in date",
        variables=[
            TemplateVariable("guest_name", "Guest's name", "John Doe"),
            TemplateVariable("check_in_date", "Check-in date", "Tomorrow, January 15, 2025"),
            TemplateVariable("check_in_time", "Check-in time", "2:00 PM"),
            TemplateVariable("confirmation_number", "Confirmation number", "BK-2025-0001"),
            TemplateVariable("room_type", "Room type", "Deluxe Room"),
            TemplateVariable("special_requests", "Special requests", "Late check-out", required=False),
            TemplateVariable("hotel_name", "Hotel name", "Grand Hotel"),
            TemplateVariable("hotel_address", "Hotel address", "Jl. Sudirman No. 1"),
            TemplateVariable("directions_url", "Directions URL", "https://maps.google.com/...", required=False),
        ],
        default_subject="Reminder: Your Stay at {{ hotel_name }} - {{ check_in_date }}",
        default_body_html="""
        <h1>See You Soon!</h1>
        <p>Dear {{ guest_name }},</p>
        <p>This is a friendly reminder about your upcoming stay.</p>

        <div class="reminder-details">
            <h2>Your Reservation</h2>
            <p><strong>Check-in:</strong> {{ check_in_date }} at {{ check_in_time }}<br>
            <strong>Room:</strong> {{ room_type }}<br>
            <strong>Confirmation:</strong> {{ confirmation_number }}</p>

            {% if special_requests %}
            <p><strong>Special Requests:</strong> {{ special_requests }}</p>
            {% endif %}
        </div>

        <div class="location">
            <h3>Getting Here</h3>
            <p>{{ hotel_address }}</p>
            {% if directions_url %}
            <a href="{{ directions_url }}">View Directions</a>
            {% endif %}
        </div>

        <p>Need to make changes? Contact us or reply to this email.</p>
        """
    ),
}
```

### 35.5 Email Service

```python
# services/email/email_service.py
from typing import Dict, Any, Optional, List
from datetime import datetime
from jinja2 import Environment, BaseLoader, select_autoescape
import html2text

class EmailService:
    """Service for sending templated emails"""

    def __init__(
        self,
        template_repo,
        log_repo,
        email_provider,
        organization_service
    ):
        self.template_repo = template_repo
        self.log_repo = log_repo
        self.provider = email_provider
        self.org_service = organization_service

        # Jinja2 environment
        self.jinja_env = Environment(
            loader=BaseLoader(),
            autoescape=select_autoescape(['html', 'xml'])
        )

    async def send_template(
        self,
        template_code: str,
        to_email: str,
        variables: Dict[str, Any],
        organization_id: int,
        to_name: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None,
        locale: str = "id",
        user_id: Optional[int] = None
    ) -> int:
        """Send email using template"""

        # Get template (tenant override or system default)
        template = await self._get_template(template_code, organization_id, locale)
        if not template:
            raise ValueError(f"Template not found: {template_code}")

        # Get organization settings for branding
        org_settings = await self.org_service.get_settings(organization_id)

        # Add common variables
        full_variables = {
            **variables,
            "organization_name": org_settings.get("name"),
            "organization_logo": org_settings.get("logo_url"),
            "organization_website": org_settings.get("website"),
            "organization_email": org_settings.get("email"),
            "organization_phone": org_settings.get("phone"),
            "current_year": datetime.now().year,
        }

        # Render template
        subject = self._render_template(template.subject_template, full_variables)
        body_html = self._render_full_email(template.body_html, full_variables, org_settings)
        body_text = self._html_to_text(body_html)

        # Create log entry
        log = await self.log_repo.create({
            "organization_id": organization_id,
            "template_id": template.id,
            "to_email": to_email,
            "to_name": to_name,
            "cc_emails": cc,
            "bcc_emails": bcc,
            "subject": subject,
            "body_preview": body_text[:500] if body_text else None,
            "status": "queued",
            "created_by_id": user_id
        })

        # Queue email for sending
        from tasks.email import send_email_task
        send_email_task.delay(log.id, body_html, body_text, attachments)

        return log.id

    async def _get_template(
        self,
        code: str,
        organization_id: int,
        locale: str
    ):
        """Get template - tenant override or system default"""
        # Try tenant-specific first
        template = await self.template_repo.get_by_code(
            code=code,
            organization_id=organization_id,
            locale=locale
        )

        if template:
            return template

        # Fall back to system default
        template = await self.template_repo.get_by_code(
            code=code,
            organization_id=None,
            locale=locale
        )

        if template:
            return template

        # Fall back to system default with default locale
        return await self.template_repo.get_by_code(
            code=code,
            organization_id=None,
            locale="en"
        )

    def _render_template(self, template_string: str, variables: Dict) -> str:
        """Render Jinja2 template"""
        template = self.jinja_env.from_string(template_string)
        return template.render(**variables)

    def _render_full_email(
        self,
        body_content: str,
        variables: Dict,
        org_settings: Dict
    ) -> str:
        """Render full email with layout"""
        # Render body content
        rendered_body = self._render_template(body_content, variables)

        # Wrap in base layout
        base_layout = self._get_base_layout(org_settings)
        return base_layout.replace("{{ content }}", rendered_body)

    def _get_base_layout(self, org_settings: Dict) -> str:
        """Get email base layout with branding"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    padding: 20px 0;
                    border-bottom: 1px solid #eee;
                }}
                .header img {{
                    max-height: 60px;
                }}
                .content {{
                    padding: 30px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px 0;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #666;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: {org_settings.get('primary_color', '#007bff')};
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #eee;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                {"<img src='" + org_settings.get('logo_url') + "' alt='Logo'>" if org_settings.get('logo_url') else ""}
                <h2>{org_settings.get('name', '')}</h2>
            </div>

            <div class="content">
                {{{{ content }}}}
            </div>

            <div class="footer">
                <p>{org_settings.get('name', '')}<br>
                {org_settings.get('address', '')}<br>
                {org_settings.get('phone', '')} | {org_settings.get('email', '')}</p>
                <p>&copy; {datetime.now().year} {org_settings.get('name', '')}. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        return h.handle(html)


# Celery task for sending
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def send_email_task(self, log_id: int, body_html: str, body_text: str, attachments: list):
    """Send email via provider"""
    from shared.database import get_db_sync

    with get_db_sync() as db:
        log_repo = EmailLogRepository(db)
        log = log_repo.get_by_id(log_id)

        if not log:
            return

        log.status = "sending"
        log_repo.update(log)

        try:
            # Get provider
            provider = get_email_provider()

            # Send email
            result = provider.send(
                to_email=log.to_email,
                to_name=log.to_name,
                subject=log.subject,
                body_html=body_html,
                body_text=body_text,
                cc=log.cc_emails,
                bcc=log.bcc_emails,
                attachments=attachments
            )

            log.status = "sent"
            log.sent_at = datetime.utcnow()
            log.provider = provider.name
            log.provider_message_id = result.message_id
            log.provider_response = result.raw_response

        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            log.retry_count += 1

            # Retry with exponential backoff
            if log.retry_count < 3:
                raise self.retry(exc=e, countdown=60 * (2 ** log.retry_count))

        log_repo.update(log)
```

### 35.6 API Endpoints

```python
# services/email/routes.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/email", tags=["Email"])

@router.get("/templates")
async def list_templates(
    category: Optional[str] = None,
    current_user = Depends(get_current_user),
    template_repo = Depends(get_template_repo)
):
    """List available email templates"""
    templates = await template_repo.get_all(
        organization_id=current_user.organization_id,
        category=category
    )

    return [
        {
            "id": t.id,
            "code": t.code,
            "name": t.name,
            "category": t.category,
            "is_customized": t.organization_id is not None,
            "locale": t.locale
        }
        for t in templates
    ]

@router.get("/templates/{code}")
async def get_template(
    code: str,
    locale: str = "id",
    current_user = Depends(get_current_user),
    template_repo = Depends(get_template_repo)
):
    """Get template details"""
    template = await template_repo.get_by_code(
        code=code,
        organization_id=current_user.organization_id,
        locale=locale
    )

    if not template:
        # Get system default
        template = await template_repo.get_by_code(
            code=code,
            organization_id=None,
            locale=locale
        )

    if not template:
        raise HTTPException(404, "Template not found")

    return {
        "id": template.id,
        "code": template.code,
        "name": template.name,
        "subject_template": template.subject_template,
        "body_html": template.body_html,
        "available_variables": template.available_variables,
        "is_customized": template.organization_id is not None
    }

@router.put("/templates/{code}")
async def customize_template(
    code: str,
    request: CustomizeTemplateRequest,
    current_user = Depends(get_current_user),
    template_repo = Depends(get_template_repo)
):
    """Customize template for organization"""
    # Get system template for reference
    system_template = await template_repo.get_by_code(
        code=code,
        organization_id=None,
        locale=request.locale
    )

    if not system_template:
        raise HTTPException(404, "System template not found")

    # Create or update org template
    org_template = await template_repo.upsert({
        "organization_id": current_user.organization_id,
        "code": code,
        "name": system_template.name,
        "category": system_template.category,
        "subject_template": request.subject_template,
        "body_html": request.body_html,
        "available_variables": system_template.available_variables,
        "locale": request.locale,
        "updated_by_id": current_user.id
    })

    return {"id": org_template.id, "status": "customized"}

@router.post("/templates/{code}/preview")
async def preview_template(
    code: str,
    request: PreviewTemplateRequest,
    current_user = Depends(get_current_user),
    email_service: EmailService = Depends()
):
    """Preview rendered template"""
    template = await email_service._get_template(
        code=code,
        organization_id=current_user.organization_id,
        locale=request.locale
    )

    if not template:
        raise HTTPException(404, "Template not found")

    org_settings = await email_service.org_service.get_settings(
        current_user.organization_id
    )

    # Render with sample/provided variables
    variables = request.variables or _get_sample_variables(template)

    subject = email_service._render_template(
        template.subject_template,
        variables
    )
    body_html = email_service._render_full_email(
        template.body_html,
        variables,
        org_settings
    )

    return {
        "subject": subject,
        "body_html": body_html
    }

@router.post("/templates/{code}/test")
async def send_test_email(
    code: str,
    request: TestEmailRequest,
    current_user = Depends(get_current_user),
    email_service: EmailService = Depends()
):
    """Send test email"""
    log_id = await email_service.send_template(
        template_code=code,
        to_email=request.to_email,
        variables=request.variables or {},
        organization_id=current_user.organization_id,
        locale=request.locale,
        user_id=current_user.id
    )

    return {"log_id": log_id, "status": "queued"}

@router.get("/logs")
async def list_email_logs(
    status: Optional[str] = None,
    template_code: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 50,
    current_user = Depends(get_current_user),
    log_repo = Depends(get_log_repo)
):
    """List email sending logs"""
    logs = await log_repo.get_all(
        organization_id=current_user.organization_id,
        status=status,
        template_code=template_code,
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )

    return logs
```

### 35.7 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Plain Text Version | Always include plain text version |
| 2 | Preview & Test | Provide preview and test send functionality |
| 3 | Variable Validation | Validate required variables before sending |
| 4 | Responsive Design | Use responsive email templates |
| 5 | Unsubscribe Link | Include unsubscribe for marketing emails |
| 6 | Log Everything | Log all sent emails for audit |
| 7 | Retry Failed | Implement retry for failed sends |
| 8 | Rate Limiting | Rate limit email sending |

---

## Standard #36: Offline/PWA Support

### 36.1 Overview

Offline/PWA Support memungkinkan aplikasi tetap berfungsi meski tanpa koneksi internet. Menggunakan Service Worker untuk caching dan IndexedDB untuk data lokal.

### 36.2 PWA Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PWA ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       BROWSER                                    │   │
│  │                                                                   │   │
│  │   ┌───────────────┐                    ┌───────────────┐        │   │
│  │   │   React App   │◄──────────────────►│Service Worker │        │   │
│  │   │               │                    │               │        │   │
│  │   │  ┌─────────┐  │                    │  ┌─────────┐  │        │   │
│  │   │  │  State  │  │                    │  │  Cache  │  │        │   │
│  │   │  │ Manager │  │                    │  │ Storage │  │        │   │
│  │   │  └─────────┘  │                    │  └─────────┘  │        │   │
│  │   │       │       │                    │       │       │        │   │
│  │   │       ▼       │                    │       ▼       │        │   │
│  │   │  ┌─────────┐  │                    │  ┌─────────┐  │        │   │
│  │   │  │IndexedDB│  │                    │  │ Network │  │        │   │
│  │   │  │(offline)│  │                    │  │ Fetch   │  │        │   │
│  │   │  └─────────┘  │                    │  └─────────┘  │        │   │
│  │   └───────────────┘                    └───────────────┘        │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                     │                                    │
│                                     │ Online                             │
│                                     ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        SERVER                                    │   │
│  │                                                                   │   │
│  │   ┌───────────────┐    ┌───────────────┐    ┌───────────────┐   │   │
│  │   │   REST API    │    │   Database    │    │     Sync      │   │   │
│  │   │               │    │               │    │    Queue      │   │   │
│  │   └───────────────┘    └───────────────┘    └───────────────┘   │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 36.3 Service Worker

```typescript
// public/sw.js
const CACHE_NAME = 'hotel-pms-v1';
const STATIC_CACHE = 'static-v1';
const DYNAMIC_CACHE = 'dynamic-v1';
const API_CACHE = 'api-v1';

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/offline.html',
  '/assets/logo.png',
  // Add other static assets
];

// API routes to cache
const CACHEABLE_API_ROUTES = [
  '/api/v1/room-types',
  '/api/v1/rate-codes',
  '/api/v1/payment-methods',
  // Lookup data that rarely changes
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== STATIC_CACHE && key !== DYNAMIC_CACHE && key !== API_CACHE)
          .map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Static assets - Cache First
  if (isStaticAsset(url.pathname)) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }

  // HTML pages - Network First with offline fallback
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkFirstWithOffline(request));
    return;
  }

  // Other requests - Stale While Revalidate
  event.respondWith(staleWhileRevalidate(request, DYNAMIC_CACHE));
});

// Cache strategies
async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }

  const response = await fetch(request);
  if (response.ok) {
    const cache = await caches.open(cacheName);
    cache.put(request, response.clone());
  }
  return response;
}

async function networkFirstWithOffline(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    return caches.match('/offline.html');
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cached = await caches.match(request);

  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) {
      const cache = caches.open(cacheName);
      cache.then((c) => c.put(request, response.clone()));
    }
    return response;
  });

  return cached || fetchPromise;
}

// Handle API requests
async function handleApiRequest(request) {
  const url = new URL(request.url);

  // Check if this is a cacheable lookup endpoint
  if (CACHEABLE_API_ROUTES.some((route) => url.pathname.includes(route)) && request.method === 'GET') {
    return staleWhileRevalidate(request, API_CACHE);
  }

  // For mutations (POST, PUT, DELETE) - try network, queue if offline
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(request.method)) {
    try {
      return await fetch(request);
    } catch (error) {
      // Queue for later sync
      await queueRequest(request);
      return new Response(
        JSON.stringify({
          queued: true,
          message: 'Request queued for sync when online',
        }),
        {
          status: 202,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }
  }

  // Regular GET requests - network first
  try {
    return await fetch(request);
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    return new Response(
      JSON.stringify({ error: 'Offline and no cached data available' }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

// Queue request for background sync
async function queueRequest(request) {
  const db = await openSyncDB();
  const requestData = {
    url: request.url,
    method: request.method,
    headers: Object.fromEntries(request.headers),
    body: await request.text(),
    timestamp: Date.now(),
  };

  const tx = db.transaction('sync-queue', 'readwrite');
  await tx.objectStore('sync-queue').add(requestData);
}

// Background sync
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-requests') {
    event.waitUntil(syncQueuedRequests());
  }
});

async function syncQueuedRequests() {
  const db = await openSyncDB();
  const tx = db.transaction('sync-queue', 'readwrite');
  const store = tx.objectStore('sync-queue');
  const requests = await store.getAll();

  for (const requestData of requests) {
    try {
      const response = await fetch(requestData.url, {
        method: requestData.method,
        headers: requestData.headers,
        body: requestData.body,
      });

      if (response.ok) {
        await store.delete(requestData.id);
        // Notify app of successful sync
        self.clients.matchAll().then((clients) => {
          clients.forEach((client) => {
            client.postMessage({
              type: 'SYNC_COMPLETED',
              request: requestData,
            });
          });
        });
      }
    } catch (error) {
      console.log('Sync failed, will retry later:', requestData.url);
    }
  }
}

// Helper functions
function isStaticAsset(pathname) {
  return /\.(js|css|png|jpg|jpeg|gif|svg|woff2?|ttf|eot)$/.test(pathname);
}

function openSyncDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('sync-db', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('sync-queue')) {
        db.createObjectStore('sync-queue', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}
```

### 36.4 IndexedDB Store

```typescript
// lib/offline/indexedDB.ts
import { openDB, DBSchema, IDBPDatabase } from 'idb';

interface OfflineDB extends DBSchema {
  'cached-data': {
    key: string;
    value: {
      key: string;
      data: any;
      timestamp: number;
      expiresAt?: number;
    };
  };
  'pending-mutations': {
    key: number;
    value: {
      id?: number;
      type: 'create' | 'update' | 'delete';
      entity: string;
      data: any;
      timestamp: number;
      retries: number;
    };
    indexes: { 'by-entity': string };
  };
  'sync-status': {
    key: string;
    value: {
      entity: string;
      lastSyncedAt: number;
      syncInProgress: boolean;
    };
  };
}

class OfflineStore {
  private db: IDBPDatabase<OfflineDB> | null = null;
  private dbName = 'hotel-pms-offline';
  private version = 1;

  async init(): Promise<void> {
    this.db = await openDB<OfflineDB>(this.dbName, this.version, {
      upgrade(db) {
        // Cached data store
        if (!db.objectStoreNames.contains('cached-data')) {
          db.createObjectStore('cached-data', { keyPath: 'key' });
        }

        // Pending mutations store
        if (!db.objectStoreNames.contains('pending-mutations')) {
          const store = db.createObjectStore('pending-mutations', {
            keyPath: 'id',
            autoIncrement: true,
          });
          store.createIndex('by-entity', 'entity');
        }

        // Sync status store
        if (!db.objectStoreNames.contains('sync-status')) {
          db.createObjectStore('sync-status', { keyPath: 'entity' });
        }
      },
    });
  }

  // Cache data
  async cacheData(key: string, data: any, ttlMinutes?: number): Promise<void> {
    if (!this.db) await this.init();

    await this.db!.put('cached-data', {
      key,
      data,
      timestamp: Date.now(),
      expiresAt: ttlMinutes ? Date.now() + ttlMinutes * 60 * 1000 : undefined,
    });
  }

  async getCachedData<T>(key: string): Promise<T | null> {
    if (!this.db) await this.init();

    const cached = await this.db!.get('cached-data', key);
    if (!cached) return null;

    // Check expiry
    if (cached.expiresAt && cached.expiresAt < Date.now()) {
      await this.db!.delete('cached-data', key);
      return null;
    }

    return cached.data as T;
  }

  // Pending mutations
  async addPendingMutation(mutation: Omit<OfflineDB['pending-mutations']['value'], 'id'>): Promise<number> {
    if (!this.db) await this.init();

    return await this.db!.add('pending-mutations', mutation as any);
  }

  async getPendingMutations(entity?: string): Promise<OfflineDB['pending-mutations']['value'][]> {
    if (!this.db) await this.init();

    if (entity) {
      return await this.db!.getAllFromIndex('pending-mutations', 'by-entity', entity);
    }
    return await this.db!.getAll('pending-mutations');
  }

  async removePendingMutation(id: number): Promise<void> {
    if (!this.db) await this.init();
    await this.db!.delete('pending-mutations', id);
  }

  async getPendingMutationCount(): Promise<number> {
    if (!this.db) await this.init();
    return await this.db!.count('pending-mutations');
  }

  // Sync status
  async getSyncStatus(entity: string): Promise<OfflineDB['sync-status']['value'] | null> {
    if (!this.db) await this.init();
    return (await this.db!.get('sync-status', entity)) || null;
  }

  async updateSyncStatus(entity: string, status: Partial<OfflineDB['sync-status']['value']>): Promise<void> {
    if (!this.db) await this.init();

    const current = (await this.getSyncStatus(entity)) || {
      entity,
      lastSyncedAt: 0,
      syncInProgress: false,
    };

    await this.db!.put('sync-status', { ...current, ...status });
  }

  // Clear all data
  async clear(): Promise<void> {
    if (!this.db) await this.init();

    const tx = this.db!.transaction(['cached-data', 'pending-mutations', 'sync-status'], 'readwrite');
    await Promise.all([
      tx.objectStore('cached-data').clear(),
      tx.objectStore('pending-mutations').clear(),
      tx.objectStore('sync-status').clear(),
    ]);
  }
}

export const offlineStore = new OfflineStore();
```

### 36.5 Offline-First Hook

```typescript
// hooks/useOfflineFirst.ts
import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { offlineStore } from '@/lib/offline/indexedDB';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';

interface UseOfflineFirstOptions<T> {
  queryKey: string[];
  fetchFn: () => Promise<T>;
  cacheKey: string;
  ttlMinutes?: number;
  enableOfflineMutations?: boolean;
}

export function useOfflineFirst<T>({
  queryKey,
  fetchFn,
  cacheKey,
  ttlMinutes = 60,
  enableOfflineMutations = true,
}: UseOfflineFirstOptions<T>) {
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
  const [pendingCount, setPendingCount] = useState(0);

  // Load cached data first
  const { data: cachedData, isLoading: isCacheLoading } = useQuery({
    queryKey: [...queryKey, 'cached'],
    queryFn: () => offlineStore.getCachedData<T>(cacheKey),
    staleTime: Infinity,
  });

  // Fetch fresh data when online
  const {
    data: freshData,
    isLoading: isFetching,
    error,
    refetch,
  } = useQuery({
    queryKey,
    queryFn: async () => {
      const data = await fetchFn();
      // Cache the fresh data
      await offlineStore.cacheData(cacheKey, data, ttlMinutes);
      return data;
    },
    enabled: isOnline,
    staleTime: ttlMinutes * 60 * 1000,
  });

  // Update pending count
  useEffect(() => {
    const updateCount = async () => {
      const count = await offlineStore.getPendingMutationCount();
      setPendingCount(count);
    };
    updateCount();
  }, []);

  // Sync pending mutations when back online
  useEffect(() => {
    if (isOnline && pendingCount > 0) {
      syncPendingMutations();
    }
  }, [isOnline, pendingCount]);

  const syncPendingMutations = async () => {
    const mutations = await offlineStore.getPendingMutations();

    for (const mutation of mutations) {
      try {
        // Execute mutation based on type
        // await executeMutation(mutation);
        await offlineStore.removePendingMutation(mutation.id!);
        setPendingCount((prev) => prev - 1);
      } catch (error) {
        console.error('Failed to sync mutation:', error);
      }
    }

    // Refetch to get latest data
    refetch();
  };

  // Determine which data to use
  const data = freshData ?? cachedData;
  const isLoading = isCacheLoading || (isOnline && isFetching && !cachedData);
  const isStale = !freshData && !!cachedData;

  return {
    data,
    isLoading,
    isStale,
    isOnline,
    error: isOnline ? error : null,
    pendingCount,
    refetch,
  };
}

// Hook for offline mutations
export function useOfflineMutation<TData, TVariables>({
  mutationFn,
  entity,
  onSuccess,
  onError,
}: {
  mutationFn: (variables: TVariables) => Promise<TData>;
  entity: string;
  onSuccess?: (data: TData) => void;
  onError?: (error: Error) => void;
}) {
  const isOnline = useOnlineStatus();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (variables: TVariables) => {
      if (isOnline) {
        // Online - execute immediately
        return await mutationFn(variables);
      } else {
        // Offline - queue for later
        const id = await offlineStore.addPendingMutation({
          type: 'create', // or determine from context
          entity,
          data: variables,
          timestamp: Date.now(),
          retries: 0,
        });

        // Return optimistic response
        return { id, queued: true, data: variables } as unknown as TData;
      }
    },
    onSuccess: (data, variables) => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: [entity] });
      onSuccess?.(data);
    },
    onError: (error: Error) => {
      onError?.(error);
    },
  });
}
```

### 36.6 Online Status Hook

```typescript
// hooks/useOnlineStatus.ts
import { useState, useEffect } from 'react';

export function useOnlineStatus(): boolean {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      // Trigger sync
      if ('serviceWorker' in navigator && 'sync' in window.registration) {
        navigator.serviceWorker.ready.then((registration) => {
          registration.sync.register('sync-requests');
        });
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}
```

### 36.7 PWA Manifest

```json
// public/manifest.json
{
  "name": "Hotel PMS",
  "short_name": "PMS",
  "description": "Hotel Property Management System",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#1a73e8",
  "orientation": "any",
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "screenshots": [
    {
      "src": "/screenshots/desktop.png",
      "sizes": "1280x720",
      "type": "image/png",
      "form_factor": "wide"
    },
    {
      "src": "/screenshots/mobile.png",
      "sizes": "390x844",
      "type": "image/png",
      "form_factor": "narrow"
    }
  ],
  "shortcuts": [
    {
      "name": "New Booking",
      "url": "/bookings/new",
      "icons": [{ "src": "/icons/booking.png", "sizes": "96x96" }]
    },
    {
      "name": "Check-in",
      "url": "/front-desk/check-in",
      "icons": [{ "src": "/icons/checkin.png", "sizes": "96x96" }]
    }
  ],
  "categories": ["business", "productivity"],
  "prefer_related_applications": false
}
```

### 36.8 Offline UI Components

```typescript
// components/OfflineIndicator.tsx
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import { useEffect, useState } from 'react';
import { offlineStore } from '@/lib/offline/indexedDB';
import { Wifi, WifiOff, Cloud, CloudOff } from 'lucide-react';

export function OfflineIndicator() {
  const isOnline = useOnlineStatus();
  const [pendingCount, setPendingCount] = useState(0);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const updateCount = async () => {
      const count = await offlineStore.getPendingMutationCount();
      setPendingCount(count);
    };

    updateCount();
    const interval = setInterval(updateCount, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!isOnline) {
      setShowBanner(true);
    } else if (pendingCount === 0) {
      // Hide after syncing
      setTimeout(() => setShowBanner(false), 3000);
    }
  }, [isOnline, pendingCount]);

  if (!showBanner) return null;

  return (
    <div
      className={`fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 p-4 rounded-lg shadow-lg z-50 ${
        isOnline ? 'bg-green-500' : 'bg-yellow-500'
      } text-white`}
    >
      <div className="flex items-center gap-3">
        {isOnline ? (
          <>
            <Wifi className="w-5 h-5" />
            <div>
              <p className="font-medium">Back Online</p>
              {pendingCount > 0 ? (
                <p className="text-sm opacity-90">Syncing {pendingCount} pending changes...</p>
              ) : (
                <p className="text-sm opacity-90">All changes synced</p>
              )}
            </div>
          </>
        ) : (
          <>
            <WifiOff className="w-5 h-5" />
            <div>
              <p className="font-medium">You're Offline</p>
              <p className="text-sm opacity-90">Changes will sync when back online</p>
              {pendingCount > 0 && (
                <p className="text-sm opacity-90">{pendingCount} changes pending</p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// components/SyncStatus.tsx
export function SyncStatus({ entity }: { entity: string }) {
  const [status, setStatus] = useState<{
    lastSyncedAt: number;
    syncInProgress: boolean;
  } | null>(null);

  useEffect(() => {
    const loadStatus = async () => {
      const s = await offlineStore.getSyncStatus(entity);
      setStatus(s);
    };
    loadStatus();
  }, [entity]);

  if (!status) return null;

  return (
    <div className="flex items-center gap-2 text-sm text-gray-500">
      {status.syncInProgress ? (
        <>
          <Cloud className="w-4 h-4 animate-pulse" />
          <span>Syncing...</span>
        </>
      ) : (
        <>
          <CloudOff className="w-4 h-4" />
          <span>
            Last synced: {new Date(status.lastSyncedAt).toLocaleTimeString()}
          </span>
        </>
      )}
    </div>
  );
}
```

### 36.9 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Cache Static First | Pre-cache static assets on install |
| 2 | Stale-While-Revalidate | Use SWR for dynamic content |
| 3 | Queue Mutations | Queue mutations when offline |
| 4 | Show Status | Always show online/offline status |
| 5 | Sync Indicator | Show pending sync count |
| 6 | Conflict Resolution | Handle sync conflicts gracefully |
| 7 | Selective Caching | Only cache what's needed offline |
| 8 | TTL Management | Set appropriate cache TTLs |

---

## Summary

| Standard | Key Points |
|----------|------------|
| #34 Data Import/Export | CSV/Excel support, validation, batch processing |
| #35 Email Templates | Jinja2 templates, tenant customization, logging |
| #36 Offline/PWA | Service Worker, IndexedDB, background sync |

---

*Last Updated: 2025-12-09*
