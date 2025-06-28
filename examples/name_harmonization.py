#!/usr/bin/env python3
"""
Name Harmonization Example for DROMA-Py

This example demonstrates how to use DROMA-Py's name harmonization features
to match sample and drug names against the database using fuzzy matching.
"""

import os
import pandas as pd
import droma_py as droma
from droma_py.exceptions import DROMAError

def main():
    """Demonstrate name harmonization functionality."""
    
    # Example database path (adjust to your actual database location)
    db_path = "path/to/your/droma.sqlite"
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Please adjust the db_path variable to point to your DROMA database")
        return
    
    print("=== DROMA-Py Name Harmonization Example ===\n")
    
    # Connect to database
    try:
        droma.connect_droma_database(db_path)
        print(f"✓ Connected to database: {db_path}\n")
    except DROMAError as e:
        print(f"✗ Connection failed: {e}")
        return
    
    # =====================================================================
    # 1. Sample Name Harmonization
    # =====================================================================
    print("1. Sample Name Harmonization")
    print("-" * 40)
    
    # Example sample names with variations and potential typos
    sample_names = [
        "MCF7",           # Exact match expected
        "mcf-7",          # Case and format variation
        "MCF 7",          # Space variation
        "HeLa",           # Another exact match
        "hela cells",     # Case and additional text
        "A549",           # Lung cancer cell line
        "A-549",          # Format variation
        "Unknown_Cell",   # Non-existent sample
        "PC3",            # Prostate cancer cell line
        "pc-3",           # Case variation
        "DU145",          # Another prostate line
        "MDA-MB-231",     # Breast cancer cell line
        "MDAMB231",       # Format variation
        "T47D",           # Breast cancer cell line
        "misspelled_sample"  # Intentional misspelling
    ]
    
    print("Input sample names:")
    for name in sample_names:
        print(f"  - {name}")
    print()
    
    try:
        # Perform sample name harmonization
        sample_mapping = droma.check_droma_sample_names(
            sample_names,
            threshold=0.8,  # 80% similarity threshold
            limit=3         # Max 3 matches per input
        )
        
        print("Sample harmonization results:")
        print("=" * 80)
        
        # Display results in a user-friendly format
        for _, row in sample_mapping.iterrows():
            original = row['original_name']
            harmonized = row['harmonized_name']
            confidence = row['match_confidence']
            
            if pd.notna(harmonized):
                status = "✓ MATCHED" if confidence >= 0.9 else "~ FUZZY"
                print(f"{status:10} | {original:15} → {harmonized:15} | {confidence:.3f}")
            else:
                print(f"✗ NO MATCH | {original:15} → {'Not found':15} | 0.000")
        
        print("\nSummary:")
        matched = sample_mapping['harmonized_name'].notna().sum()
        total = len(sample_mapping)
        print(f"  Matched: {matched}/{total} ({matched/total*100:.1f}%)")
        
        # Show high-confidence matches
        high_conf = sample_mapping[sample_mapping['match_confidence'] >= 0.9]
        if not high_conf.empty:
            print(f"  High confidence (≥90%): {len(high_conf)}")
        
    except DROMAError as e:
        print(f"✗ Error in sample harmonization: {e}")
    
    print("\n")
    
    # =====================================================================
    # 2. Drug Name Harmonization
    # =====================================================================
    print("2. Drug Name Harmonization")
    print("-" * 40)
    
    # Example drug names with variations and potential typos
    drug_names = [
        "Tamoxifen",         # Exact match expected
        "tamoxifen",         # Case variation
        "Cisplatin",         # Chemotherapy drug
        "cis-platin",        # Format variation
        "Doxorubicin",       # Anthracycline
        "doxorubicin HCl",   # With salt form
        "Paclitaxel",        # Taxane
        "5-Fluorouracil",    # Antimetabolite
        "5-FU",              # Common abbreviation
        "Imatinib",          # Tyrosine kinase inhibitor
        "imatinib mesylate", # With salt form
        "Gefitinib",         # EGFR inhibitor
        "Unknown_Drug",      # Non-existent drug
        "Carboplatin",       # Platinum-based
        "carboplatin",       # Case variation
        "misspeled_drug"     # Intentional misspelling
    ]
    
    print("Input drug names:")
    for name in drug_names:
        print(f"  - {name}")
    print()
    
    try:
        # Perform drug name harmonization
        drug_mapping = droma.check_droma_drug_names(
            drug_names,
            threshold=0.8,    # 80% similarity threshold
            limit=3,          # Max 3 matches per input
            ignore_salts=True # Ignore salt forms for matching
        )
        
        print("Drug harmonization results:")
        print("=" * 80)
        
        # Display results in a user-friendly format
        for _, row in drug_mapping.iterrows():
            original = row['original_name']
            harmonized = row['harmonized_name']
            confidence = row['match_confidence']
            
            if pd.notna(harmonized):
                status = "✓ MATCHED" if confidence >= 0.9 else "~ FUZZY"
                print(f"{status:10} | {original:20} → {harmonized:20} | {confidence:.3f}")
            else:
                print(f"✗ NO MATCH | {original:20} → {'Not found':20} | 0.000")
        
        print("\nSummary:")
        matched = drug_mapping['harmonized_name'].notna().sum()
        total = len(drug_mapping)
        print(f"  Matched: {matched}/{total} ({matched/total*100:.1f}%)")
        
        # Show high-confidence matches
        high_conf = drug_mapping[drug_mapping['match_confidence'] >= 0.9]
        if not high_conf.empty:
            print(f"  High confidence (≥90%): {len(high_conf)}")
            
    except DROMAError as e:
        print(f"✗ Error in drug harmonization: {e}")
    
    print("\n")
    
    # =====================================================================
    # 3. Practical Usage - Data Integration
    # =====================================================================
    print("3. Practical Usage - Data Integration")
    print("-" * 40)
    
    # Simulate external dataset that needs name harmonization
    external_data = pd.DataFrame({
        'sample_name': ['MCF7', 'hela cells', 'A-549', 'Unknown_Cell'],
        'drug_name': ['tamoxifen', 'Cisplatin', '5-FU', 'Unknown_Drug'],
        'response_value': [0.85, 0.62, 0.73, 0.91]
    })
    
    print("External dataset (before harmonization):")
    print(external_data)
    print()
    
    try:
        # Harmonize sample names
        sample_map = droma.check_droma_sample_names(
            external_data['sample_name'].tolist(),
            threshold=0.8
        )
        
        # Harmonize drug names
        drug_map = droma.check_droma_drug_names(
            external_data['drug_name'].tolist(),
            threshold=0.8
        )
        
        # Create mapping dictionaries
        sample_dict = dict(zip(sample_map['original_name'], 
                              sample_map['harmonized_name']))
        drug_dict = dict(zip(drug_map['original_name'], 
                            drug_map['harmonized_name']))
        
        # Apply harmonization to external data
        external_data['harmonized_sample'] = external_data['sample_name'].map(sample_dict)
        external_data['harmonized_drug'] = external_data['drug_name'].map(drug_dict)
        
        print("External dataset (after harmonization):")
        print(external_data[['sample_name', 'harmonized_sample', 
                            'drug_name', 'harmonized_drug', 'response_value']])
        print()
        
        # Count successful harmonizations
        sample_success = external_data['harmonized_sample'].notna().sum()
        drug_success = external_data['harmonized_drug'].notna().sum()
        
        print("Integration summary:")
        print(f"  Sample names harmonized: {sample_success}/{len(external_data)}")
        print(f"  Drug names harmonized: {drug_success}/{len(external_data)}")
        
        # Identify rows ready for analysis
        ready_for_analysis = external_data.dropna(subset=['harmonized_sample', 'harmonized_drug'])
        print(f"  Rows ready for analysis: {len(ready_for_analysis)}/{len(external_data)}")
        
    except DROMAError as e:
        print(f"✗ Error in data integration: {e}")
    
    print("\n")
    
    # =====================================================================
    # 4. Advanced Harmonization Options
    # =====================================================================
    print("4. Advanced Harmonization Options")
    print("-" * 40)
    
    try:
        # Example of different threshold effects
        test_names = ["mcf-7", "A 549", "misspelled_cell"]
        
        print("Testing different similarity thresholds:")
        for threshold in [0.6, 0.8, 0.9]:
            mapping = droma.check_droma_sample_names(
                test_names, 
                threshold=threshold,
                limit=1
            )
            matched = mapping['harmonized_name'].notna().sum()
            print(f"  Threshold {threshold}: {matched}/{len(test_names)} matches")
        
        print()
        
        # Example of limiting results
        print("Effect of result limit:")
        mapping_limit1 = droma.check_droma_sample_names(["MCF"], limit=1)
        mapping_limit3 = droma.check_droma_sample_names(["MCF"], limit=3)
        
        print(f"  Limit 1: {len(mapping_limit1)} results")
        print(f"  Limit 3: {len(mapping_limit3)} results")
        
    except DROMAError as e:
        print(f"✗ Error in advanced harmonization: {e}")
    
    # =====================================================================
    # 5. Cleanup
    # =====================================================================
    print("\n5. Cleanup")
    print("-" * 20)
    
    try:
        droma.close_droma_database()
        print("✓ Database connection closed")
    except DROMAError as e:
        print(f"Warning: Error during cleanup: {e}")
    
    print("\n=== Name harmonization example completed! ===")

if __name__ == "__main__":
    main() 