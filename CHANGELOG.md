# Changelog

All notable changes to the DROMA-Py project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-12-28

### Added
- Initial release of DROMA-Py package
- Complete Python interface for DROMA database operations
- Database connection and management functions (`connect_droma_database`, `close_droma_database`)
- Data retrieval functions (`get_feature_from_database`, `list_droma_features`, `list_droma_samples`)
- Annotation management (`get_droma_annotation`, `update_droma_annotation`)
- Database management functions (`update_droma_database`, `list_droma_projects`)
- Name harmonization system (`check_droma_sample_names`, `check_droma_drug_names`)
- Comprehensive exception hierarchy (`DROMAError` and subclasses)
- Support for all DROMA data types (mRNA, CNV, methylation, proteins, drugs, mutations, fusions)
- Cross-platform compatibility with R DROMA ecosystem
- Professional packaging with type hints and documentation

### Features
- **Dual Interface**: Both functional (mirroring R) and object-oriented approaches
- **Type Safety**: Full type hints for better IDE support and error detection
- **Error Handling**: Custom exception hierarchy with detailed error messages
- **Fuzzy Matching**: Intelligent name harmonization using rapidfuzz
- **Pandas Integration**: DataFrames as primary data structure
- **Performance**: Direct SQLite access for optimal performance
- **Compatibility**: Same database format as R DROMA packages

### Documentation
- Comprehensive README with installation and usage examples
- 4 detailed example scripts demonstrating all major features
- Complete API documentation with type hints
- Integration guide for R/Python workflows

### Examples Included
- `basic_usage.py`: Database connection and basic operations
- `data_analysis.py`: Comprehensive data analysis workflow
- `name_harmonization.py`: Sample and drug name harmonization
- `batch_processing.py`: Bulk operations and performance monitoring

### Dependencies
- pandas >= 1.3.0
- numpy >= 1.21.0
- rapidfuzz >= 3.0.0
- typing-extensions >= 4.0.0 (Python < 3.10)

### Development
- Modern Python packaging with pyproject.toml
- Code quality tools: black, isort, flake8, mypy
- Testing framework setup with pytest
- Pre-commit hooks for code quality
- Mozilla Public License 2.0

## [Unreleased]

### Planned
- Comprehensive test suite
- Asynchronous database operations
- Query result caching
- Visualization functions
- Sphinx documentation site
- CI/CD pipeline 