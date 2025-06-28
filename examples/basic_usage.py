#!/usr/bin/env python3
"""
Basic Usage Example for DROMA-Py

This example demonstrates fundamental database operations using DROMA-Py,
including connecting to databases, listing projects, and basic data retrieval.
"""

import os
import pandas as pd
import droma_py as droma
from droma_py.exceptions import DROMAError, DROMAConnectionError

def main():
    """Demonstrate basic DROMA-Py usage."""
    
    # Example database path (adjust to your actual database location)
    db_path = "path/to/your/droma.sqlite"
    # db_path = "../../250520-DROMA_DB/sql_db/droma.sqlite"
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Please adjust the db_path variable to point to your DROMA database")
        return
    
    print("=== DROMA-Py Basic Usage Example ===\n")
    
    # =====================================================================
    # 1. Database Connection
    # =====================================================================
    print("1. Connecting to Database")
    print("-" * 30)
    
    try:
        # Method 1: Functional interface
        connection = droma.connect_droma_database(db_path)
        print(f"✓ Connected to database: {db_path}")
        
        # Method 2: Object-oriented interface (recommended)
        with droma.DROMADatabase(db_path) as db:
            print("✓ Connected using object-oriented interface")
            
            # Basic database info
            tables = db.list_tables()
            print(f"✓ Database contains {len(tables)} tables")
            
    except DROMAConnectionError as e:
        print(f"✗ Connection failed: {e}")
        return
    except DROMAError as e:
        print(f"✗ DROMA error: {e}")
        return
    
    print()
    
    # =====================================================================
    # 2. List Projects and Tables
    # =====================================================================
    print("2. Exploring Database Contents")
    print("-" * 30)
    
    try:
        # List all database tables
        tables = droma.list_droma_database_tables()
        print(f"Available tables ({len(tables)}):")
        for table in tables[:10]:  # Show first 10 tables
            print(f"  - {table}")
        if len(tables) > 10:
            print(f"  ... and {len(tables) - 10} more")
        
        print()
        
        # List projects
        projects = droma.list_droma_projects()
        if not projects.empty:
            print("Available projects:")
            print(projects[['project_name', 'dataset_type', 'tumor_type']].head())
        else:
            print("No projects found in database")
            
    except DROMAError as e:
        print(f"✗ Error listing contents: {e}")
    
    print()
    
    # =====================================================================
    # 3. Sample and Feature Exploration
    # =====================================================================
    print("3. Exploring Samples and Features")
    print("-" * 30)
    
    try:
        # Get project names for examples
        projects = droma.list_droma_projects()
        if not projects.empty:
            example_project = projects.iloc[0]['project_name']
            print(f"Using project '{example_project}' for examples")
            
            # List samples
            samples = droma.list_droma_samples(example_project, limit=10)
            if not samples.empty:
                print(f"\nFirst 10 samples from {example_project}:")
                print(samples[['sample_id', 'data_type', 'tumor_type']].head())
            
            # List features for different data types
            data_types = ['mRNA', 'cnv', 'drug']
            for data_type in data_types:
                try:
                    features = droma.list_droma_features(
                        example_project, data_type, limit=5
                    )
                    if not features.empty:
                        print(f"\nFirst 5 {data_type} features:")
                        print(features['feature_name'].tolist())
                except DROMAError:
                    print(f"No {data_type} data available for {example_project}")
        else:
            print("No projects available for exploration")
            
    except DROMAError as e:
        print(f"✗ Error exploring data: {e}")
    
    print()
    
    # =====================================================================
    # 4. Annotation Retrieval
    # =====================================================================
    print("4. Retrieving Annotations")
    print("-" * 30)
    
    try:
        # Get sample annotations
        sample_anno = droma.get_droma_annotation("sample", limit=10)
        if not sample_anno.empty:
            print("Sample annotations (first 10 rows):")
            print(sample_anno.head())
        
        print()
        
        # Get drug annotations
        drug_anno = droma.get_droma_annotation("drug", limit=5)
        if not drug_anno.empty:
            print("Drug annotations (first 5 rows):")
            print(drug_anno[['drug_name', 'targets', 'moa']].head())
            
    except DROMAError as e:
        print(f"✗ Error retrieving annotations: {e}")
    
    print()
    
    # =====================================================================
    # 5. Simple Data Retrieval
    # =====================================================================
    print("5. Data Retrieval Example")
    print("-" * 30)
    
    try:
        projects = droma.list_droma_projects()
        if not projects.empty:
            example_project = projects.iloc[0]['project_name']
            
            # Try to get some mRNA data
            features = droma.list_droma_features(
                example_project, "mRNA", limit=3
            )
            
            if not features.empty:
                example_gene = features.iloc[0]['feature_name']
                print(f"Retrieving {example_gene} expression data...")
                
                gene_data = droma.get_feature_from_database(
                    "mRNA", example_gene,
                    data_sources=[example_project]
                )
                
                if gene_data and example_project in gene_data:
                    data_df = pd.DataFrame(gene_data[example_project])
                    print(f"✓ Retrieved data shape: {data_df.shape}")
                    print("Data preview:")
                    print(data_df.head())
                else:
                    print("No data retrieved for the specified gene")
            else:
                print("No mRNA features available in the example project")
        else:
            print("No projects available for data retrieval")
            
    except DROMAError as e:
        print(f"✗ Error retrieving data: {e}")
    
    print()
    
    # =====================================================================
    # 6. Clean Up
    # =====================================================================
    print("6. Cleanup")
    print("-" * 30)
    
    try:
        droma.close_droma_database()
        print("✓ Database connection closed")
    except DROMAError as e:
        print(f"Warning: Error during cleanup: {e}")
    
    print("\n=== Example completed successfully! ===")

if __name__ == "__main__":
    main() 