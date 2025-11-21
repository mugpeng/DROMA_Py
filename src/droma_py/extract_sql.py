"""
SQLite matrix storage and retrieval functions for DROMA-Py.

This module provides functions for storing matrices in SQLite databases and
retrieving them, with efficient indexing and metadata management.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Union, List
import logging
import re

from .exceptions import (
    DROMAConnectionError,
    DROMADataError,
    DROMAValidationError,
    DROMATableError,
)

logger = logging.getLogger(__name__)


def _validate_table_name(table_name: str) -> None:
    """
    Validate table name for SQL injection safety.
    
    Args:
        table_name: Table name to validate
    
    Raises:
        DROMAValidationError: If table name is invalid
    """
    if not isinstance(table_name, str) or len(table_name) == 0:
        raise DROMAValidationError(
            "table_name must be a non-empty string"
        )
    
    # SQLite table names must start with letter/underscore and contain only
    # letters, numbers, and underscores
    if re.match(r"^[0-9]|[^a-zA-Z0-9_]", table_name):
        raise DROMAValidationError(
            f"Invalid table name '{table_name}'",
            "Table names must start with letter/underscore and contain only letters, numbers, underscores"
        )


def store_matrices_in_database(
    db_path: Union[str, Path],
    matrix: Union[pd.DataFrame, np.ndarray],
    table_name: str
) -> Path:
    """
    Store a matrix or DataFrame in a SQLite database with efficient indexing.
    
    Converts and stores a matrix or DataFrame in a SQLite database. Row names
    are preserved as feature_id column. The function creates the database
    directory if needed and creates an index on feature_id for efficient queries.
    
    Args:
        db_path: Path where the SQLite database file should be created or updated
        matrix: Matrix (numpy array) or DataFrame to store. Must have row and column names.
        table_name: Name of the table to create in database. Must start with letter/underscore
                   and contain only letters, numbers, underscores.
    
    Returns:
        Path: Path to the database file
    
    Raises:
        DROMAValidationError: If inputs are invalid or table name is invalid
        DROMADataError: If matrix processing fails
        DROMAConnectionError: If database connection fails
    
    Examples:
        >>> import numpy as np
        >>> import pandas as pd
        >>> 
        >>> # Store numpy matrix
        >>> exp_matrix = np.random.randn(100, 10)
        >>> rownames = [f"Gene_{i}" for i in range(100)]
        >>> colnames = [f"Sample_{i}" for i in range(10)]
        >>> exp_df = pd.DataFrame(exp_matrix, index=rownames, columns=colnames)
        >>> 
        >>> db_path = store_matrices_in_database(
        ...     db_path="expression_data.sqlite",
        ...     matrix=exp_df,
        ...     table_name="expression"
        ... )
        >>> 
        >>> # Store DataFrame directly
        >>> df = pd.DataFrame(np.random.rand(100, 10), 
        ...                   index=[f"Gene_{i}" for i in range(100)],
        ...                   columns=[f"Sample_{i}" for i in range(10)])
        >>> store_matrices_in_database("data.sqlite", df, "methylation")
    """
    # First principles validation: check fundamental requirements
    if not isinstance(db_path, (str, Path)):
        raise DROMAValidationError(
            "db_path must be a string or Path object",
            f"Got type: {type(db_path)}"
        )
    
    db_path = Path(db_path)
    
    if matrix is None:
        raise DROMAValidationError(
            "matrix is required and must be a DataFrame or numpy array"
        )
    
    if not isinstance(matrix, (pd.DataFrame, np.ndarray)):
        raise DROMAValidationError(
            "matrix must be a pandas DataFrame or numpy array",
            f"Got type: {type(matrix)}"
        )
    
    # Validate table name
    _validate_table_name(table_name)
    
    # Create database directory if needed
    db_dir = db_path.parent
    if not db_dir.exists():
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {db_dir}")
    
    # Connect to database with proper cleanup
    logger.info(f"Connecting to database: {db_path}")
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        raise DROMAConnectionError(
            f"Failed to connect to database: {db_path}",
            str(e)
        )
    
    try:
        # Process matrix
        logger.info(f"Processing matrix: {table_name}")
        
        # Convert to DataFrame if numpy array
        if isinstance(matrix, np.ndarray):
            df = pd.DataFrame(matrix)
        else:
            df = matrix.copy()
        
        # Validate and generate row names if missing
        if df.index.name is None:
            # Check if index is generic integer sequence
            if (isinstance(df.index, pd.RangeIndex) or 
                (isinstance(df.index, pd.Index) and 
                 df.index.dtype == 'int64' and 
                 len(df.index) > 0 and
                 df.index[0] == 0 and 
                 df.index[-1] == len(df.index) - 1)):
                df.index = [f"feature_{i}" for i in range(len(df))]
                logger.warning("Matrix has no row names. Generated generic names.")
        
        # Validate and generate column names if missing
        if len(df.columns) > 0:
            # Check if columns are unnamed (pandas default)
            if all(str(col).startswith("Unnamed:") or 
                   (isinstance(col, int) and col == i) 
                   for i, col in enumerate(df.columns)):
                df.columns = [f"sample_{i}" for i in range(len(df.columns))]
                logger.warning("Matrix has no column names. Generated generic names.")
        
        # Reset index to create feature_id column
        # This preserves the index values as a column
        df = df.reset_index()
        
        # Rename the index column to feature_id
        # After reset_index(), the old index becomes the first column
        if df.columns[0] != "feature_id":
            df.rename(columns={df.columns[0]: "feature_id"}, inplace=True)
        
        # Ensure feature_id is first column (should already be, but double-check)
        if "feature_id" not in df.columns:
            raise DROMADataError(
                "Failed to create feature_id column",
                "Index reset operation failed"
            )
        
        cols = ["feature_id"] + [col for col in df.columns if col != "feature_id"]
        df = df[cols]
        
        # Store dimensions for logging
        n_features = len(df)
        n_samples = len(df.columns) - 1  # Subtract 1 for feature_id column
        
        # Write to database (overwrite if exists)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        
        # Create index on feature_id for efficient queries
        index_name = f"idx_{table_name}_feature_id"
        index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} (feature_id)"
        conn.execute(index_sql)
        conn.commit()
        
        logger.info(f"Stored {n_features} features × {n_samples} samples with feature_id index")
        
    except Exception as e:
        conn.rollback()
        raise DROMADataError(
            f"Failed to process matrix '{table_name}'",
            str(e)
        )
    finally:
        conn.close()
    
    # Final summary
    logger.info(f"Database storage complete. Table '{table_name}' created.")
    
    return db_path


def retrieve_matrix_from_database(
    db_path: Union[str, Path],
    table_name: str,
    features: Optional[List[str]] = None
) -> Optional[pd.DataFrame]:
    """
    Retrieve a matrix from SQLite database, reconstructing the original format.
    
    Loads a matrix from SQLite database, reconstructing the original matrix format
    with row names from feature_id column. Returns a DataFrame with feature_id
    values as index.
    
    Args:
        db_path: Path to the SQLite database file
        table_name: Name of the table containing the matrix data
        features: Optional list of specific feature IDs to retrieve. If None, retrieves all
    
    Returns:
        pd.DataFrame: DataFrame with feature_id values as index, or None if no data found
    
    Raises:
        DROMAConnectionError: If database file not found or connection fails
        DROMATableError: If table not found in database
        DROMAValidationError: If inputs are invalid
        DROMADataError: If data retrieval fails
    
    Examples:
        >>> # Retrieve entire matrix
        >>> exp_matrix = retrieve_matrix_from_database(
        ...     "expression_data.sqlite", 
        ...     "expression"
        ... )
        >>> 
        >>> # Retrieve specific features
        >>> subset_matrix = retrieve_matrix_from_database(
        ...     "expression_data.sqlite", 
        ...     "expression", 
        ...     features=["Gene_1", "Gene_5", "Gene_10"]
        ... )
    """
    # Validate inputs
    if not isinstance(db_path, (str, Path)):
        raise DROMAValidationError(
            "db_path must be a string or Path object"
        )
    
    db_path = Path(db_path)
    
    if not db_path.exists():
        raise DROMAConnectionError(
            f"Database file does not exist: {db_path}",
            "Check the file path"
        )
    
    # Validate table name
    _validate_table_name(table_name)
    
    if features is not None and not isinstance(features, (list, tuple)):
        raise DROMAValidationError(
            "features must be a list or tuple of feature IDs, or None"
        )
    
    # Connect to database
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        raise DROMAConnectionError(
            f"Failed to connect to database: {db_path}",
            str(e)
        )
    
    try:
        # Check if table exists
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if cursor.fetchone() is None:
            # Get list of available tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            available_tables = [row[0] for row in cursor.fetchall()]
            raise DROMATableError(
                f"Table '{table_name}' not found in database",
                f"Available tables: {', '.join(available_tables) if available_tables else 'none'}"
            )
        
        # Build query
        if features is None:
            query = f"SELECT * FROM {table_name}"
            params = None
        else:
            if not all(isinstance(f, str) for f in features):
                raise DROMAValidationError(
                    "All features must be strings"
                )
            # Use parameterized query to prevent SQL injection
            placeholders = ", ".join(["?" for _ in features])
            query = f"SELECT * FROM {table_name} WHERE feature_id IN ({placeholders})"
            params = features
        
        # Execute query
        try:
            if params:
                df = pd.read_sql_query(query, conn, params=params)
            else:
                df = pd.read_sql_query(query, conn)
            
            if df.empty:
                logger.warning(f"No data retrieved for table '{table_name}'")
                return None
            
            # Check if feature_id column exists
            if "feature_id" not in df.columns:
                raise DROMADataError(
                    f"Table '{table_name}' does not have a feature_id column",
                    f"Available columns: {', '.join(df.columns)}"
                )
            
            # Set feature_id as index
            df = df.set_index("feature_id")
            
            logger.info(f"Retrieved matrix: {len(df)} features × {len(df.columns)} samples")
            
            return df
            
        except pd.errors.DatabaseError as e:
            raise DROMADataError(
                f"Failed to retrieve matrix from table '{table_name}'",
                str(e)
            )
    
    finally:
        conn.close()


def list_matrix_tables(
    db_path: Union[str, Path]
) -> pd.DataFrame:
    """
    List all matrix tables stored in the database along with metadata.
    
    Lists all matrix tables stored in the database along with metadata including
    dimensions (number of features and samples) for each table.
    
    Args:
        db_path: Path to the SQLite database file
    
    Returns:
        pd.DataFrame: DataFrame with table information including table_name,
                      n_features, and n_samples columns. Empty DataFrame if no tables found.
    
    Raises:
        DROMAConnectionError: If database file not found or connection fails
        DROMAValidationError: If db_path is invalid
    
    Examples:
        >>> # List all matrices in database
        >>> table_info = list_matrix_tables("expression_data.sqlite")
        >>> print(table_info)
    """
    # Validate inputs
    if not isinstance(db_path, (str, Path)):
        raise DROMAValidationError(
            "db_path must be a string or Path object"
        )
    
    db_path = Path(db_path)
    
    if not db_path.exists():
        raise DROMAConnectionError(
            f"Database file does not exist: {db_path}",
            "Check the file path"
        )
    
    # Connect to database
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        raise DROMAConnectionError(
            f"Failed to connect to database: {db_path}",
            str(e)
        )
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        if not all_tables:
            logger.info("No tables found in database")
            return pd.DataFrame(columns=["table_name", "n_features", "n_samples"])
        
        # Check if metadata table exists
        if "matrix_metadata" in all_tables:
            metadata = pd.read_sql_query("SELECT * FROM matrix_metadata", conn)
            return metadata
        
        # Generate metadata on the fly
        matrix_tables = [t for t in all_tables 
                        if t not in ["matrix_metadata", "sqlite_sequence"]]
        
        if not matrix_tables:
            logger.info("No matrix tables found in database")
            return pd.DataFrame(columns=["table_name", "n_features", "n_samples"])
        
        metadata_list = []
        
        # Try to get dimensions for each table
        for table_name in matrix_tables:
            try:
                # Validate table name (defensive check, though it came from database)
                # This ensures we don't accidentally use malicious table names
                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
                    logger.warning(f"Skipping table with invalid name: {table_name}")
                    continue
                
                # Get row count (number of features)
                # Note: table_name is from database, but we validate it for safety
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                n_features = cursor.fetchone()[0]
                
                # Get column count (subtract 1 for feature_id)
                cursor.execute(f"PRAGMA table_info({table_name})")
                col_info = cursor.fetchall()
                n_samples = len([col for col in col_info if col[1] != "feature_id"])
                
                metadata_list.append({
                    "table_name": table_name,
                    "n_features": n_features,
                    "n_samples": n_samples
                })
            except sqlite3.Error as e:
                logger.warning(f"Could not get metadata for table '{table_name}': {e}")
                metadata_list.append({
                    "table_name": table_name,
                    "n_features": None,
                    "n_samples": None
                })
        
        metadata_df = pd.DataFrame(metadata_list)
        return metadata_df
    
    finally:
        conn.close()

