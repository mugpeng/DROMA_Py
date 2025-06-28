"""
Name harmonization functions for DROMA-Py.

This module provides functions for checking and harmonizing sample and drug names
against the DROMA database using fuzzy matching and name cleaning approaches.
"""

import sqlite3
import pandas as pd
import re
from typing import Optional, List, Dict, Union
import logging
from rapidfuzz import fuzz, process

from .database import get_global_connection
from .exceptions import DROMAConnectionError, DROMATableError

logger = logging.getLogger(__name__)


def _clean_name(name: str) -> str:
    """
    Clean names for better matching.
    
    Args:
        name: Name to clean
        
    Returns:
        str: Cleaned name
    """
    if pd.isna(name) or name is None:
        return ""
    
    # Convert to lowercase
    name = str(name).lower()
    
    # Remove [?]
    name = name.replace("[?]", "")
    
    # Remove Chinese characters (if any)
    name = re.sub(r'[\u4e00-\u9fff]', '', name)
    
    # First remove [xx] format and its contents
    name = re.sub(r'\[.*?\]', '', name)
    
    # Handle parentheses - only remove if there's content outside them
    if not re.match(r'^\s*\(.*\)\s*$', name):
        name = re.sub(r'\s*\([^)]+\)', '', name)
    else:
        # For names entirely in parentheses, remove the parentheses but keep content
        name = re.sub(r'^\s*\(|\)\s*$', '', name)
    
    # Remove special characters and extra spaces
    name = re.sub(r'[^a-z0-9]', '', name)
    name = name.strip()
    
    return name


def _clean_drug_name(name: str) -> str:
    """
    Clean drug names for better matching.
    
    Args:
        name: Drug name to clean
        
    Returns:
        str: Cleaned drug name
    """
    if pd.isna(name) or name is None:
        return ""
    
    # Convert to lowercase
    name = str(name).lower()
    
    # Remove [?]
    name = name.replace("[?]", "")
    
    # Remove Chinese characters (if any)
    name = re.sub(r'[\u4e00-\u9fff]', '', name)
    
    # Handle parentheses - only remove if there's content outside them
    if not re.match(r'^\s*\(.*\)\s*$', name):
        name = re.sub(r'\s*\([^)]+\)', '', name)
    else:
        # For names entirely in parentheses, remove the parentheses but keep content
        name = re.sub(r'^\s*\(|\)\s*$', '', name)
    
    # Remove special characters but keep spaces for drug names
    name = re.sub(r'[^a-z0-9]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    
    return name


def check_droma_sample_names(
    sample_names: List[str],
    connection: Optional[sqlite3.Connection] = None,
    max_distance: float = 0.2,
    min_name_length: int = 5
) -> pd.DataFrame:
    """
    Check sample names against the sample_anno table and provide harmonized mappings.
    
    Uses fuzzy matching and name cleaning approach to match sample names.
    
    Args:
        sample_names: List of sample names to check and harmonize
        connection: Optional database connection. If None, uses global connection
        max_distance: Maximum distance for fuzzy matching (default: 0.2)
        min_name_length: Minimum name length for partial matching (default: 5)
        
    Returns:
        pd.DataFrame: DataFrame with columns: original_name, cleaned_name, harmonized_name, 
                     match_type, match_confidence, new_name
                     
    Examples:
        >>> # Check sample names from a data matrix
        >>> sample_names = ["MCF7", "HeLa", "A549_lung", "Unknown_Sample"]
        >>> name_mapping = check_droma_sample_names(sample_names)
        >>> print(name_mapping[['original_name', 'harmonized_name', 'match_confidence']])
    """
    if connection is None:
        connection = get_global_connection()
    
    cursor = connection.cursor()
    
    # Check if sample_anno table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    if "sample_anno" not in all_tables:
        raise DROMATableError("Sample annotation table 'sample_anno' not found in database")
    
    # Get sample annotation data
    sample_anno = pd.read_sql_query("SELECT * FROM sample_anno", connection)
    
    if sample_anno.empty:
        logger.warning("Sample annotation table is empty")
        # Return basic mapping with no matches
        result = pd.DataFrame({
            'original_name': sample_names,
            'cleaned_name': [_clean_name(name) for name in sample_names],
            'harmonized_name': sample_names,
            'match_type': 'no_match',
            'match_confidence': 'none',
            'new_name': sample_names
        })
        return result
    
    # Clean reference names in sample_anno
    sample_anno['clean_sampleid'] = sample_anno['SampleID'].apply(_clean_name)
    sample_anno['clean_rawname'] = sample_anno['ProjectRawName'].apply(_clean_name)
    
    # Handle AlternateName column if it exists
    alternate_mapping = pd.DataFrame()
    if 'AlternateName' in sample_anno.columns:
        alt_data = []
        for _, row in sample_anno.iterrows():
            harmonized_name = row['SampleID']
            
            # Add the harmonized name itself
            alt_data.append({
                'raw_name': harmonized_name,
                'harmonized_name': harmonized_name,
                'clean_name': _clean_name(harmonized_name)
            })
            
            # Process alternate names if they exist
            if pd.notna(row['AlternateName']) and row['AlternateName'] != "":
                alt_names = re.split(r'[:|]', str(row['AlternateName']))
                alt_names = [name.strip() for name in alt_names if name.strip() and name.strip() != "|"]
                
                for alt_name in alt_names:
                    alt_data.append({
                        'raw_name': alt_name,
                        'harmonized_name': harmonized_name,
                        'clean_name': _clean_name(alt_name)
                    })
        
        alternate_mapping = pd.DataFrame(alt_data)
    
    # Clean input sample names
    sample_names_clean = [_clean_name(name) for name in sample_names]
    
    # Create result data frame
    result_data = []
    
    # Match each sample name
    for i, original_name in enumerate(sample_names):
        clean_name = sample_names_clean[i]
        
        # For very long names, keep original
        if len(original_name) > 30:
            result_data.append({
                'original_name': original_name,
                'cleaned_name': clean_name,
                'harmonized_name': original_name,
                'match_type': 'keep_original_long',
                'match_confidence': 'medium',
                'new_name': original_name
            })
            continue
        
        matched = False
        
        # Try exact match with SampleID
        exact_sampleid = sample_anno[sample_anno['clean_sampleid'] == clean_name]
        if not exact_sampleid.empty:
            harmonized = exact_sampleid.iloc[0]['SampleID']
            result_data.append({
                'original_name': original_name,
                'cleaned_name': clean_name,
                'harmonized_name': harmonized,
                'match_type': 'exact_sampleid',
                'match_confidence': 'high',
                'new_name': harmonized
            })
            matched = True
        
        # Try exact match with ProjectRawName
        elif not sample_anno[sample_anno['clean_rawname'] == clean_name].empty:
            exact_rawname = sample_anno[sample_anno['clean_rawname'] == clean_name]
            harmonized = exact_rawname.iloc[0]['SampleID']
            result_data.append({
                'original_name': original_name,
                'cleaned_name': clean_name,
                'harmonized_name': harmonized,
                'match_type': 'exact_rawname',
                'match_confidence': 'high',
                'new_name': harmonized
            })
            matched = True
        
        # Try exact match with AlternateName if available
        elif not alternate_mapping.empty and not alternate_mapping[alternate_mapping['clean_name'] == clean_name].empty:
            exact_alternate = alternate_mapping[alternate_mapping['clean_name'] == clean_name]
            harmonized = exact_alternate.iloc[0]['harmonized_name']
            result_data.append({
                'original_name': original_name,
                'cleaned_name': clean_name,
                'harmonized_name': harmonized,
                'match_type': 'exact_alternate',
                'match_confidence': 'high',
                'new_name': harmonized
            })
            matched = True
        
        if not matched and len(clean_name) >= 3:
            # Try fuzzy match with SampleID
            choices = sample_anno['clean_sampleid'].dropna().tolist()
            if choices:
                best_match = process.extractOne(
                    clean_name, choices, 
                    scorer=fuzz.ratio,
                    score_cutoff=int((1-max_distance) * 100)
                )
                if best_match:
                    match_idx = sample_anno[sample_anno['clean_sampleid'] == best_match[0]].index[0]
                    harmonized = sample_anno.loc[match_idx, 'SampleID']
                    result_data.append({
                        'original_name': original_name,
                        'cleaned_name': clean_name,
                        'harmonized_name': harmonized,
                        'match_type': 'fuzzy_sampleid',
                        'match_confidence': 'medium',
                        'new_name': harmonized
                    })
                    matched = True
            
            # Try fuzzy match with ProjectRawName
            if not matched:
                choices = sample_anno['clean_rawname'].dropna().tolist()
                if choices:
                    best_match = process.extractOne(
                        clean_name, choices,
                        scorer=fuzz.ratio,
                        score_cutoff=int((1-max_distance) * 100)
                    )
                    if best_match:
                        match_idx = sample_anno[sample_anno['clean_rawname'] == best_match[0]].index[0]
                        harmonized = sample_anno.loc[match_idx, 'SampleID']
                        result_data.append({
                            'original_name': original_name,
                            'cleaned_name': clean_name,
                            'harmonized_name': harmonized,
                            'match_type': 'fuzzy_rawname',
                            'match_confidence': 'medium',
                            'new_name': harmonized
                        })
                        matched = True
            
            # Try fuzzy match with AlternateName if available
            if not matched and not alternate_mapping.empty:
                choices = alternate_mapping['clean_name'].dropna().tolist()
                if choices:
                    best_match = process.extractOne(
                        clean_name, choices,
                        scorer=fuzz.ratio,
                        score_cutoff=int((1-max_distance) * 100)
                    )
                    if best_match:
                        match_idx = alternate_mapping[alternate_mapping['clean_name'] == best_match[0]].index[0]
                        harmonized = alternate_mapping.loc[match_idx, 'harmonized_name']
                        result_data.append({
                            'original_name': original_name,
                            'cleaned_name': clean_name,
                            'harmonized_name': harmonized,
                            'match_type': 'fuzzy_alternate',
                            'match_confidence': 'medium',
                            'new_name': harmonized
                        })
                        matched = True
        
        # Try partial match (sample name is contained in annotation)
        if not matched and len(clean_name) >= min_name_length:
            # Check if sample name is contained in SampleID names
            partial_sampleid = sample_anno[sample_anno['clean_sampleid'].str.contains(clean_name, na=False)]
            if not partial_sampleid.empty:
                harmonized = partial_sampleid.iloc[0]['SampleID']
                result_data.append({
                    'original_name': original_name,
                    'cleaned_name': clean_name,
                    'harmonized_name': harmonized,
                    'match_type': 'partial_sampleid',
                    'match_confidence': 'low',
                    'new_name': harmonized
                })
                matched = True
            
            # Check if sample name is contained in ProjectRawName names
            elif not sample_anno[sample_anno['clean_rawname'].str.contains(clean_name, na=False)].empty:
                partial_rawname = sample_anno[sample_anno['clean_rawname'].str.contains(clean_name, na=False)]
                harmonized = partial_rawname.iloc[0]['SampleID']
                result_data.append({
                    'original_name': original_name,
                    'cleaned_name': clean_name,
                    'harmonized_name': harmonized,
                    'match_type': 'partial_rawname',
                    'match_confidence': 'low',
                    'new_name': harmonized
                })
                matched = True
        
        # No match found - use cleaned name
        if not matched:
            result_data.append({
                'original_name': original_name,
                'cleaned_name': clean_name,
                'harmonized_name': clean_name,
                'match_type': 'no_match',
                'match_confidence': 'none',
                'new_name': original_name
            })
    
    result_df = pd.DataFrame(result_data)
    
    # Print summary
    match_summary = result_df['match_type'].value_counts()
    logger.info("Sample name matching summary:")
    for match_type, count in match_summary.items():
        logger.info(f"    {match_type}: {count}")
    
    # Warn about low confidence matches
    low_confidence = result_df[result_df['match_confidence'].isin(['medium', 'low'])]
    if not low_confidence.empty:
        logger.warning(f"{len(low_confidence)} samples have medium/low confidence matches.")
        logger.info("Consider manual review of these matches:")
        for i in range(min(5, len(low_confidence))):
            row = low_confidence.iloc[i]
            logger.info(f"    {row['original_name']} -> {row['harmonized_name']} ({row['match_type']})")
        if len(low_confidence) > 5:
            logger.info(f"    ... and {len(low_confidence) - 5} more")
    
    return result_df


def check_droma_drug_names(
    drug_names: List[str],
    connection: Optional[sqlite3.Connection] = None,
    max_distance: float = 0.2,
    min_name_length: int = 5,
    keep_long_names_threshold: int = 17
) -> pd.DataFrame:
    """
    Check drug names against the drug_anno table and provide harmonized mappings.
    
    Uses fuzzy matching and name cleaning approach to match drug names.
    
    Args:
        drug_names: List of drug names to check and harmonize
        connection: Optional database connection. If None, uses global connection
        max_distance: Maximum distance for fuzzy matching (default: 0.2)
        min_name_length: Minimum name length for partial matching (default: 5)
        keep_long_names_threshold: Names longer than this will be kept as original (default: 17)
        
    Returns:
        pd.DataFrame: DataFrame with columns: original_name, cleaned_name, harmonized_name, 
                     match_type, match_confidence, new_name
                     
    Examples:
        >>> # Check drug names from a drug response matrix
        >>> drug_names = ["Tamoxifen", "cisplatin", "Doxorubicin_HCl", "Unknown_Compound"]
        >>> name_mapping = check_droma_drug_names(drug_names)
        >>> print(name_mapping[['original_name', 'harmonized_name', 'match_confidence']])
    """
    if connection is None:
        connection = get_global_connection()
    
    cursor = connection.cursor()
    
    # Check if drug_anno table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    if "drug_anno" not in all_tables:
        raise DROMATableError("Drug annotation table 'drug_anno' not found in database")
    
    # Get drug annotation data
    drug_anno = pd.read_sql_query("SELECT * FROM drug_anno", connection)
    
    if drug_anno.empty:
        logger.warning("Drug annotation table is empty")
        # Return basic mapping with no matches
        result = pd.DataFrame({
            'original_name': drug_names,
            'cleaned_name': [_clean_drug_name(name) for name in drug_names],
            'harmonized_name': drug_names,
            'match_type': 'no_match',
            'match_confidence': 'none',
            'new_name': drug_names
        })
        return result
    
    # Clean reference names in drug_anno
    drug_anno['clean_drugname'] = drug_anno['DrugName'].apply(_clean_drug_name)
    drug_anno['clean_rawname'] = drug_anno['ProjectRawName'].apply(_clean_drug_name)
    
    # Clean input drug names
    drug_names_clean = [_clean_drug_name(name) for name in drug_names]
    
    # Create result data frame
    result_data = []
    
    # Match each drug name
    for i, original_name in enumerate(drug_names):
        clean_name = drug_names_clean[i]
        
        # For very long drug names, keep original
        if len(original_name) > keep_long_names_threshold:
            result_data.append({
                'original_name': original_name,
                'cleaned_name': clean_name,
                'harmonized_name': original_name,
                'match_type': 'keep_original_long',
                'match_confidence': 'medium',
                'new_name': original_name
            })
            continue
        
        matched = False
        
        # Try exact match with DrugName
        exact_drugname = drug_anno[drug_anno['clean_drugname'] == clean_name]
        if not exact_drugname.empty:
            harmonized = exact_drugname.iloc[0]['DrugName']
            result_data.append({
                'original_name': original_name,
                'cleaned_name': clean_name,
                'harmonized_name': harmonized,
                'match_type': 'exact_drugname',
                'match_confidence': 'high',
                'new_name': harmonized
            })
            matched = True
        
        # Try exact match with ProjectRawName
        elif not drug_anno[drug_anno['clean_rawname'] == clean_name].empty:
            exact_rawname = drug_anno[drug_anno['clean_rawname'] == clean_name]
            harmonized = exact_rawname.iloc[0]['DrugName']
            result_data.append({
                'original_name': original_name,
                'cleaned_name': clean_name,
                'harmonized_name': harmonized,
                'match_type': 'exact_rawname',
                'match_confidence': 'high',
                'new_name': harmonized
            })
            matched = True
        
        if not matched and len(clean_name) >= 3:
            # Try fuzzy match with DrugName
            choices = drug_anno['clean_drugname'].dropna().tolist()
            if choices:
                best_match = process.extractOne(
                    clean_name, choices,
                    scorer=fuzz.ratio,
                    score_cutoff=int((1-max_distance) * 100)
                )
                if best_match:
                    match_idx = drug_anno[drug_anno['clean_drugname'] == best_match[0]].index[0]
                    harmonized = drug_anno.loc[match_idx, 'DrugName']
                    result_data.append({
                        'original_name': original_name,
                        'cleaned_name': clean_name,
                        'harmonized_name': harmonized,
                        'match_type': 'fuzzy_drugname',
                        'match_confidence': 'medium',
                        'new_name': harmonized
                    })
                    matched = True
            
            # Try fuzzy match with ProjectRawName
            if not matched:
                choices = drug_anno['clean_rawname'].dropna().tolist()
                if choices:
                    best_match = process.extractOne(
                        clean_name, choices,
                        scorer=fuzz.ratio,
                        score_cutoff=int((1-max_distance) * 100)
                    )
                    if best_match:
                        match_idx = drug_anno[drug_anno['clean_rawname'] == best_match[0]].index[0]
                        harmonized = drug_anno.loc[match_idx, 'DrugName']
                        result_data.append({
                            'original_name': original_name,
                            'cleaned_name': clean_name,
                            'harmonized_name': harmonized,
                            'match_type': 'fuzzy_rawname',
                            'match_confidence': 'medium',
                            'new_name': harmonized
                        })
                        matched = True
        
        # Try partial match (drug name is contained in annotation)
        if not matched and len(clean_name) >= min_name_length:
            # Check if drug name is contained in DrugName names
            partial_drugname = drug_anno[drug_anno['clean_drugname'].str.contains(clean_name, na=False)]
            if not partial_drugname.empty:
                harmonized = partial_drugname.iloc[0]['DrugName']
                result_data.append({
                    'original_name': original_name,
                    'cleaned_name': clean_name,
                    'harmonized_name': harmonized,
                    'match_type': 'partial_drugname',
                    'match_confidence': 'low',
                    'new_name': harmonized
                })
                matched = True
            
            # Check if drug name is contained in ProjectRawName names
            elif not drug_anno[drug_anno['clean_rawname'].str.contains(clean_name, na=False)].empty:
                partial_rawname = drug_anno[drug_anno['clean_rawname'].str.contains(clean_name, na=False)]
                harmonized = partial_rawname.iloc[0]['DrugName']
                result_data.append({
                    'original_name': original_name,
                    'cleaned_name': clean_name,
                    'harmonized_name': harmonized,
                    'match_type': 'partial_rawname',
                    'match_confidence': 'low',
                    'new_name': harmonized
                })
                matched = True
        
        # No match found - use cleaned name
        if not matched:
            result_data.append({
                'original_name': original_name,
                'cleaned_name': clean_name,
                'harmonized_name': clean_name,
                'match_type': 'no_match',
                'match_confidence': 'none',
                'new_name': original_name
            })
    
    result_df = pd.DataFrame(result_data)
    
    # Print summary
    match_summary = result_df['match_type'].value_counts()
    logger.info("Drug name matching summary:")
    for match_type, count in match_summary.items():
        logger.info(f"    {match_type}: {count}")
    
    # Warn about low confidence matches
    low_confidence = result_df[result_df['match_confidence'].isin(['medium', 'low'])]
    if not low_confidence.empty:
        logger.warning(f"{len(low_confidence)} drugs have medium/low confidence matches.")
        logger.info("Consider manual review of these matches:")
        for i in range(min(5, len(low_confidence))):
            row = low_confidence.iloc[i]
            logger.info(f"    {row['original_name']} -> {row['harmonized_name']} ({row['match_type']})")
        if len(low_confidence) > 5:
            logger.info(f"    ... and {len(low_confidence) - 5} more")
    
    return result_df