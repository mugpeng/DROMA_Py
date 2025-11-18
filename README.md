# DROMA-Py

[![Website](https://img.shields.io/badge/🌐_Website-droma01.github.io/DROMA-blue)](https://droma01.github.io/DROMA/)
[![License](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](https://opensource.org/licenses/MPL-2.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![DOI](https://img.shields.io/badge/DOI-10.1101%2F2024.15742800-blue)](https://doi.org/10.1101/2024.15742800)

**Python interface for DROMA (Drug Response Omics association MAp) database operations**

DROMA-Py provides a comprehensive Python interface for interacting with DROMA SQLite databases, offering both functional and object-oriented approaches for database operations, data retrieval, and name harmonization in precision oncology research.

## 🚀 Features

- **Database Management**: Connect, query, and manage DROMA SQLite databases
- **Data Retrieval**: Extract omics and drug response data with flexible filtering
- **Name Harmonization**: Intelligent matching of sample and drug names using fuzzy logic
- **Project Management**: Track and organize multi-omics datasets across projects
- **Dual Interface**: Both functional and object-oriented programming styles
- **Type Safety**: Full type hints and validation for reliable data operations

## 📦 Installation

### Using pip (recommended)

```bash
pip install droma-py
```

### From source

```bash
git clone https://github.com/droma01/droma
cd droma/250521-DROMA_package/250626-DROMA_py
pip install -e .
```

### Development installation

```bash
git clone https://github.com/droma01/droma
cd droma/250521-DROMA_package/250626-DROMA_py
pip install -e ".[dev]"
```

## 🔧 Quick Start

### Basic Database Connection

```python
import droma_py as droma

# Connect to database
con = droma.connect_droma_database("path/to/droma.sqlite")

# Or use object-oriented approach
with droma.DROMADatabase("path/to/droma.sqlite") as db:
    projects = db.list_tables()
    print(f"Found {len(projects)} tables")
```

### Data Retrieval

```python
# List available projects
projects = droma.list_droma_projects()
print(projects)

# Get sample annotations
sample_anno = droma.get_droma_annotation("sample", project_name="gCSI")

# List features for a specific data type
genes = droma.list_droma_features("gCSI", "mRNA", limit=100)

# Get specific feature data
brca1_data = droma.get_feature_from_database(
    "mRNA", "BRCA1", 
    data_sources=["gCSI", "CCLE"],
    data_type="CellLine"
)
```

### Name Harmonization

```python
# Check sample names against database
sample_names = ["MCF7", "HeLa", "A549_lung", "Unknown_Sample"]
name_mapping = droma.check_droma_sample_names(sample_names)
print(name_mapping[['original_name', 'harmonized_name', 'match_confidence']])

# Check drug names
drug_names = ["Tamoxifen", "cisplatin", "Doxorubicin"]
drug_mapping = droma.check_droma_drug_names(drug_names)
```

### Database Management

```python
import pandas as pd
import numpy as np

# Add new data to database
expr_data = pd.DataFrame(np.random.randn(100, 50))
expr_data.index = [f"gene_{i}" for i in range(100)]
expr_data.columns = [f"sample_{i}" for i in range(50)]

# Update database with new table
droma.update_droma_database(expr_data, "myproject_mRNA", overwrite=True)

# Update project metadata
droma.update_droma_projects("myproject", dataset_type="CellLine")

# Update annotations
droma.update_droma_annotation(
    "sample", name_mapping, "myproject",
    data_type="CellLine", tumor_type="breast cancer"
)
```

## 📊 Advanced Usage

### Object-Oriented Interface

```python
from droma_py import DROMADatabase

# Use as context manager
with DROMADatabase("path/to/droma.sqlite") as db:
    # Get all tables
    tables = db.list_tables()
    
    # Execute custom queries
    result = db.fetchall("SELECT COUNT(*) FROM sample_anno WHERE DataType = ?", ("CellLine",))
    
    # Check table existence
    if db.table_exists("gCSI_mRNA"):
        print("gCSI mRNA data is available")
```

### Filtering and Complex Queries

```python
# Get data with multiple filters
cell_line_samples = droma.list_droma_samples(
    "gCSI", 
    data_type="CellLine",
    tumor_type="breast cancer",
    pattern="^MCF"
)

# Get features matching pattern
cancer_genes = droma.list_droma_features(
    "gCSI", "mRNA",
    pattern="^(BRCA|TP53|EGFR)",
    limit=50
)

# Complex annotation queries
annotations = droma.get_droma_annotation(
    "sample",
    project_name="gCSI",
    data_type="CellLine",
    limit=100
)
```

## 🛠️ API Reference

### Core Functions

#### Database Connection
- `connect_droma_database(db_path, set_global=True)` - Connect to database
- `close_droma_database(connection=None)` - Close database connection

#### Data Retrieval
- `get_feature_from_database(select_feas_type, select_feas="all", ...)` - Get feature data
- `list_droma_features(project_name, data_sources, ...)` - List available features
- `list_droma_samples(project_name, ...)` - List available samples
- `get_droma_annotation(anno_type, ...)` - Get annotation data

#### Database Management
- `update_droma_database(obj, table_name, ...)` - Add/update tables
- `list_droma_database_tables(pattern=None, ...)` - List database tables
- `list_droma_projects(...)` - List projects
- `update_droma_projects(project_name=None, ...)` - Update project metadata
- `update_droma_annotation(anno_type, name_mapping, ...)` - Update annotations

#### Name Harmonization
- `check_droma_sample_names(sample_names, ...)` - Check and harmonize sample names
- `check_droma_drug_names(drug_names, ...)` - Check and harmonize drug names

### Classes

#### DROMADatabase
Object-oriented interface for database operations.

```python
db = DROMADatabase("path/to/database.sqlite")
db.connect()
result = db.fetchall("SELECT * FROM projects")
db.close()
```

**Methods:**
- `connect()` - Establish connection
- `close()` - Close connection
- `execute(query, params=None)` - Execute SQL query
- `fetchall(query, params=None)` - Fetch all results
- `fetchone(query, params=None)` - Fetch one result
- `list_tables()` - List all tables
- `table_exists(table_name)` - Check if table exists

## 🔍 Data Types and Formats

### Supported Data Types
- **mRNA**: Gene expression data
- **cnv**: Copy number variation
- **meth**: DNA methylation
- **proteinrppa**: Protein RPPA data
- **proteinms**: Protein mass spectrometry
- **drug**: Drug response data
- **mutation_gene**: Gene-level mutations
- **mutation_site**: Site-specific mutations
- **fusion**: Gene fusion data

### Sample Types
- **CellLine**: Cancer cell lines
- **PDO**: Patient-derived organoids
- **PDC**: Patient-derived cells
- **PDX**: Patient-derived xenografts

## 🧪 Examples

See the `examples/` directory for comprehensive usage examples:

- `basic_usage.py` - Basic database operations
- `data_analysis.py` - Data retrieval and analysis
- `name_harmonization.py` - Name matching examples
- `batch_processing.py` - Bulk data operations

## 🤝 Integration with R

DROMA-Py is designed to work seamlessly with the R DROMA ecosystem:

- Compatible database formats
- Consistent function naming and parameters
- Cross-platform data sharing

```python
# Python: Export data for R
data = droma.get_feature_from_database("mRNA", "BRCA1")
pd.DataFrame(data['gCSI']).to_csv("brca1_data.csv")

# R: Import and use
# data <- read.csv("brca1_data.csv")
```

## 📈 Performance Tips

1. **Use context managers** for automatic connection cleanup
2. **Batch operations** when updating multiple tables
3. **Filter early** to reduce data transfer
4. **Index frequently queried columns** in custom tables
5. **Use specific queries** instead of loading entire tables

## 🐛 Error Handling

```python
from droma_py.exceptions import DROMAError, DROMAConnectionError

try:
    con = droma.connect_droma_database("nonexistent.db")
except DROMAConnectionError as e:
    print(f"Connection failed: {e}")
except DROMAError as e:
    print(f"DROMA error: {e}")
```

## 📝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
git clone https://github.com/droma01/droma
cd droma/250521-DROMA_package/250626-DROMA_py
pip install -e ".[dev]"
pre-commit install
```

### Running Tests

```bash
pytest tests/
pytest --cov=droma_py tests/  # with coverage
```

## 📄 License

This project is licensed under the Mozilla Public License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- University of Macau Precision Oncology Research Team
- Contributors to the DROMA ecosystem
- Open source community

## 📞 Support

- **Website**: [https://droma01.github.io/DROMA/](https://droma01.github.io/DROMA/)
- **Issues**: [GitHub Issues](https://github.com/droma01/droma/issues)
- **Email**: contact@droma.io

## 📚 Citation

If you use DROMA-Py in your research, please cite:

```bibtex
@article{droma2024,
  title={DROMA: A Comprehensive Platform for Drug Response and Omics Analysis},
  author={University of Macau Precision Oncology Research Team},
  journal={bioRxiv},
  year={2024},
  doi={10.1101/2024.15742800}
}
```

---

Part of the **DROMA Ecosystem**:
- [DROMA-R](../250513-DROMA_R/) - R package for statistical analysis
- [DROMA-Set](../250522-DROMA_Set/) - R data management framework  
- [DROMA-DB](../../250520-DROMA_DB/) - Database creation and management
- [DROMA-Web](../../250511-DROMA_Webserver/) - Interactive web interface
- [DROMA-MCP](../../250319-DROMA_AI/DROMA_MCP/) - AI-powered analysis tools 