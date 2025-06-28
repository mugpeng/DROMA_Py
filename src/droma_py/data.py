"""
Data retrieval functions for DROMA-Py.

This module provides functions for retrieving data from DROMA databases,
including features, samples, and annotations.
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Optional, Union, List, Dict, Any
import logging
import re

from .database import get_global_connection
from .exceptions import (
    DROMADataError, 
    DROMAQueryError,
    DROMATableError,
    DROMAValidationError
)

logger = logging.getLogger(__name__)


def get_feature_from_database(
    select_feas_type: str,
    select_feas: Union[str, List[str]] = "all",
    data_sources: Union[str, List[str]] = "all",
    data_type: Union[str, List[str]] = "all",
    tumor_type: Union[str, List[str]] = "all",
    connection: Optional[sqlite3.Connection] = None
) -> Dict[str, Union[pd.DataFrame, pd.Series, List[str]]]:
    """
    Retrieve specific feature data from the DROMA database based on selection criteria.
    
    This function mirrors the R getFeatureFromDatabase() function with enhanced support
    for multiple features, data types, and tumor types.
    
    Args:
        select_feas_type: The type of feature to select (e.g., "mRNA", "cnv", "drug")
        select_feas: The specific feature(s) to select within the feature type. 
                    Can be a single feature name, list of features, or "all" (default: "all")
        data_sources: Data sources to select from (e.g., "gCSI", ["CCLE", "GDSC"])
        data_type: Filter by data type(s). Can be a single type, list of types, or "all"
                  ("all", "CellLine", "PDO", "PDC", "PDX")
        tumor_type: Filter by tumor type(s). Can be a single type, list of types, or "all"
                   ("all" or specific tumor types like "breast", "lung", etc.)
        connection: Optional database connection. If None, uses global connection
        
    Returns:
        Dict[str, Union[pd.DataFrame, pd.Series, List[str]]]: Selected features from specified data sources
        
    Examples:
        >>> # Get all mRNA data from gCSI
        >>> data = get_feature_from_database("mRNA", data_sources=["gCSI"])
        
        >>> # Get multiple genes from multiple sources
        >>> multi_gene_data = get_feature_from_database(
        ...     "mRNA", 
        ...     select_feas=["BRCA1", "TP53", "EGFR"], 
        ...     data_sources=["gCSI", "CCLE"]
        ... )
        
        >>> # Get drug response data for multiple data types
        >>> drug_data = get_feature_from_database(
        ...     "drug", 
        ...     data_type=["CellLine", "PDO"]
        ... )
        
        >>> # Get mRNA data for specific tumor types
        >>> tumor_data = get_feature_from_database(
        ...     "mRNA", 
        ...     tumor_type=["breast", "lung", "colon"]
        ... )
    """
    if connection is None:
        connection = get_global_connection()
    
    cursor = connection.cursor()
    
    # Get data source tables that match the feature type
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    pattern = f"_{select_feas_type}$"
    feature_tables = [t for t in all_tables if re.search(pattern, t)]
    
    if not feature_tables:
        raise DROMADataError(f"No tables found for feature type: {select_feas_type}")
    
    # Filter by data sources if specified
    if data_sources != "all":
        if isinstance(data_sources, str):
            data_sources = [data_sources]
        pattern_sources = f"^({'|'.join(data_sources)})_"
        feature_tables = [t for t in feature_tables if re.search(pattern_sources, t)]
    
    if not feature_tables:
        raise DROMADataError("No matching tables found for the specified data sources")
    
    # Get sample IDs from sample_anno based on data_type and tumor_type
    filtered_samples = None
    if data_type != "all" or tumor_type != "all":
        sample_query = "SELECT SampleID FROM sample_anno WHERE 1=1"
        params = []
        
        if data_type != "all":
            # Handle both single string and list of strings
            if isinstance(data_type, str):
                data_type_list = [data_type]
            else:
                data_type_list = data_type
            
            # Create IN clause for multiple data types
            placeholders = ", ".join(["?" for _ in data_type_list])
            sample_query += f" AND DataType IN ({placeholders})"
            params.extend(data_type_list)
        
        if tumor_type != "all":
            # Handle both single string and list of strings
            if isinstance(tumor_type, str):
                tumor_type_list = [tumor_type]
            else:
                tumor_type_list = tumor_type
            
            # Create IN clause for multiple tumor types
            placeholders = ", ".join(["?" for _ in tumor_type_list])
            sample_query += f" AND TumorType IN ({placeholders})"
            params.extend(tumor_type_list)
        
        try:
            if params:
                cursor.execute(sample_query, params)
            else:
                cursor.execute(sample_query)
            
            filtered_samples = [row[0] for row in cursor.fetchall()]
            
            if not filtered_samples:
                raise DROMADataError(
                    f"No samples match the specified data_type='{data_type}' and tumor_type='{tumor_type}' criteria"
                )
        except sqlite3.Error as e:
            logger.warning(f"Could not filter samples: {e}")
            filtered_samples = None
    
    # Retrieve data for each table
    result_dict = {}
    
    for table in feature_tables:
        # Extract data source name from table name
        data_source = re.sub(f"_{select_feas_type}$", "", table)
        
        try:
            # Query for the specified feature or entire table
            if select_feas_type in ["mRNA", "cnv", "meth", "proteinrppa", "proteinms", "drug", "drug_raw"]:
                # For continuous data
                if select_feas == "all":
                    # Get entire table
                    query = f"SELECT * FROM {table}"
                    feature_data = pd.read_sql_query(query, connection)
                    
                    if feature_data.empty:
                        continue  # Skip if table is empty
                    
                    # Convert to matrix format (set index to feature_id if exists)
                    if 'feature_id' in feature_data.columns:
                        feature_data = feature_data.set_index('feature_id')
                    
                    feature_result = feature_data
                    
                else:
                    # Handle both single feature and multiple features
                    if isinstance(select_feas, str):
                        select_feas_list = [select_feas]
                    else:
                        select_feas_list = select_feas
                    
                    # Get rows for the specified features using IN clause
                    placeholders = ", ".join(["?" for _ in select_feas_list])
                    query = f"SELECT * FROM {table} WHERE feature_id IN ({placeholders})"
                    feature_data = pd.read_sql_query(query, connection, params=select_feas_list)
                    
                    if feature_data.empty:
                        continue  # Skip if features not found
                    
                    # Convert to appropriate format
                    if 'feature_id' in feature_data.columns:
                        feature_data = feature_data.set_index('feature_id')
                    
                    # Return DataFrame for multiple features, Series for single feature
                    if len(select_feas_list) == 1 and len(feature_data) == 1:
                        # Single feature - return as Series
                        feature_result = feature_data.iloc[0]
                    else:
                        # Multiple features - return as DataFrame
                        feature_result = feature_data
                    
            else:
                # For discrete data like mutations
                if select_feas == "all":
                    # Get entire table
                    query = f"SELECT * FROM {table}"
                    feature_result = pd.read_sql_query(query, connection)
                    
                    if feature_result.empty:
                        continue  # Skip if table is empty
                        
                else:
                    # Handle both single feature and multiple features
                    if isinstance(select_feas, str):
                        select_feas_list = [select_feas]
                    else:
                        select_feas_list = select_feas
                    
                    # Get data for the specified features using IN clause
                    placeholders = ", ".join(["?" for _ in select_feas_list])
                    query = f"SELECT gene, cells FROM {table} WHERE gene IN ({placeholders})"
                    cursor.execute(query, select_feas_list)
                    results = cursor.fetchall()
                    
                    if not results:
                        continue  # Skip if features not found
                    
                    if len(select_feas_list) == 1:
                        # Single feature - return list of sample IDs
                        feature_result = [row[1] for row in results]
                    else:
                        # Multiple features - return dictionary with gene as key
                        feature_result = {}
                        for gene, cells in results:
                            if gene not in feature_result:
                                feature_result[gene] = []
                            feature_result[gene].append(cells)
            
            # Filter by samples if needed
            if filtered_samples is not None:
                if select_feas_type in ["mRNA", "cnv", "meth", "proteinrppa", "proteinms", "drug", "drug_raw"]:
                    if isinstance(feature_result, pd.DataFrame):
                        # For full tables, filter columns
                        common_samples = list(set(feature_result.columns) & set(filtered_samples))
                        if not common_samples:
                            continue  # Skip if no samples match the filter
                        feature_result = feature_result[common_samples]
                    elif isinstance(feature_result, pd.Series):
                        # For single features, filter index
                        common_samples = list(set(feature_result.index) & set(filtered_samples))
                        if not common_samples:
                            continue  # Skip if no samples match the filter
                        feature_result = feature_result[common_samples]
                else:
                    # For discrete data, handle different return formats
                    if isinstance(feature_result, list):
                        # Single feature - filter the list
                        feature_result = list(set(feature_result) & set(filtered_samples))
                        if not feature_result:
                            continue  # Skip if no samples match the filter
                    elif isinstance(feature_result, dict):
                        # Multiple features - filter each gene's sample list
                        filtered_dict = {}
                        for gene, samples in feature_result.items():
                            filtered_gene_samples = list(set(samples) & set(filtered_samples))
                            if filtered_gene_samples:
                                filtered_dict[gene] = filtered_gene_samples
                        feature_result = filtered_dict
                        if not feature_result:
                            continue  # Skip if no samples match the filter
            
            # Add to result dictionary
            result_dict[data_source] = feature_result
            
        except sqlite3.Error as e:
            logger.warning(f"Error querying table {table}: {e}")
            continue
    
    if not result_dict:
        raise DROMADataError(
            f"No data found for feature '{select_feas}' with the specified criteria"
        )
    
    return result_dict


def list_droma_features(
    project_name: str,
    data_sources: str,
    data_type: str = "all",
    tumor_type: str = "all",
    connection: Optional[sqlite3.Connection] = None,
    limit: Optional[int] = None,
    pattern: Optional[str] = None
) -> List[str]:
    """
    List all available features for a specific project and data type.
    
    Args:
        project_name: Name of the project (e.g., "gCSI", "CCLE")
        data_sources: Type of data to query (e.g., "mRNA", "cnv", "drug", "mutation_gene")
        data_type: Filter by data type ("all", "CellLine", "PDO", "PDC", "PDX")
        tumor_type: Filter by tumor type ("all" or specific tumor type)
        connection: Optional database connection. If None, uses global connection
        limit: Maximum number of features to return (default: None for all features)
        pattern: Optional regex pattern to filter feature names
        
    Returns:
        List[str]: List of available feature names
        
    Examples:
        >>> # List all genes in gCSI mRNA data
        >>> genes = list_droma_features("gCSI", "mRNA")
        
        >>> # List all drugs in gCSI drug response data
        >>> drugs = list_droma_features("gCSI", "drug")
        
        >>> # List genes matching a pattern
        >>> brca_genes = list_droma_features("gCSI", "mRNA", pattern="^BRCA")
        
        >>> # List first 100 features
        >>> top_genes = list_droma_features("gCSI", "mRNA", limit=100)
    """
    if connection is None:
        connection = get_global_connection()
    
    cursor = connection.cursor()
    
    # Construct table name
    table_name = f"{project_name}_{data_sources}"
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    if table_name not in all_tables:
        available_tables = [t for t in all_tables if t.startswith(f"{project_name}_")]
        raise DROMATableError(
            f"Table '{table_name}' not found",
            f"Available tables: {', '.join(available_tables)}"
        )
    
    # Get filtered sample IDs if data_type or tumor_type filters are specified
    filtered_samples = None
    if data_type != "all" or tumor_type != "all":
        if "sample_anno" not in all_tables:
            logger.warning("Sample annotation table 'sample_anno' not found. Ignoring data_type and tumor_type filters.")
        else:
            sample_query = "SELECT DISTINCT SampleID FROM sample_anno WHERE ProjectID = ?"
            params = [project_name]
            
            if data_type != "all":
                sample_query += " AND DataType = ?"
                params.append(data_type)
            
            if tumor_type != "all":
                sample_query += " AND TumorType = ?"
                params.append(tumor_type)
            
            try:
                cursor.execute(sample_query, params)
                filtered_samples = [row[0] for row in cursor.fetchall()]
                
                if not filtered_samples:
                    filter_parts = []
                    if data_type != "all":
                        filter_parts.append(f"data_type='{data_type}'")
                    if tumor_type != "all":
                        filter_parts.append(f"tumor_type='{tumor_type}'")
                    filter_desc = " with " + " and ".join(filter_parts)
                    
                    logger.info(f"No samples found for project '{project_name}'{filter_desc}")
                    return []
            except sqlite3.Error as e:
                logger.warning(f"Error filtering samples: {e}")
                filtered_samples = None
    
    # Determine the column name based on data type
    if data_sources in ["mRNA", "cnv", "meth", "proteinrppa", "proteinms", "drug", "drug_raw"]:
        feature_column = "feature_id"
    elif data_sources in ["mutation_gene", "mutation_site", "fusion"]:
        feature_column = "genes"
    else:
        # Try to detect the column automatically
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        if "feature_id" in column_names:
            feature_column = "feature_id"
        elif "genes" in column_names:
            feature_column = "genes"
        else:
            raise DROMADataError(
                f"Cannot determine feature column for data type '{data_sources}'",
                f"Available columns: {', '.join(column_names)}"
            )
    
    # For continuous data types, check which features have data for the filtered samples
    if (filtered_samples is not None and 
        data_sources in ["mRNA", "cnv", "meth", "proteinrppa", "proteinms", "drug", "drug_raw"]):
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        available_columns = [col[1] for col in columns_info if col[1] != "feature_id"]
        
        # Find intersection of filtered samples and available columns
        common_samples = list(set(filtered_samples) & set(available_columns))
        
        if not common_samples:
            logger.info(f"No data available for the specified sample filters in {table_name}")
            return []
    
    # Construct query to get distinct features
    query = f"SELECT DISTINCT {feature_column} FROM {table_name} WHERE {feature_column} IS NOT NULL"
    params = []
    
    # Add pattern filter if specified
    if pattern:
        # Convert regex pattern to SQL LIKE pattern for basic matching
        like_pattern = pattern
        
        # Handle common regex patterns
        if pattern.startswith("^"):
            like_pattern = pattern[1:] + "%"  # Remove ^ and add % at end
        elif pattern.endswith("$"):
            like_pattern = "%" + pattern[:-1]  # Remove $ and add % at start
        elif pattern.startswith("^") and pattern.endswith("$"):
            like_pattern = pattern[1:-1]  # Remove both ^ and $ (exact match)
        else:
            like_pattern = f"%{pattern}%"  # Default: contains matching
        
        # Replace common regex characters with SQL LIKE equivalents
        like_pattern = like_pattern.replace("*", "%").replace(".", "_")
        
        query += f" AND {feature_column} LIKE ?"
        params.append(like_pattern)
    
    # Add ordering
    query += f" ORDER BY {feature_column}"
    
    # Add limit if specified
    if limit is not None and isinstance(limit, int) and limit > 0:
        query += f" LIMIT {limit}"
    
    # Execute query
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        features = [row[0] for row in results]
        
        if not features:
            filter_parts = []
            if pattern:
                filter_parts.append(f"pattern='{pattern}'")
            if data_type != "all":
                filter_parts.append(f"data_type='{data_type}'")
            if tumor_type != "all":
                filter_parts.append(f"tumor_type='{tumor_type}'")
            
            filter_desc = ""
            if filter_parts:
                filter_desc = " with " + " and ".join(filter_parts)
            
            logger.info(f"No features found in {table_name}{filter_desc}")
            return []
        
        # Print summary information
        total_query = f"SELECT COUNT(DISTINCT {feature_column}) as total FROM {table_name} WHERE {feature_column} IS NOT NULL"
        cursor.execute(total_query)
        total_features = cursor.fetchone()[0]
        
        filter_desc = ""
        filters = []
        if pattern:
            filters.append(f"pattern='{pattern}'")
        if data_type != "all":
            filters.append(f"data_type='{data_type}'")
        if tumor_type != "all":
            filters.append(f"tumor_type='{tumor_type}'")
        
        if filters:
            filter_desc = f" (filtered by {' and '.join(filters)})"
        
        if limit:
            logger.info(f"Showing first {len(features)} features out of {total_features} total features in {table_name}{filter_desc}")
        elif pattern:
            logger.info(f"Found {len(features)} features matching pattern '{pattern}' out of {total_features} total features in {table_name}{filter_desc}")
        else:
            logger.info(f"Found {len(features)} features in {table_name}{filter_desc}")
        
        return features
        
    except sqlite3.Error as e:
        raise DROMAQueryError(f"Error querying features from {table_name}", str(e))


def list_droma_samples(
    project_name: str,
    data_sources: str = "all",
    data_type: str = "all",
    tumor_type: str = "all",
    connection: Optional[sqlite3.Connection] = None,
    limit: Optional[int] = None,
    pattern: Optional[str] = None
) -> List[str]:
    """
    List all available samples for a specific project, optionally filtered by data type or tumor type.
    
    Args:
        project_name: Name of the project (e.g., "gCSI", "CCLE")
        data_sources: Filter by data sources ("all" or specific data type like "mRNA", "cnv", "drug")
        data_type: Filter by data type ("all", "CellLine", "PDO", "PDC", "PDX")
        tumor_type: Filter by tumor type ("all" or specific tumor type)
        connection: Optional database connection. If None, uses global connection
        limit: Maximum number of samples to return (default: None for all samples)
        pattern: Optional regex pattern to filter sample names
        
    Returns:
        List[str]: List of available sample IDs
        
    Examples:
        >>> # List all samples for gCSI project
        >>> samples = list_droma_samples("gCSI")
        
        >>> # List only cell line samples
        >>> cell_lines = list_droma_samples("gCSI", data_type="CellLine")
        
        >>> # List samples with mRNA data
        >>> mrna_samples = list_droma_samples("gCSI", data_sources="mRNA")
        
        >>> # List samples matching a pattern
        >>> mcf_samples = list_droma_samples("gCSI", pattern="^MCF")
    """
    if connection is None:
        connection = get_global_connection()
    
    cursor = connection.cursor()
    
    # Check if sample_anno table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    if "sample_anno" not in all_tables:
        raise DROMATableError("Sample annotation table 'sample_anno' not found in database")
    
    # Get samples with data_sources filter if specified
    filtered_samples_by_data = None
    if data_sources != "all":
        data_table_name = f"{project_name}_{data_sources}"
        
        if data_table_name not in all_tables:
            available_tables = [t for t in all_tables if t.startswith(f"{project_name}_")]
            raise DROMATableError(
                f"Data source table '{data_table_name}' not found",
                f"Available tables: {', '.join(available_tables)}"
            )
        
        # Get samples that have data in this data source
        if data_sources in ["mRNA", "cnv", "meth", "proteinrppa", "proteinms", "drug", "drug_raw"]:
            # For continuous data, get column names (excluding feature_id)
            cursor.execute(f"PRAGMA table_info({data_table_name})")
            columns_info = cursor.fetchall()
            filtered_samples_by_data = [col[1] for col in columns_info if col[1] != "feature_id"]
        elif data_sources in ["mutation_gene", "mutation_site", "fusion"]:
            # For discrete data, get unique values from cells column
            try:
                cursor.execute(f"SELECT DISTINCT cells FROM {data_table_name} WHERE cells IS NOT NULL")
                results = cursor.fetchall()
                filtered_samples_by_data = [row[0] for row in results]
            except sqlite3.Error as e:
                logger.warning(f"Error querying discrete data: {e}")
                filtered_samples_by_data = []
        else:
            # Try to detect automatically
            cursor.execute(f"PRAGMA table_info({data_table_name})")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            
            if "cells" in column_names:
                # Discrete data
                cursor.execute(f"SELECT DISTINCT cells FROM {data_table_name} WHERE cells IS NOT NULL")
                results = cursor.fetchall()
                filtered_samples_by_data = [row[0] for row in results]
            else:
                # Continuous data
                filtered_samples_by_data = [col[1] for col in columns_info if col[1] != "feature_id"]
        
        if not filtered_samples_by_data:
            logger.info(f"No samples found with data in '{data_sources}' for project '{project_name}'")
            return []
    
    # Construct query
    query = "SELECT DISTINCT SampleID FROM sample_anno WHERE ProjectID = ?"
    params = [project_name]
    
    # Add data type filter
    if data_type != "all":
        query += " AND DataType = ?"
        params.append(data_type)
    
    # Add tumor type filter
    if tumor_type != "all":
        query += " AND TumorType = ?"
        params.append(tumor_type)
    
    # Add data sources filter by restricting to samples with data
    if filtered_samples_by_data is not None:
        if filtered_samples_by_data:
            placeholders = ', '.join('?' * len(filtered_samples_by_data))
            query += f" AND SampleID IN ({placeholders})"
            params.extend(filtered_samples_by_data)
        else:
            # No samples with data in this data source
            return []
    
    # Add pattern filter if specified
    if pattern:
        # Convert regex pattern to SQL LIKE pattern
        like_pattern = pattern
        
        if pattern.startswith("^"):
            like_pattern = pattern[1:] + "%"
        elif pattern.endswith("$"):
            like_pattern = "%" + pattern[:-1]
        elif pattern.startswith("^") and pattern.endswith("$"):
            like_pattern = pattern[1:-1]
        else:
            like_pattern = f"%{pattern}%"
        
        like_pattern = like_pattern.replace("*", "%").replace(".", "_")
        
        query += " AND SampleID LIKE ?"
        params.append(like_pattern)
    
    # Add ordering
    query += " ORDER BY SampleID"
    
    # Add limit if specified
    if limit is not None and isinstance(limit, int) and limit > 0:
        query += f" LIMIT {limit}"
    
    # Execute query
    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
        samples = [row[0] for row in results]
        
        if not samples:
            filter_parts = []
            if data_type != "all":
                filter_parts.append(f"data_type='{data_type}'")
            if tumor_type != "all":
                filter_parts.append(f"tumor_type='{tumor_type}'")
            if data_sources != "all":
                filter_parts.append(f"data_sources='{data_sources}'")
            if pattern:
                filter_parts.append(f"pattern='{pattern}'")
            
            filter_desc = ""
            if filter_parts:
                filter_desc = " with " + " and ".join(filter_parts)
            
            logger.info(f"No samples found for project '{project_name}'{filter_desc}")
            return []
        
        # Print summary information
        total_query = "SELECT COUNT(DISTINCT SampleID) as total FROM sample_anno WHERE ProjectID = ?"
        cursor.execute(total_query, [project_name])
        total_samples = cursor.fetchone()[0]
        
        filter_desc = ""
        filters = []
        if data_type != "all":
            filters.append(f"data_type='{data_type}'")
        if tumor_type != "all":
            filters.append(f"tumor_type='{tumor_type}'")
        if data_sources != "all":
            filters.append(f"data_sources='{data_sources}'")
        if pattern:
            filters.append(f"pattern='{pattern}'")
        
        if filters:
            filter_desc = f" (filtered by {' and '.join(filters)})"
        
        if limit:
            logger.info(f"Showing first {len(samples)} samples out of {total_samples} total samples for project '{project_name}'{filter_desc}")
        else:
            if pattern or data_sources != "all":
                logger.info(f"Found {len(samples)} samples out of {total_samples} total samples for project '{project_name}'{filter_desc}")
            else:
                logger.info(f"Found {len(samples)} samples for project '{project_name}'{filter_desc}")
        
        return samples
        
    except sqlite3.Error as e:
        raise DROMAQueryError(f"Error querying samples for project '{project_name}'", str(e))


def get_droma_annotation(
    anno_type: str,
    project_name: Optional[str] = None,
    ids: Optional[List[str]] = None,
    data_type: str = "all",
    tumor_type: str = "all",
    connection: Optional[sqlite3.Connection] = None,
    limit: Optional[int] = None
) -> pd.DataFrame:
    """
    Retrieve annotation data from either sample_anno or drug_anno tables.
    
    Args:
        anno_type: Type of annotation to retrieve ("sample" or "drug")
        project_name: Optional project name to filter results (default: None for all projects)
        ids: Optional specific IDs to retrieve (SampleID for samples, DrugName for drugs)
        data_type: For sample annotations only: filter by data type ("all", "CellLine", "PDO", "PDC", "PDX")
        tumor_type: For sample annotations only: filter by tumor type ("all" or specific type)
        connection: Optional database connection. If None, uses global connection
        limit: Maximum number of records to return (default: None for all records)
        
    Returns:
        pd.DataFrame: Annotation data
        
    Examples:
        >>> # Get all sample annotations
        >>> sample_anno = get_droma_annotation("sample")
        
        >>> # Get sample annotations for gCSI project only
        >>> gCSI_samples = get_droma_annotation("sample", project_name="gCSI")
        
        >>> # Get annotations for specific samples
        >>> specific_samples = get_droma_annotation("sample", ids=["22RV1", "2313287"])
        
        >>> # Get all drug annotations
        >>> drug_anno = get_droma_annotation("drug")
    """
    if connection is None:
        connection = get_global_connection()
    
    # Validate anno_type
    if anno_type not in ["sample", "drug"]:
        raise DROMAValidationError("anno_type must be either 'sample' or 'drug'")
    
    # Determine table name and ID column
    if anno_type == "sample":
        table_name = "sample_anno"
        id_column = "SampleID"
        project_column = "ProjectID"
    else:
        table_name = "drug_anno"
        id_column = "DrugName"
        project_column = "ProjectID"
    
    cursor = connection.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    if table_name not in all_tables:
        raise DROMATableError(f"Annotation table '{table_name}' not found in database")
    
    # Build query
    query = f"SELECT * FROM {table_name} WHERE 1=1"
    params = []
    
    # Add project filter
    if project_name is not None:
        query += f" AND {project_column} = ?"
        params.append(project_name)
    
    # Add ID filter
    if ids is not None and len(ids) > 0:
        placeholders = ', '.join('?' * len(ids))
        query += f" AND {id_column} IN ({placeholders})"
        params.extend(ids)
    
    # Add sample-specific filters
    if anno_type == "sample":
        # Add data type filter
        if data_type != "all":
            query += " AND DataType = ?"
            params.append(data_type)
        
        # Add tumor type filter
        if tumor_type != "all":
            query += " AND TumorType = ?"
            params.append(tumor_type)
    
    # Add ordering
    query += f" ORDER BY {id_column}"
    
    # Add limit if specified
    if limit is not None and isinstance(limit, int) and limit > 0:
        query += f" LIMIT {limit}"
    
    # Execute query
    try:
        if params:
            result = pd.read_sql_query(query, connection, params=params)
        else:
            result = pd.read_sql_query(query, connection)
        
        if result.empty:
            filter_desc = ""
            filters = []
            
            if project_name is not None:
                filters.append(f"project='{project_name}'")
            if ids is not None:
                filters.append(f"specific IDs ({len(ids)} requested)")
            if anno_type == "sample":
                if data_type != "all":
                    filters.append(f"data_type='{data_type}'")
                if tumor_type != "all":
                    filters.append(f"tumor_type='{tumor_type}'")
            
            if filters:
                filter_desc = " with filters: " + ", ".join(filters)
            
            logger.info(f"No {anno_type} annotations found{filter_desc}")
            return pd.DataFrame()
        
        # Print summary information
        total_query = f"SELECT COUNT(*) as total FROM {table_name}"
        cursor.execute(total_query)
        total_records = cursor.fetchone()[0]
        
        filter_desc = ""
        if (project_name is not None or ids is not None or 
            (anno_type == "sample" and (data_type != "all" or tumor_type != "all"))):
            filters = []
            
            if project_name is not None:
                filters.append(f"project='{project_name}'")
            if ids is not None:
                filters.append("specific IDs")
            if anno_type == "sample":
                if data_type != "all":
                    filters.append(f"data_type='{data_type}'")
                if tumor_type != "all":
                    filters.append(f"tumor_type='{tumor_type}'")
            
            filter_desc = f" (filtered by {' and '.join(filters)})"
        
        if limit:
            logger.info(f"Retrieved first {len(result)} {anno_type} annotations out of {total_records} total records{filter_desc}")
        else:
            logger.info(f"Retrieved {len(result)} {anno_type} annotations{filter_desc}")
        
        return result
        
    except sqlite3.Error as e:
        raise DROMAQueryError(f"Error querying {anno_type} annotations", str(e)) 