"""
DROMA-Py: Python interface for DROMA database operations.

This package provides Python bindings for interacting with DROMA (Drug Response 
Omics association MAp) SQLite databases, offering both functional and object-oriented
interfaces for database operations, data retrieval, and name harmonization.
"""

__version__ = "0.1.0"
__author__ = "University of Macau Precision Oncology Research Team"
__email__ = "contact@droma.io"
__license__ = "MPL-2.0"

# Core database connection and management
from .database import (
    DROMADatabase,
    connect_droma_database,
    close_droma_database,
)

# Data retrieval and manipulation
from .data import (
    get_feature_from_database,
    list_droma_features,
    list_droma_samples,
    get_droma_annotation,
)

# Database management
from .management import (
    update_droma_database,
    update_droma_projects,
    update_droma_annotation,
    list_droma_database_tables,
    list_droma_projects,
)

# Name harmonization
from .harmonization import (
    check_droma_sample_names,
    check_droma_drug_names,
)

# Exceptions
from .exceptions import (
    DROMAError,
    DROMAConnectionError,
    DROMADataError,
    DROMAValidationError,
    DROMAQueryError,
    DROMATableError,
)

__all__ = [
    # Core classes
    "DROMADatabase",
    # Connection functions
    "connect_droma_database",
    "close_droma_database",
    # Data functions
    "get_feature_from_database",
    "list_droma_features",
    "list_droma_samples",
    "get_droma_annotation",
    # Management functions
    "update_droma_database",
    "update_droma_projects",
    "update_droma_annotation",
    "list_droma_database_tables",
    "list_droma_projects",
    # Name harmonization
    "check_droma_sample_names",
    "check_droma_drug_names",
    # Exceptions
    "DROMAError",
    "DROMAConnectionError",
    "DROMADataError",
    "DROMAValidationError",
    "DROMAQueryError",
    "DROMATableError",
] 