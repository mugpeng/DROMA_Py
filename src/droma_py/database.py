"""
Core database connection and management for DROMA-Py.

This module provides both functional and object-oriented interfaces for
connecting to and managing DROMA SQLite databases.
"""

import sqlite3
import os
import atexit
from pathlib import Path
from typing import Optional, Union, Dict, Any
import logging

from .exceptions import DROMAConnectionError, DROMAError

# Global connection storage
_global_connection: Optional[sqlite3.Connection] = None

logger = logging.getLogger(__name__)


class DROMADatabase:
    """
    Object-oriented interface for DROMA database operations.
    
    This class provides a high-level interface for interacting with DROMA
    SQLite databases, managing connections, and performing database operations.
    
    Examples:
        >>> db = DROMADatabase("path/to/droma.sqlite")
        >>> db.connect()
        >>> projects = db.list_projects()
        >>> db.close()
        
        # Or use as context manager
        >>> with DROMADatabase("path/to/droma.sqlite") as db:
        ...     projects = db.list_projects()
    """
    
    def __init__(self, db_path: Union[str, Path]) -> None:
        """
        Initialize DROMA database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self._is_connected = False
    
    def connect(self) -> sqlite3.Connection:
        """
        Establish connection to the DROMA database.
        
        Returns:
            sqlite3.Connection: Database connection object
            
        Raises:
            DROMAConnectionError: If database file not found or connection fails
        """
        if not self.db_path.exists():
            raise DROMAConnectionError(
                f"Database file not found: {self.db_path}",
                "Create the database first or check the file path"
            )
        
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            self._is_connected = True
            logger.info(f"Connected to DROMA database at {self.db_path}")
            return self.connection
        except sqlite3.Error as e:
            raise DROMAConnectionError(
                f"Failed to connect to database: {self.db_path}",
                str(e)
            )
    
    def close(self) -> None:
        """Close the database connection."""
        if self.connection and self._is_connected:
            try:
                self.connection.close()
                self._is_connected = False
                self.connection = None
                logger.info("Database connection closed")
            except sqlite3.Error as e:
                logger.warning(f"Error closing database connection: {e}")
    
    def __enter__(self) -> "DROMADatabase":
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
    
    def execute(self, query: str, params: Optional[tuple] = None) -> sqlite3.Cursor:
        """
        Execute a SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            sqlite3.Cursor: Query result cursor
            
        Raises:
            DROMAConnectionError: If not connected to database
        """
        if not self._is_connected or not self.connection:
            raise DROMAConnectionError("Not connected to database")
        
        try:
            if params:
                return self.connection.execute(query, params)
            else:
                return self.connection.execute(query)
        except sqlite3.Error as e:
            raise DROMAError(f"Query execution failed: {query}", str(e))
    
    def fetchall(self, query: str, params: Optional[tuple] = None) -> list:
        """
        Execute query and fetch all results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            list: Query results
        """
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def fetchone(self, query: str, params: Optional[tuple] = None) -> Optional[sqlite3.Row]:
        """
        Execute query and fetch one result.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Optional[sqlite3.Row]: Single query result or None
        """
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def list_tables(self) -> list[str]:
        """
        List all tables in the database.
        
        Returns:
            list[str]: List of table names
        """
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        results = self.fetchall(query)
        return [row[0] for row in results]
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            bool: True if table exists, False otherwise
        """
        tables = self.list_tables()
        return table_name in tables


def connect_droma_database(
    db_path: Union[str, Path] = None,
    set_global: bool = True
) -> sqlite3.Connection:
    """
    Establish a connection to the DROMA SQLite database.
    
    This function mirrors the R connectDROMADatabase() function, providing
    a functional interface for database connection.
    
    Args:
        db_path: Path to the SQLite database file. If None, uses default path
        set_global: Whether to set this as the global connection
        
    Returns:
        sqlite3.Connection: Database connection object
        
    Raises:
        DROMAConnectionError: If database file not found or connection fails
        
    Examples:
        >>> con = connect_droma_database("path/to/droma.sqlite")
        >>> # Use connection...
        >>> close_droma_database(con)
    """
    global _global_connection
    
    # Default path if not provided
    if db_path is None:
        db_path = Path("sql_db") / "droma.sqlite"
    else:
        db_path = Path(db_path)
    
    if not db_path.exists():
        raise DROMAConnectionError(
            f"Database file not found: {db_path}",
            "Create the database first with createDROMADatabase() or check the file path"
        )
    
    try:
        connection = sqlite3.connect(str(db_path))
        connection.row_factory = sqlite3.Row
        
        if set_global:
            # Close existing global connection if any
            if _global_connection:
                try:
                    _global_connection.close()
                except sqlite3.Error:
                    pass
            
            _global_connection = connection
            
            # Register cleanup function
            atexit.register(_cleanup_global_connection)
        
        logger.info(f"Connected to DROMA database at {db_path}")
        return connection
        
    except sqlite3.Error as e:
        raise DROMAConnectionError(
            f"Failed to connect to database: {db_path}",
            str(e)
        )


def close_droma_database(connection: Optional[sqlite3.Connection] = None) -> bool:
    """
    Close the connection to the DROMA database.
    
    Args:
        connection: Database connection to close. If None, closes global connection
        
    Returns:
        bool: True if successfully disconnected, False otherwise
        
    Examples:
        >>> con = connect_droma_database()
        >>> close_droma_database(con)
        True
    """
    global _global_connection
    
    if connection is None:
        if _global_connection is None:
            logger.info("No open database connection found")
            return False
        connection = _global_connection
        _global_connection = None
    
    try:
        connection.close()
        logger.info("Database connection closed")
        return True
    except sqlite3.Error as e:
        logger.warning(f"Error closing database connection: {e}")
        return False


def get_global_connection() -> sqlite3.Connection:
    """
    Get the global database connection.
    
    Returns:
        sqlite3.Connection: Global database connection
        
    Raises:
        DROMAConnectionError: If no global connection exists
    """
    global _global_connection
    
    if _global_connection is None:
        raise DROMAConnectionError(
            "No database connection found",
            "Connect first with connect_droma_database()"
        )
    
    return _global_connection


def _cleanup_global_connection() -> None:
    """Clean up global connection on exit."""
    global _global_connection
    if _global_connection:
        try:
            _global_connection.close()
        except sqlite3.Error:
            pass
        _global_connection = None 