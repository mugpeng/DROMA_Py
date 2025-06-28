#!/usr/bin/env python3
"""
Batch Processing Example for DROMA-Py

This example demonstrates batch data processing, database updates,
and bulk operations using DROMA-Py for handling large-scale data operations.
"""

import os
import pandas as pd
import numpy as np
import droma_py as droma
from droma_py.exceptions import DROMAError
from pathlib import Path
import time

def main():
    """Demonstrate batch processing capabilities with DROMA-Py."""
    
    # Example database path (adjust to your actual database location)
    db_path = "path/to/your/droma.sqlite"
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Please adjust the db_path variable to point to your DROMA database")
        return
    
    print("=== DROMA-Py Batch Processing Example ===\n")
    
    # Connect to database
    try:
        droma.connect_droma_database(db_path)
        print(f"✓ Connected to database: {db_path}\n")
    except DROMAError as e:
        print(f"✗ Connection failed: {e}")
        return
    
    # =====================================================================
    # 1. Batch Data Generation (Simulating External Data)
    # =====================================================================
    print("1. Generating Simulated Batch Data")
    print("-" * 40)
    
    # Simulate multiple datasets that need to be processed
    batch_datasets = {}
    
    # Generate sample expression data
    np.random.seed(42)  # For reproducible results
    n_genes = 100
    n_samples = 50
    
    print("Generating synthetic datasets...")
    
    # Dataset 1: mRNA expression
    genes = [f"GENE_{i:03d}" for i in range(1, n_genes + 1)]
    samples = [f"SAMPLE_{i:03d}" for i in range(1, n_samples + 1)]
    
    expr_data = pd.DataFrame(
        np.random.normal(5, 2, (n_genes, n_samples)),
        index=genes,
        columns=samples
    )
    batch_datasets['test_project_mRNA'] = expr_data
    print(f"✓ Generated mRNA data: {expr_data.shape}")
    
    # Dataset 2: Copy number variation
    cnv_data = pd.DataFrame(
        np.random.normal(0, 0.5, (n_genes, n_samples)),
        index=genes,
        columns=samples
    )
    batch_datasets['test_project_cnv'] = cnv_data
    print(f"✓ Generated CNV data: {cnv_data.shape}")
    
    # Dataset 3: Drug response data
    n_drugs = 20
    drugs = [f"DRUG_{i:03d}" for i in range(1, n_drugs + 1)]
    
    drug_data = pd.DataFrame(
        np.random.uniform(0, 1, (n_drugs, n_samples)),
        index=drugs,
        columns=samples
    )
    batch_datasets['test_project_drug'] = drug_data
    print(f"✓ Generated drug response data: {drug_data.shape}")
    
    print(f"Total datasets generated: {len(batch_datasets)}")
    print()
    
    # =====================================================================
    # 2. Batch Database Updates
    # =====================================================================
    print("2. Batch Database Updates")
    print("-" * 40)
    
    update_results = {}
    
    print("Updating database with batch datasets...")
    start_time = time.time()
    
    for table_name, data in batch_datasets.items():
        try:
            print(f"Updating {table_name}... ", end="")
            
            # Update database with overwrite to ensure clean data
            droma.update_droma_database(
                data, 
                table_name,
                overwrite=True
            )
            
            update_results[table_name] = {
                'status': 'success',
                'rows': data.shape[0],
                'cols': data.shape[1]
            }
            print(f"✓ Success ({data.shape[0]} × {data.shape[1]})")
            
        except DROMAError as e:
            update_results[table_name] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"✗ Failed: {e}")
    
    total_time = time.time() - start_time
    
    # Summary of updates
    successful_updates = sum(1 for r in update_results.values() if r['status'] == 'success')
    print(f"\nBatch update summary:")
    print(f"  Successful: {successful_updates}/{len(batch_datasets)}")
    print(f"  Total time: {total_time:.2f} seconds")
    print(f"  Average time per table: {total_time/len(batch_datasets):.2f} seconds")
    print()
    
    # =====================================================================
    # 3. Batch Annotation Updates
    # =====================================================================
    print("3. Batch Annotation Updates")
    print("-" * 40)
    
    try:
        # Create sample annotations
        sample_annotations = pd.DataFrame({
            'sample_id': samples,
            'data_type': ['CellLine'] * len(samples),
            'tumor_type': np.random.choice(['breast', 'lung', 'colon'], len(samples)),
            'tissue': np.random.choice(['primary', 'metastatic'], len(samples)),
            'gender': np.random.choice(['male', 'female'], len(samples)),
            'age': np.random.randint(20, 80, len(samples))
        })
        
        print(f"Updating sample annotations for {len(sample_annotations)} samples...")
        droma.update_droma_annotation(
            "sample", 
            sample_annotations, 
            "test_project",
            data_type="CellLine"
        )
        print("✓ Sample annotations updated")
        
        # Create drug annotations
        drug_annotations = pd.DataFrame({
            'drug_name': drugs,
            'targets': [f"TARGET_{i}" for i in range(1, len(drugs) + 1)],
            'moa': np.random.choice(['kinase_inhibitor', 'dna_damage', 'apoptosis'], len(drugs)),
            'phase': np.random.choice(['I', 'II', 'III', 'approved'], len(drugs))
        })
        
        print(f"Updating drug annotations for {len(drug_annotations)} drugs...")
        droma.update_droma_annotation(
            "drug",
            drug_annotations,
            "test_project"
        )
        print("✓ Drug annotations updated")
        
    except DROMAError as e:
        print(f"✗ Error updating annotations: {e}")
    
    print()
    
    # =====================================================================
    # 4. Batch Data Validation
    # =====================================================================
    print("4. Batch Data Validation")
    print("-" * 40)
    
    validation_results = {}
    
    print("Validating uploaded data...")
    
    for table_name in batch_datasets.keys():
        try:
            # Check if table exists in database
            with droma.DROMADatabase(db_path) as db:
                if db.table_exists(table_name):
                    # Get row count from database
                    result = db.fetchone(f"SELECT COUNT(*) as count FROM `{table_name}`")
                    db_rows = result['count'] if result else 0
                    
                    original_rows = batch_datasets[table_name].shape[0]
                    
                    validation_results[table_name] = {
                        'exists': True,
                        'original_rows': original_rows,
                        'db_rows': db_rows,
                        'valid': db_rows == original_rows
                    }
                    
                    status = "✓" if db_rows == original_rows else "✗"
                    print(f"{status} {table_name}: {db_rows}/{original_rows} rows")
                else:
                    validation_results[table_name] = {
                        'exists': False,
                        'valid': False
                    }
                    print(f"✗ {table_name}: Table not found")
                    
        except DROMAError as e:
            validation_results[table_name] = {
                'exists': False,
                'valid': False,
                'error': str(e)
            }
            print(f"✗ {table_name}: Validation error - {e}")
    
    # Validation summary
    valid_tables = sum(1 for r in validation_results.values() if r.get('valid', False))
    print(f"\nValidation summary: {valid_tables}/{len(batch_datasets)} tables valid")
    print()
    
    # =====================================================================
    # 5. Batch Data Retrieval and Quality Check
    # =====================================================================
    print("5. Batch Data Retrieval and Quality Check")
    print("-" * 40)
    
    print("Performing quality checks on uploaded data...")
    
    try:
        # Check data consistency across tables
        for table_name in batch_datasets.keys():
            data_type = table_name.split('_')[-1]  # Extract data type
            
            # Get feature list
            features = droma.list_droma_features("test_project", data_type, limit=5)
            
            if not features.empty:
                # Sample a feature and check data quality
                sample_feature = features.iloc[0]['feature_name']
                
                feature_data = droma.get_feature_from_database(
                    data_type, 
                    sample_feature,
                    data_sources=["test_project"]
                )
                
                if feature_data and "test_project" in feature_data:
                    values = list(feature_data["test_project"].values())
                    
                    # Basic quality metrics
                    n_values = len(values)
                    n_missing = sum(1 for v in values if pd.isna(v))
                    mean_val = np.nanmean(values) if values else 0
                    std_val = np.nanstd(values) if values else 0
                    
                    print(f"✓ {data_type:8} | {sample_feature:12} | "
                          f"N={n_values:3} | Missing={n_missing:2} | "
                          f"Mean={mean_val:.2f} | Std={std_val:.2f}")
                else:
                    print(f"✗ {data_type:8} | No data retrieved")
            else:
                print(f"✗ {data_type:8} | No features found")
                
    except DROMAError as e:
        print(f"✗ Error in quality check: {e}")
    
    print()
    
    # =====================================================================
    # 6. Batch Name Harmonization
    # =====================================================================
    print("6. Batch Name Harmonization")
    print("-" * 40)
    
    # Simulate external data with various naming conventions
    external_samples = [
        "SAMPLE_001", "sample_002", "Sample-003", "SAMPLE 004", "unknown_sample"
    ]
    
    external_drugs = [
        "DRUG_001", "drug_002", "Drug-003", "DRUG 004", "unknown_drug"
    ]
    
    print("Testing name harmonization with external naming conventions...")
    
    try:
        # Batch harmonize sample names
        sample_mapping = droma.check_droma_sample_names(
            external_samples,
            threshold=0.8
        )
        
        print("Sample name harmonization results:")
        for _, row in sample_mapping.iterrows():
            original = row['original_name']
            harmonized = row['harmonized_name']
            confidence = row['match_confidence']
            
            if pd.notna(harmonized):
                print(f"  ✓ {original:15} → {harmonized:15} ({confidence:.3f})")
            else:
                print(f"  ✗ {original:15} → No match found")
        
        # Batch harmonize drug names
        drug_mapping = droma.check_droma_drug_names(
            external_drugs,
            threshold=0.8
        )
        
        print("\nDrug name harmonization results:")
        for _, row in drug_mapping.iterrows():
            original = row['original_name']
            harmonized = row['harmonized_name']
            confidence = row['match_confidence']
            
            if pd.notna(harmonized):
                print(f"  ✓ {original:15} → {harmonized:15} ({confidence:.3f})")
            else:
                print(f"  ✗ {original:15} → No match found")
                
    except DROMAError as e:
        print(f"✗ Error in batch harmonization: {e}")
    
    print()
    
    # =====================================================================
    # 7. Batch Data Export
    # =====================================================================
    print("7. Batch Data Export")
    print("-" * 40)
    
    export_dir = Path("batch_export")
    export_dir.mkdir(exist_ok=True)
    
    print(f"Exporting data to {export_dir}/...")
    
    try:
        # Export all annotations
        sample_anno = droma.get_droma_annotation("sample", project_name="test_project")
        drug_anno = droma.get_droma_annotation("drug")
        
        if not sample_anno.empty:
            sample_file = export_dir / "sample_annotations.csv"
            sample_anno.to_csv(sample_file, index=False)
            print(f"✓ Sample annotations: {sample_file} ({len(sample_anno)} rows)")
        
        if not drug_anno.empty:
            drug_file = export_dir / "drug_annotations.csv"
            drug_anno.to_csv(drug_file, index=False)
            print(f"✓ Drug annotations: {drug_file} ({len(drug_anno)} rows)")
        
        # Export feature lists for each data type
        for table_name in batch_datasets.keys():
            data_type = table_name.split('_')[-1]
            
            features = droma.list_droma_features("test_project", data_type)
            if not features.empty:
                feature_file = export_dir / f"{data_type}_features.csv"
                features.to_csv(feature_file, index=False)
                print(f"✓ {data_type} features: {feature_file} ({len(features)} features)")
        
        # Export project summary
        projects = droma.list_droma_projects()
        if not projects.empty:
            project_file = export_dir / "projects_summary.csv"
            projects.to_csv(project_file, index=False)
            print(f"✓ Project summary: {project_file}")
            
    except DROMAError as e:
        print(f"✗ Error in batch export: {e}")
    
    print()
    
    # =====================================================================
    # 8. Performance Monitoring
    # =====================================================================
    print("8. Performance Monitoring")
    print("-" * 40)
    
    print("Database performance metrics:")
    
    try:
        with droma.DROMADatabase(db_path) as db:
            # Get database size information
            tables = db.list_tables()
            print(f"  Total tables: {len(tables)}")
            
            # Count total rows across all tables
            total_rows = 0
            for table in tables[:10]:  # Sample first 10 tables
                try:
                    result = db.fetchone(f"SELECT COUNT(*) as count FROM `{table}`")
                    if result:
                        total_rows += result['count']
                except:
                    pass  # Skip tables that might have issues
            
            print(f"  Sample row count (first 10 tables): {total_rows:,}")
            
            # Measure query performance
            start_time = time.time()
            projects = droma.list_droma_projects()
            query_time = time.time() - start_time
            print(f"  Project query time: {query_time:.3f} seconds")
            
            # Test batch retrieval performance
            if not projects.empty:
                project_name = projects.iloc[0]['project_name']
                
                start_time = time.time()
                samples = droma.list_droma_samples(project_name, limit=100)
                sample_query_time = time.time() - start_time
                print(f"  Sample query time (100 rows): {sample_query_time:.3f} seconds")
                
    except DROMAError as e:
        print(f"✗ Error in performance monitoring: {e}")
    
    print()
    
    # =====================================================================
    # 9. Cleanup and Summary
    # =====================================================================
    print("9. Cleanup and Summary")
    print("-" * 40)
    
    # Batch processing summary
    print("Batch processing completed!")
    print(f"  Datasets processed: {len(batch_datasets)}")
    print(f"  Successful updates: {successful_updates}")
    print(f"  Valid tables: {valid_tables}")
    print(f"  Export files created: {len(list(export_dir.glob('*.csv')))}")
    
    # Optional: Clean up test data (uncomment if desired)
    print("\nNote: Test tables remain in database for inspection")
    print("To remove test data, manually delete tables starting with 'test_project_'")
    
    # Close database connection
    try:
        droma.close_droma_database()
        print("\n✓ Database connection closed")
    except DROMAError as e:
        print(f"Warning: Error during cleanup: {e}")
    
    print("\n=== Batch processing example completed! ===")

if __name__ == "__main__":
    main() 