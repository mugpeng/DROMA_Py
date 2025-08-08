# DROMA-Py API Reference

DROMA-Py is a Python package that provides Python bindings for interacting with DROMA (Drug Response Omics association MAp) SQLite databases. This reference documents all public functions available for use in other projects.

## Installation & Import

```python
import droma_py as dp
# or import specific functions
from droma_py import connect_droma_database, get_feature_from_database
```

## Core Database Connection

### DROMADatabase (Class)
Object-oriented interface for DROMA database operations.

```python
class DROMADatabase:
    def __init__(self, db_path: Union[str, Path]) -> None
    def connect(self) -> sqlite3.Connection
    def close(self) -> None
    def execute(self, query: str, params: Optional[tuple] = None) -> sqlite3.Cursor
    def fetchall(self, query: str, params: Optional[tuple] = None) -> list
    def fetchone(self, query: str, params: Optional[tuple] = None) -> Optional[sqlite3.Row]
    def list_tables(self) -> list[str]
    def table_exists(self, table_name: str) -> bool
```

**Usage:**
```python
# As context manager (recommended)
with dp.DROMADatabase("path/to/droma.sqlite") as db:
    tables = db.list_tables()
    
# Manual connection management
db = dp.DROMADatabase("path/to/droma.sqlite")
db.connect()
projects = db.list_tables()
db.close()
```

### connect_droma_database()
Establish a connection to the DROMA SQLite database.

```python
connect_droma_database(
    db_path: Union[str, Path] = None,
    set_global: bool = True
) -> sqlite3.Connection
```

**Parameters:**
- `db_path`: Path to the SQLite database file. If None, uses default path
- `set_global`: Whether to set this as the global connection

**Usage:**
```python
con = dp.connect_droma_database("path/to/droma.sqlite")
```

### close_droma_database()
Close the connection to the DROMA database.

```python
close_droma_database(connection: Optional[sqlite3.Connection] = None) -> bool
```

**Parameters:**
- `connection`: Database connection to close. If None, closes global connection

**Usage:**
```python
dp.close_droma_database(con)
```

## Data Retrieval Functions

### get_feature_from_database()
Retrieve specific feature data from the DROMA database based on selection criteria.

```python
get_feature_from_database(
    select_feas_type: str,
    select_feas: Union[str, List[str]] = "all",
    data_sources: Union[str, List[str]] = "all",
    data_type: Union[str, List[str]] = "all",
    tumor_type: Union[str, List[str]] = "all",
    connection: Optional[sqlite3.Connection] = None
) -> Dict[str, Union[pd.DataFrame, pd.Series, List[str]]]
```

**Parameters:**
- `select_feas_type`: The type of feature to select (e.g., "mRNA", "cnv", "drug")
- `select_feas`: The specific feature(s) to select. Can be single feature, list, or "all"
- `data_sources`: Data sources to select from (e.g., "gCSI", ["CCLE", "GDSC"])
- `data_type`: Filter by data type ("all", "CellLine", "PDO", "PDC", "PDX")
- `tumor_type`: Filter by tumor type ("all" or specific tumor types)
- `connection`: Optional database connection

**Usage:**
```python
# Get all mRNA data from gCSI
data = dp.get_feature_from_database("mRNA", data_sources=["gCSI"])

# Get specific genes from multiple sources
gene_data = dp.get_feature_from_database(
    "mRNA", 
    select_feas=["BRCA1", "TP53", "EGFR"], 
    data_sources=["gCSI", "CCLE"]
)

# Get drug response data for cell lines
drug_data = dp.get_feature_from_database("drug", data_type="CellLine")
```

### list_droma_features()
List all available features for a specific project and data type.

```python
list_droma_features(
    project_name: str,
    data_sources: str,
    data_type: str = "all",
    tumor_type: str = "all",
    connection: Optional[sqlite3.Connection] = None,
    limit: Optional[int] = None,
    pattern: Optional[str] = None
) -> List[str]
```

**Parameters:**
- `project_name`: Name of the project (e.g., "gCSI", "CCLE")
- `data_sources`: Type of data to query (e.g., "mRNA", "cnv", "drug")
- `data_type`: Filter by data type ("all", "CellLine", "PDO", "PDC", "PDX")
- `tumor_type`: Filter by tumor type ("all" or specific tumor type)
- `connection`: Optional database connection
- `limit`: Maximum number of features to return
- `pattern`: Optional regex pattern to filter feature names

**Usage:**
```python
# List all genes in gCSI mRNA data
genes = dp.list_droma_features("gCSI", "mRNA")

# List all drugs in gCSI drug response data
drugs = dp.list_droma_features("gCSI", "drug")

# List genes matching a pattern
brca_genes = dp.list_droma_features("gCSI", "mRNA", pattern="^BRCA")
```

### list_droma_samples()
List all available samples for a specific project.

```python
list_droma_samples(
    project_name: str,
    data_sources: str = "all",
    data_type: str = "all",
    tumor_type: str = "all",
    connection: Optional[sqlite3.Connection] = None,
    limit: Optional[int] = None,
    pattern: Optional[str] = None
) -> List[str]
```

**Parameters:**
- `project_name`: Name of the project (e.g., "gCSI", "CCLE")
- `data_sources`: Filter by data sources ("all" or specific data type)
- `data_type`: Filter by data type ("all", "CellLine", "PDO", "PDC", "PDX")
- `tumor_type`: Filter by tumor type ("all" or specific tumor type)
- `connection`: Optional database connection
- `limit`: Maximum number of samples to return
- `pattern`: Optional regex pattern to filter sample names

**Usage:**
```python
# List all samples for gCSI project
samples = dp.list_droma_samples("gCSI")

# List only cell line samples
cell_lines = dp.list_droma_samples("gCSI", data_type="CellLine")

# List samples with mRNA data
mrna_samples = dp.list_droma_samples("gCSI", data_sources="mRNA")
```

### get_droma_annotation()
Retrieve annotation data from either sample_anno or drug_anno tables.

```python
get_droma_annotation(
    anno_type: str,
    project_name: Optional[str] = None,
    ids: Optional[List[str]] = None,
    data_type: str = "all",
    tumor_type: str = "all",
    connection: Optional[sqlite3.Connection] = None,
    limit: Optional[int] = None
) -> pd.DataFrame
```

**Parameters:**
- `anno_type`: Type of annotation to retrieve ("sample" or "drug")
- `project_name`: Optional project name to filter results
- `ids`: Optional specific IDs to retrieve
- `data_type`: For samples: filter by data type ("all", "CellLine", "PDO", "PDC", "PDX")
- `tumor_type`: For samples: filter by tumor type ("all" or specific type)
- `connection`: Optional database connection
- `limit`: Maximum number of records to return

**Usage:**
```python
# Get all sample annotations
sample_anno = dp.get_droma_annotation("sample")

# Get sample annotations for gCSI project only
gCSI_samples = dp.get_droma_annotation("sample", project_name="gCSI")

# Get annotations for specific samples
specific_samples = dp.get_droma_annotation("sample", ids=["22RV1", "2313287"])

# Get all drug annotations
drug_anno = dp.get_droma_annotation("drug")
```

## Database Management Functions

### update_droma_database()
Add or update a table in the DROMA database with a new object.

```python
update_droma_database(
    obj: Union[pd.DataFrame, np.ndarray],
    table_name: str,
    overwrite: bool = False,
    connection: Optional[sqlite3.Connection] = None
) -> bool
```

**Parameters:**
- `obj`: The object to add to the database (DataFrame or numpy array)
- `table_name`: The name to use for the table in the database
- `overwrite`: Whether to overwrite if table already exists
- `connection`: Optional database connection

**Usage:**
```python
import pandas as pd
import numpy as np

expr_data = pd.DataFrame(np.random.randn(10, 10))
expr_data.index = [f"gene{i}" for i in range(10)]
expr_data.columns = [f"sample{i}" for i in range(10)]

success = dp.update_droma_database(expr_data, "myproject_mRNA", overwrite=True)
```

### list_droma_database_tables()
List available tables in DROMA database.

```python
list_droma_database_tables(
    pattern: Optional[str] = None,
    connection: Optional[sqlite3.Connection] = None
) -> pd.DataFrame
```

**Parameters:**
- `pattern`: Optional regex pattern to filter table names
- `connection`: Optional database connection

**Usage:**
```python
tables = dp.list_droma_database_tables()
print(tables[['table_name', 'data_type', 'feature_type']])
```

### list_droma_projects()
List all projects available in the DROMA database.

```python
list_droma_projects(
    connection: Optional[sqlite3.Connection] = None,
    show_names_only: bool = False,
    project_data_types: Optional[str] = None
) -> Union[pd.DataFrame, List[str]]
```

**Parameters:**
- `connection`: Optional database connection
- `show_names_only`: If True, returns only a list of project names
- `project_data_types`: Project name to get specific data types for

**Usage:**
```python
projects = dp.list_droma_projects()
project_names = dp.list_droma_projects(show_names_only=True)
data_types = dp.list_droma_projects(project_data_types="gCSI")
```

### update_droma_projects()
Update or add project metadata to the projects table.

```python
update_droma_projects(
    project_name: Optional[str] = None,
    dataset_type: Optional[str] = None,
    connection: Optional[sqlite3.Connection] = None,
    create_table: bool = True
) -> bool
```

**Parameters:**
- `project_name`: Name of the project to update. If None, updates all projects
- `dataset_type`: Dataset type to assign (e.g., "CellLine", "PDX", "PDO")
- `connection`: Optional database connection
- `create_table`: Whether to create the projects table if it doesn't exist

**Usage:**
```python
# Update specific project
dp.update_droma_projects("gCSI", dataset_type="CellLine")

# Update all projects
dp.update_droma_projects()
```

### update_droma_annotation()
Add harmonized sample or drug names to the corresponding annotation tables.

```python
update_droma_annotation(
    anno_type: str,
    name_mapping: pd.DataFrame,
    project_name: str,
    data_type: Union[str, List[str]] = None,
    tumor_type: Union[str, List[str]] = None,
    patient_id: Union[str, List[str]] = None,
    gender: Union[str, List[str]] = None,
    age: Union[int, float, List[Union[int, float]]] = None,
    full_ethnicity: Union[str, List[str]] = None,
    simple_ethnicity: Union[str, List[str]] = None,
    connection: Optional[sqlite3.Connection] = None
) -> bool
```

**Parameters:**
- `anno_type`: Type of annotation to update ("sample" or "drug")
- `name_mapping`: DataFrame with name mappings (original_name, new_name, match_confidence)
- `project_name`: Project name to assign to new entries
- `data_type`: Data type(s) for samples (can be single value or list)
- `tumor_type`: Tumor type(s) for samples (can be single value or list)
- `patient_id`: Patient ID(s) for samples (can be single value or list)
- `gender`: Gender(s) for samples (can be single value or list)
- `age`: Age(s) for samples (can be single value or list)
- `full_ethnicity`: Full ethnicity/ethnicities for samples (can be single value or list)
- `simple_ethnicity`: Simple ethnicity/ethnicities for samples (can be single value or list)
- `connection`: Optional database connection

**Usage:**
```python
# Update sample annotations
mapping = dp.check_droma_sample_names(sample_names)
dp.update_droma_annotation(
    "sample", mapping, "MyProject",
    data_type="CellLine", tumor_type="breast cancer"
)
```

## Name Harmonization Functions

### check_droma_sample_names()
Check sample names against the sample_anno table and provide harmonized mappings.

```python
check_droma_sample_names(
    sample_names: List[str],
    connection: Optional[sqlite3.Connection] = None,
    max_distance: float = 0.2,
    min_name_length: int = 5
) -> pd.DataFrame
```

**Parameters:**
- `sample_names`: List of sample names to check and harmonize
- `connection`: Optional database connection
- `max_distance`: Maximum distance for fuzzy matching (default: 0.2)
- `min_name_length`: Minimum name length for partial matching (default: 5)

**Returns:** DataFrame with columns: original_name, cleaned_name, harmonized_name, match_type, match_confidence, new_name

**Usage:**
```python
sample_names = ["MCF7", "HeLa", "A549_lung", "Unknown_Sample"]
name_mapping = dp.check_droma_sample_names(sample_names)
print(name_mapping[['original_name', 'harmonized_name', 'match_confidence']])
```

### check_droma_drug_names()
Check drug names against the drug_anno table and provide harmonized mappings.

```python
check_droma_drug_names(
    drug_names: List[str],
    connection: Optional[sqlite3.Connection] = None,
    max_distance: float = 0.2,
    min_name_length: int = 5,
    keep_long_names_threshold: int = 17
) -> pd.DataFrame
```

**Parameters:**
- `drug_names`: List of drug names to check and harmonize
- `connection`: Optional database connection
- `max_distance`: Maximum distance for fuzzy matching (default: 0.2)
- `min_name_length`: Minimum name length for partial matching (default: 5)
- `keep_long_names_threshold`: Names longer than this will be kept as original (default: 17)

**Returns:** DataFrame with columns: original_name, cleaned_name, harmonized_name, match_type, match_confidence, new_name

**Usage:**
```python
drug_names = ["Tamoxifen", "cisplatin", "Doxorubicin_HCl", "Unknown_Compound"]
name_mapping = dp.check_droma_drug_names(drug_names)
print(name_mapping[['original_name', 'harmonized_name', 'match_confidence']])
```

## Exception Classes

The package defines several custom exceptions for better error handling:

- `DROMAError`: Base exception class for all DROMA-related errors
- `DROMAConnectionError`: Raised when database connection operations fail
- `DROMADataError`: Raised when data operations fail (e.g., invalid data format, missing data)
- `DROMAValidationError`: Raised when input validation fails
- `DROMAQueryError`: Raised when database queries fail
- `DROMATableError`: Raised when table operations fail (e.g., table not found, schema mismatch)

## Complete Usage Example

```python
import droma_py as dp
import pandas as pd

# Connect to database
dp.connect_droma_database("path/to/droma.sqlite")

# List available projects
projects = dp.list_droma_projects(show_names_only=True)
print("Available projects:", projects)

# Get sample information for a project
samples = dp.list_droma_samples("gCSI", data_type="CellLine")
print(f"Found {len(samples)} cell line samples in gCSI")

# Get gene expression data for specific genes
genes_of_interest = ["BRCA1", "TP53", "EGFR"]
expression_data = dp.get_feature_from_database(
    "mRNA", 
    select_feas=genes_of_interest,
    data_sources=["gCSI"],
    data_type="CellLine"
)

# Get drug response data
drug_data = dp.get_feature_from_database(
    "drug", 
    data_sources=["gCSI"],
    data_type="CellLine"
)

# Harmonize sample names
new_sample_names = ["MCF7", "HeLa", "unknown_sample"]
harmonized = dp.check_droma_sample_names(new_sample_names)
print(harmonized)

# Close connection
dp.close_droma_database()
```

## Notes for AI Assistants

When using this API in other projects:

1. **Always establish a database connection first** using `connect_droma_database()` or `DROMADatabase` class
2. **Use the harmonization functions** to check sample/drug names before data analysis
3. **Filter data appropriately** using data_type and tumor_type parameters
4. **Handle exceptions** using the provided exception classes
5. **Check data availability** using the list functions before attempting to retrieve specific features
6. **Close connections** properly when done to avoid resource leaks

The package provides both functional and object-oriented interfaces. Use the `DROMADatabase` class for more complex operations or when you need fine-grained control over the connection.