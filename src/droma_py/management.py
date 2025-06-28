"""
Database management functions for DROMA-Py.

This module provides functions for managing DROMA database content,
including updating tables, projects, and annotations.
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Optional, Union, List, Dict, Any
from datetime import datetime
import logging

from .database import get_global_connection
from .exceptions import (
    DROMAConnectionError, 
    DROMADataError, 
    DROMAValidationError,
    DROMATableError
)

logger = logging.getLogger(__name__)


def update_droma_database(
    obj: Union[pd.DataFrame, np.ndarray],
    table_name: str,
    overwrite: bool = False,
    connection: Optional[sqlite3.Connection] = None
) -> bool:
    """
    Add or update a table in the DROMA database with a new object.
    
    This function mirrors the R updateDROMADatabase() function.
    
    Args:
        obj: The object to add to the database (DataFrame or numpy array)
        table_name: The name to use for the table in the database
        overwrite: Whether to overwrite if table already exists
        connection: Optional database connection. If None, uses global connection
        
    Returns:
        bool: True if successful
        
    Raises:
        DROMAConnectionError: If no database connection
        DROMADataError: If object format is invalid
        DROMATableError: If table already exists and overwrite is False
        
    Examples:
        >>> import pandas as pd
        >>> expr_data = pd.DataFrame(np.random.randn(10, 10))
        >>> expr_data.index = [f"gene{i}" for i in range(10)]
        >>> expr_data.columns = [f"sample{i}" for i in range(10)]
        >>> update_droma_database(expr_data, "myproject_mRNA", overwrite=True)
        True
    """
    if connection is None:
        connection = get_global_connection()
    
    # Check if table already exists
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    table_exists = cursor.fetchone() is not None
    
    if table_exists and not overwrite:
        raise DROMATableError(
            f"Table '{table_name}' already exists",
            "Set overwrite=True to replace it"
        )
    elif table_exists and overwrite:
        logger.info(f"Overwriting existing table '{table_name}'")
    
    # Process the object based on its type
    if isinstance(obj, np.ndarray):
        # Convert numpy array to DataFrame
        df = pd.DataFrame(obj)
        if hasattr(obj, 'index'):
            df.index = obj.index
        if hasattr(obj, 'columns'):
            df.columns = obj.columns
    elif isinstance(obj, pd.DataFrame):
        df = obj.copy()
    else:
        raise DROMADataError(
            "Object must be a pandas DataFrame or numpy array",
            f"Got {type(obj)}"
        )
    
    # Add feature_id column if index has meaningful names
    if df.index.name or not all(df.index == range(len(df))):
        df = df.reset_index()
        df.rename(columns={df.columns[0]: 'feature_id'}, inplace=True)
    
    try:
        # Write to database
        df.to_sql(table_name, connection, if_exists='replace', index=False)
        
        # Create index on feature_id for faster lookups if column exists
        if 'feature_id' in df.columns:
            index_name = f"idx_{table_name}_feature_id"
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} (feature_id)")
            except sqlite3.Error as e:
                logger.warning(f"Could not create index: {e}")
        
        connection.commit()
        
        logger.info(
            f"Added {'DataFrame' if isinstance(obj, pd.DataFrame) else 'array'} "
            f"to database as '{table_name}' with {len(df)} rows and {len(df.columns)} columns"
        )
        
        return True
        
    except sqlite3.Error as e:
        raise DROMADataError(f"Failed to write table '{table_name}' to database", str(e))


def list_droma_database_tables(
    pattern: Optional[str] = None,
    connection: Optional[sqlite3.Connection] = None
) -> pd.DataFrame:
    """
    List available tables in DROMA database.
    
    Provides information about omics and drug tables in the DROMA database.
    Excludes annotation tables, projects table, and backup tables.
    
    Args:
        pattern: Optional regex pattern to filter table names
        connection: Optional database connection. If None, uses global connection
        
    Returns:
        pd.DataFrame: Table information with metadata
        
    Examples:
        >>> tables = list_droma_database_tables()
        >>> print(tables[['table_name', 'data_type', 'feature_type']])
    """
    if connection is None:
        connection = get_global_connection()
    
    # Get table list
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    # Filter to only omics and drug tables, excluding system tables and backups
    excluded_tables = {'sample_anno', 'drug_anno', 'projects', 'droma_metadata', 'search_vectors'}
    tables = [t for t in all_tables if t not in excluded_tables]
    
    # Remove tables containing "raw", "dose", or "viability"
    tables = [t for t in tables if not any(x in t for x in ['raw', 'dose', 'viability'])]
    
    # Only keep tables that follow the pattern "project_datatype"
    tables = [t for t in tables if '_' in t and len(t.split('_')) >= 2]
    
    # Apply user pattern filter if provided
    if pattern:
        import re
        tables = [t for t in tables if re.search(pattern, t)]
    
    if not tables:
        logger.info("No omics or drug tables found")
        return pd.DataFrame()
    
    # Get metadata for each table
    result_data = []
    
    for table in tables:
        try:
            # Get basic table info
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            feature_count = cursor.fetchone()[0]
            
            cursor.execute(f"PRAGMA table_info({table})")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            feature_id_cols = sum(1 for name in column_names if name == 'feature_id')
            sample_count = max(0, len(column_names) - feature_id_cols)
            
            # Extract data type and feature type
            parts = table.split('_')
            data_type = parts[0] if parts else None
            
            # Handle feature type with special cases for mutation tables
            if len(parts) >= 3 and parts[1] == 'mutation':
                feature_type = '_'.join(parts[1:3])  # "mutation_site" or "mutation_gene"
            elif len(parts) >= 2:
                feature_type = parts[1]  # Regular case
            else:
                feature_type = None
            
            result_data.append({
                'table_name': table,
                'data_type': data_type,
                'feature_type': feature_type,
                'feature_count': feature_count,
                'sample_count': sample_count,
                'created_date': None,
                'updated_date': None
            })
            
        except sqlite3.Error as e:
            logger.warning(f"Error getting info for table {table}: {e}")
            continue
    
    if not result_data:
        return pd.DataFrame()
    
    result_df = pd.DataFrame(result_data)
    
    # Add created_date and updated_date from projects table if available
    if 'projects' in all_tables:
        try:
            projects_df = pd.read_sql_query("SELECT * FROM projects", connection)
            for idx, row in result_df.iterrows():
                project_match = projects_df[projects_df['project_name'] == row['data_type']]
                if not project_match.empty:
                    result_df.at[idx, 'created_date'] = project_match.iloc[0].get('created_date')
                    result_df.at[idx, 'updated_date'] = project_match.iloc[0].get('updated_date')
        except sqlite3.Error as e:
            logger.warning(f"Error reading projects table: {e}")
    
    return result_df


def list_droma_projects(
    connection: Optional[sqlite3.Connection] = None,
    show_names_only: bool = False,
    project_data_types: Optional[str] = None
) -> Union[pd.DataFrame, List[str]]:
    """
    List all projects available in the DROMA database.
    
    Args:
        connection: Optional database connection. If None, uses global connection
        show_names_only: If True, returns only a list of project names
        project_data_types: Project name to get specific data types for
        
    Returns:
        Union[pd.DataFrame, List[str]]: Project information or list of names/data types
        
    Examples:
        >>> projects = list_droma_projects()
        >>> project_names = list_droma_projects(show_names_only=True)
        >>> data_types = list_droma_projects(project_data_types="gCSI")
    """
    if connection is None:
        connection = get_global_connection()
    
    cursor = connection.cursor()
    
    # Check if projects table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
    projects_table_exists = cursor.fetchone() is not None
    
    if projects_table_exists:
        projects_df = pd.read_sql_query("SELECT * FROM projects", connection)
        
        if show_names_only:
            return projects_df['project_name'].tolist()
        
        if project_data_types:
            project_row = projects_df[projects_df['project_name'] == project_data_types]
            if not project_row.empty:
                data_types_str = project_row.iloc[0]['data_types']
                return data_types_str.split(',') if data_types_str else []
            else:
                logger.warning(f"Project '{project_data_types}' not found")
                return []
        
        return projects_df
    
    # If no projects table, infer from table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    project_names = set()
    for table in all_tables:
        parts = table.split('_')
        if (len(parts) >= 2 and 
            table not in ['sample_anno', 'drug_anno'] and 
            not table.endswith('_raw')):
            project_names.add(parts[0])
    
    project_names = list(project_names)
    
    if not project_names:
        logger.info("No projects found in database")
        if show_names_only:
            return []
        return pd.DataFrame()
    
    if show_names_only:
        return project_names
    
    if project_data_types:
        if project_data_types in project_names:
            # Get all tables for this project
            project_tables = [t for t in all_tables if t.startswith(f"{project_data_types}_")]
            # Remove backup tables
            project_tables = [t for t in project_tables if not t.endswith('_raw')]
            # Extract data types
            data_types = list(set(t.replace(f"{project_data_types}_", "") for t in project_tables))
            return data_types
        else:
            logger.warning(f"Project '{project_data_types}' not found")
            return []
    
    # Create basic project DataFrame
    result_df = pd.DataFrame({'project_name': project_names})
    return result_df


def update_droma_projects(
    project_name: Optional[str] = None,
    dataset_type: Optional[str] = None,
    connection: Optional[sqlite3.Connection] = None,
    create_table: bool = True
) -> bool:
    """
    Update or add project metadata to the projects table.
    
    This function automatically detects project information from existing tables
    and updates the projects table accordingly.
    
    Args:
        project_name: Name of the project to update. If None, updates all projects
        dataset_type: Dataset type to assign (e.g., "CellLine", "PDX", "PDO")
        connection: Optional database connection. If None, uses global connection
        create_table: Whether to create the projects table if it doesn't exist
        
    Returns:
        bool: True if successful
        
    Examples:
        >>> # Update specific project
        >>> update_droma_projects("gCSI", dataset_type="CellLine")
        
        >>> # Update all projects
        >>> update_droma_projects()
    """
    if connection is None:
        connection = get_global_connection()
    
    cursor = connection.cursor()
    
    # Get all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    # Extract project names from table names
    if project_name is None:
        project_names = set()
        for table in all_tables:
            parts = table.split('_')
            if (len(parts) >= 2 and 
                table not in ['sample_anno', 'drug_anno', 'search_vectors', 'projects', 'droma_metadata'] and
                not table.endswith('_raw')):
                project_names.add(parts[0])
        project_names = list(project_names)
    else:
        project_names = [project_name]
    
    if not project_names:
        logger.info("No projects found in database")
        return False
    
    # Check if projects table exists, create if needed
    projects_table_exists = 'projects' in all_tables
    if not projects_table_exists:
        if create_table:
            create_projects_query = """
                CREATE TABLE projects (
                    project_name TEXT PRIMARY KEY,
                    dataset_type TEXT,
                    data_types TEXT,
                    sample_count INTEGER,
                    drug_count INTEGER,
                    created_date TEXT,
                    updated_date TEXT
                )
            """
            cursor.execute(create_projects_query)
            logger.info("Created projects table")
        else:
            raise DROMATableError(
                "Projects table does not exist",
                "Set create_table=True to create it"
            )
    
    # Get existing projects data
    existing_projects = pd.read_sql_query("SELECT * FROM projects", connection) if projects_table_exists else pd.DataFrame()
    
    updated_count = 0
    added_count = 0
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for proj in project_names:
        # Get tables for this project
        project_tables = [t for t in all_tables if t.startswith(f"{proj}_")]
        project_tables = [t for t in project_tables if not t.endswith('_raw')]
        
        if not project_tables:
            logger.warning(f"No tables found for project '{proj}'")
            continue
        
        # Extract data types, excluding tables with "raw", "dose", or "viability"
        filtered_tables = [t for t in project_tables if not any(x in t for x in ['raw', 'dose', 'viability'])]
        data_types = set()
        for table in filtered_tables:
            data_type = table.replace(f"{proj}_", "")
            data_types.add(data_type)
        
        # Special handling for drug_dose and drug_viability tables
        if any(t in project_tables for t in [f"{proj}_drug_dose", f"{proj}_drug_viability"]):
            data_types.add("drug_dose")
        
        data_types = sorted(data_types)
        
        # Determine dataset type
        current_dataset_type = dataset_type
        sample_count = 0
        
        # Get sample count from sample_anno if available
        if 'sample_anno' in all_tables:
            try:
                sample_query = "SELECT COUNT(DISTINCT SampleID) FROM sample_anno WHERE ProjectID = ?"
                cursor.execute(sample_query, (proj,))
                result = cursor.fetchone()
                sample_count = result[0] if result else 0
                
                # Try to guess dataset_type if not provided
                if current_dataset_type is None:
                    type_query = "SELECT DISTINCT DataType FROM sample_anno WHERE ProjectID = ? LIMIT 1"
                    cursor.execute(type_query, (proj,))
                    type_result = cursor.fetchone()
                    if type_result:
                        current_dataset_type = type_result[0]
            except sqlite3.Error:
                pass
        
        # Count drugs in drug table if available
        drug_count = 0
        drug_table = f"{proj}_drug"
        if drug_table in all_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {drug_table}")
                result = cursor.fetchone()
                drug_count = result[0] if result else 0
            except sqlite3.Error:
                pass
        
        data_types_str = ','.join(data_types)
        
        # Check if project already exists
        project_exists = not existing_projects.empty and proj in existing_projects['project_name'].values
        
        if project_exists:
            # Update existing project
            update_query = """
                UPDATE projects SET
                    dataset_type = ?,
                    data_types = ?,
                    sample_count = ?,
                    drug_count = ?,
                    updated_date = ?
                WHERE project_name = ?
            """
            cursor.execute(update_query, (
                current_dataset_type, data_types_str, sample_count, 
                drug_count, current_time, proj
            ))
            
            logger.info(
                f"Updated project '{proj}' with {len(data_types)} data types "
                f"({data_types_str}), {sample_count} samples, {drug_count} drugs"
            )
            updated_count += 1
        else:
            # Add new project
            insert_query = """
                INSERT INTO projects (project_name, dataset_type, data_types, 
                                    sample_count, drug_count, created_date, updated_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                proj, current_dataset_type, data_types_str, sample_count,
                drug_count, current_time, current_time
            ))
            
            logger.info(
                f"Added new project '{proj}' with {len(data_types)} data types "
                f"({data_types_str}), {sample_count} samples, {drug_count} drugs"
            )
            added_count += 1
    
    connection.commit()
    
    if added_count > 0 or updated_count > 0:
        logger.info(f"Project metadata update complete: {added_count} projects added, {updated_count} projects updated")
    else:
        logger.info("No projects were added or updated")
    
    return True


def update_droma_annotation(
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
) -> bool:
    """
    Add harmonized sample or drug names to the corresponding annotation tables.
    
    Args:
        anno_type: Type of annotation to update ("sample" or "drug")
        name_mapping: DataFrame with name mappings (original_name, new_name, match_confidence)
        project_name: Project name to assign to new entries
        data_type: Data type(s) for samples (can be single value or list)
        tumor_type: Tumor type(s) for samples (can be single value or list)
        patient_id: Patient ID(s) for samples (can be single value or list)
        gender: Gender(s) for samples (can be single value or list)  
        age: Age(s) for samples (can be single value or list)
        full_ethnicity: Full ethnicity/ethnicities for samples (can be single value or list)
        simple_ethnicity: Simple ethnicity/ethnicities for samples (can be single value or list)
        connection: Optional database connection. If None, uses global connection
        
    Returns:
        bool: True if successful
        
    Examples:
        >>> # Update sample annotations
        >>> mapping = check_droma_sample_names(sample_names)
        >>> update_droma_annotation(
        ...     "sample", mapping, "MyProject",
        ...     data_type="CellLine", tumor_type="breast cancer"
        ... )
    """
    if connection is None:
        connection = get_global_connection()
    
    # Validate anno_type
    if anno_type not in ['sample', 'drug']:
        raise DROMAValidationError("anno_type must be either 'sample' or 'drug'")
    
    # Validate name_mapping structure
    required_cols = ['original_name', 'new_name', 'match_confidence']
    if not all(col in name_mapping.columns for col in required_cols):
        raise DROMAValidationError(f"name_mapping must contain columns: {required_cols}")
    
    # Validate parameter lengths for sample annotations
    if anno_type == 'sample':
        n_rows = len(name_mapping)
        
        def _validate_param(param, param_name):
            if param is not None:
                if isinstance(param, list) and len(param) != n_rows and len(param) != 1:
                    raise DROMAValidationError(
                        f"{param_name} list length ({len(param)}) must match "
                        f"name_mapping rows ({n_rows}) or be a single value"
                    )
        
        _validate_param(data_type, "data_type")
        _validate_param(tumor_type, "tumor_type")
        _validate_param(patient_id, "patient_id")
        _validate_param(gender, "gender")
        _validate_param(age, "age")
        _validate_param(full_ethnicity, "full_ethnicity")
        _validate_param(simple_ethnicity, "simple_ethnicity")
    
    # Determine table name and columns
    if anno_type == 'sample':
        table_name = 'sample_anno'
        id_column = 'SampleID'
        index_prefix = 'UM_SAMPLE_'
    else:
        table_name = 'drug_anno'
        id_column = 'DrugName'
        index_prefix = 'UM_DRUG_'
    
    cursor = connection.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cursor.fetchone():
        raise DROMATableError(f"Annotation table '{table_name}' not found in database")
    
    # Get existing annotation data
    existing_anno = pd.read_sql_query(f"SELECT * FROM {table_name}", connection)
    
    # Find maximum IndexID number for generating new IDs
    max_index_num = 0
    if 'IndexID' in existing_anno.columns and not existing_anno.empty:
        index_ids = existing_anno['IndexID'].dropna()
        if not index_ids.empty:
            numbers = index_ids.str.replace(index_prefix, '').astype(str)
            numeric_ids = pd.to_numeric(numbers, errors='coerce').dropna()
            if not numeric_ids.empty:
                max_index_num = int(numeric_ids.max())
    
    added_count = 0
    skipped_count = 0
    current_index_num = max_index_num
    
    # Helper function to get parameter value for row i
    def _get_param_value(param, i):
        if param is None:
            return None
        if isinstance(param, list):
            return param[i] if len(param) > 1 else param[0]
        return param
    
    # Process each entry
    for i, row in name_mapping.iterrows():
        new_name = row['new_name']
        original_name = row['original_name']
        match_confidence = row['match_confidence']
        
        # Check if entry already exists
        if anno_type == 'sample':
            existing_check = existing_anno[
                (existing_anno['SampleID'] == new_name) & 
                (existing_anno['ProjectID'] == project_name)
            ]
        else:
            existing_check = existing_anno[
                (existing_anno['DrugName'] == new_name) & 
                (existing_anno['ProjectID'] == project_name)
            ]
        
        if not existing_check.empty:
            skipped_count += 1
            continue
        
        # Generate new IndexID
        current_index_num += 1
        new_index_id = f"{index_prefix}{current_index_num}"
        
        # Prepare insert data
        if anno_type == 'sample':
            insert_data = {
                'SampleID': new_name,
                'PatientID': _get_param_value(patient_id, i),
                'ProjectID': project_name,
                'HarmonizedIdentifier': None,
                'TumorType': _get_param_value(tumor_type, i),
                'MolecularSubtype': None,
                'Gender': _get_param_value(gender, i),
                'Age': _get_param_value(age, i),
                'FullEthnicity': _get_param_value(full_ethnicity, i),
                'SimpleEthnicity': _get_param_value(simple_ethnicity, i),
                'TNMstage': None,
                'Primary_Metastasis': None,
                'DataType': _get_param_value(data_type, i),
                'ProjectRawName': original_name,
                'AlternateName': None,
                'IndexID': new_index_id
            }
        else:
            insert_data = {
                'DrugName': new_name,
                'ProjectID': project_name,
                'Harmonized ID (Pubchem ID)': None,
                'Source for Clinical Information': None,
                'Clinical Phase': None,
                'MOA': None,
                'Targets': None,
                'ProjectRawName': original_name,
                'IndexID': new_index_id
            }
        
        # Insert new entry
        columns = ', '.join(f'`{k}`' for k in insert_data.keys())
        placeholders = ', '.join('?' * len(insert_data))
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        try:
            cursor.execute(insert_query, list(insert_data.values()))
            added_count += 1
        except sqlite3.Error as e:
            logger.error(f"Failed to insert entry for {new_name}: {e}")
            continue
    
    connection.commit()
    
    # Print summary
    logger.info(f"Updated {table_name} table:")
    logger.info(f"  Added: {added_count} new entries")
    logger.info(f"  Skipped: {skipped_count} existing entries")
    
    if current_index_num > max_index_num:
        logger.info(f"  Generated new IndexIDs from {index_prefix}{max_index_num + 1} to {index_prefix}{current_index_num}")
    
    # Print match confidence summary
    if 'match_type' in name_mapping.columns:
        match_summary = name_mapping['match_type'].value_counts()
        logger.info("  Match types for processed entries:")
        for match_type, count in match_summary.items():
            logger.info(f"    {match_type}: {count}")
    else:
        confidence_summary = name_mapping['match_confidence'].value_counts()
        logger.info("  Match confidence for processed entries:")
        for confidence, count in confidence_summary.items():
            logger.info(f"    {confidence}: {count}")
    
    return True 