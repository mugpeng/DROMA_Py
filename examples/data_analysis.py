#!/usr/bin/env python3
"""
Data Analysis Example for DROMA-Py

This example demonstrates comprehensive data analysis workflows using DROMA-Py,
including multi-omics data retrieval, integration, and basic analysis tasks.
"""

import os
import pandas as pd
import numpy as np
import droma_py as droma
from droma_py.exceptions import DROMAError
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    """Demonstrate data analysis workflows with DROMA-Py."""
    
    # Example database path (adjust to your actual database location)
    db_path = "path/to/your/droma.sqlite"
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Please adjust the db_path variable to point to your DROMA database")
        return
    
    print("=== DROMA-Py Data Analysis Example ===\n")
    
    # Connect to database
    try:
        droma.connect_droma_database(db_path)
        print(f"✓ Connected to database: {db_path}\n")
    except DROMAError as e:
        print(f"✗ Connection failed: {e}")
        return
    
    # =====================================================================
    # 1. Project Overview and Selection
    # =====================================================================
    print("1. Project Overview and Selection")
    print("-" * 40)
    
    try:
        # Get comprehensive project information
        projects = droma.list_droma_projects()
        
        if projects.empty:
            print("No projects found in database")
            return
            
        print(f"Available projects ({len(projects)}):")
        print(projects[['project_name', 'dataset_type', 'tumor_type', 'total_samples']].head())
        
        # Select a project for analysis
        example_project = projects.iloc[0]['project_name']
        project_info = projects.iloc[0]
        
        print(f"\nSelected project for analysis: {example_project}")
        print(f"  Dataset type: {project_info['dataset_type']}")
        print(f"  Tumor type: {project_info['tumor_type']}")
        print(f"  Total samples: {project_info['total_samples']}")
        
    except DROMAError as e:
        print(f"✗ Error getting project overview: {e}")
        return
    
    print()
    
    # =====================================================================
    # 2. Data Availability Assessment
    # =====================================================================
    print("2. Data Availability Assessment")
    print("-" * 40)
    
    data_types = ['mRNA', 'cnv', 'drug', 'mutation_gene', 'proteinrppa']
    data_summary = {}
    
    for data_type in data_types:
        try:
            features = droma.list_droma_features(example_project, data_type, limit=1)
            samples = droma.list_droma_samples(example_project, data_type=data_type, limit=1)
            
            data_summary[data_type] = {
                'available': not features.empty,
                'feature_count': len(features) if not features.empty else 0,
                'sample_count': len(samples) if not samples.empty else 0
            }
            
            if data_summary[data_type]['available']:
                print(f"✓ {data_type:12} | Features: {data_summary[data_type]['feature_count']:5} | Samples: {data_summary[data_type]['sample_count']:5}")
            else:
                print(f"✗ {data_type:12} | Not available")
                
        except DROMAError:
            data_summary[data_type] = {'available': False, 'feature_count': 0, 'sample_count': 0}
            print(f"✗ {data_type:12} | Error accessing data")
    
    print()
    
    # =====================================================================
    # 3. Sample Annotation Analysis
    # =====================================================================
    print("3. Sample Annotation Analysis")
    print("-" * 40)
    
    try:
        # Get sample annotations
        sample_anno = droma.get_droma_annotation(
            "sample", 
            project_name=example_project,
            limit=1000
        )
        
        if not sample_anno.empty:
            print(f"Total samples with annotations: {len(sample_anno)}")
            
            # Analyze data type distribution
            if 'data_type' in sample_anno.columns:
                data_type_counts = sample_anno['data_type'].value_counts()
                print("\nData type distribution:")
                for dtype, count in data_type_counts.items():
                    print(f"  {dtype}: {count}")
            
            # Analyze tumor type distribution
            if 'tumor_type' in sample_anno.columns:
                tumor_type_counts = sample_anno['tumor_type'].value_counts()
                print(f"\nTumor type distribution (top 5):")
                for ttype, count in tumor_type_counts.head().items():
                    print(f"  {ttype}: {count}")
            
            # Show annotation columns
            print(f"\nAvailable annotation columns ({len(sample_anno.columns)}):")
            for col in sample_anno.columns[:10]:  # Show first 10 columns
                print(f"  - {col}")
            if len(sample_anno.columns) > 10:
                print(f"  ... and {len(sample_anno.columns) - 10} more")
        else:
            print("No sample annotations found")
            
    except DROMAError as e:
        print(f"✗ Error analyzing sample annotations: {e}")
    
    print()
    
    # =====================================================================
    # 4. Gene Expression Analysis
    # =====================================================================
    print("4. Gene Expression Analysis")
    print("-" * 40)
    
    if data_summary['mRNA']['available']:
        try:
            # Get some cancer-related genes
            cancer_genes = ['TP53', 'BRCA1', 'BRCA2', 'EGFR', 'MYC']
            
            print(f"Analyzing expression of cancer genes: {cancer_genes}")
            
            expression_data = {}
            for gene in cancer_genes:
                try:
                    gene_data = droma.get_feature_from_database(
                        "mRNA", gene,
                        data_sources=[example_project],
                        limit=100
                    )
                    
                    if gene_data and example_project in gene_data:
                        expression_data[gene] = gene_data[example_project]
                        print(f"✓ {gene}: {len(gene_data[example_project])} samples")
                    else:
                        print(f"✗ {gene}: No data found")
                        
                except DROMAError:
                    print(f"✗ {gene}: Error retrieving data")
            
            # Combine expression data
            if expression_data:
                expr_df = pd.DataFrame(expression_data)
                print(f"\nExpression matrix shape: {expr_df.shape}")
                print("Expression summary statistics:")
                print(expr_df.describe())
                
                # Calculate correlation matrix
                if len(expr_df.columns) > 1:
                    corr_matrix = expr_df.corr()
                    print("\nGene expression correlations:")
                    print(corr_matrix.round(3))
                    
                    # Find highly correlated gene pairs
                    high_corr_pairs = []
                    for i in range(len(corr_matrix.columns)):
                        for j in range(i+1, len(corr_matrix.columns)):
                            corr_val = corr_matrix.iloc[i, j]
                            if abs(corr_val) > 0.5:  # Threshold for high correlation
                                gene1 = corr_matrix.columns[i]
                                gene2 = corr_matrix.columns[j]
                                high_corr_pairs.append((gene1, gene2, corr_val))
                    
                    if high_corr_pairs:
                        print("\nHighly correlated gene pairs (|r| > 0.5):")
                        for gene1, gene2, corr in high_corr_pairs:
                            print(f"  {gene1} - {gene2}: {corr:.3f}")
            else:
                print("No expression data retrieved for analysis")
                
        except DROMAError as e:
            print(f"✗ Error in gene expression analysis: {e}")
    else:
        print("mRNA data not available for this project")
    
    print()
    
    # =====================================================================
    # 5. Drug Response Analysis
    # =====================================================================
    print("5. Drug Response Analysis")
    print("-" * 40)
    
    if data_summary['drug']['available']:
        try:
            # Get drug annotation information
            drug_anno = droma.get_droma_annotation("drug", limit=100)
            
            if not drug_anno.empty:
                print(f"Drug annotations available: {len(drug_anno)}")
                
                # Analyze mechanism of action distribution
                if 'moa' in drug_anno.columns:
                    moa_counts = drug_anno['moa'].value_counts()
                    print(f"\nTop 5 mechanisms of action:")
                    for moa, count in moa_counts.head().items():
                        print(f"  {moa}: {count}")
                
                # Select some drugs for analysis
                example_drugs = drug_anno['drug_name'].head(3).tolist()
                print(f"\nAnalyzing drug response for: {example_drugs}")
                
                drug_response_data = {}
                for drug in example_drugs:
                    try:
                        drug_data = droma.get_feature_from_database(
                            "drug", drug,
                            data_sources=[example_project],
                            limit=100
                        )
                        
                        if drug_data and example_project in drug_data:
                            drug_response_data[drug] = drug_data[example_project]
                            response_values = list(drug_data[example_project].values())
                            mean_response = np.mean(response_values)
                            print(f"✓ {drug}: {len(response_values)} samples, mean response: {mean_response:.3f}")
                        else:
                            print(f"✗ {drug}: No data found")
                            
                    except DROMAError:
                        print(f"✗ {drug}: Error retrieving data")
                
                # Analyze drug response distribution
                if drug_response_data:
                    drug_df = pd.DataFrame(drug_response_data)
                    print(f"\nDrug response matrix shape: {drug_df.shape}")
                    print("Drug response summary statistics:")
                    print(drug_df.describe())
            else:
                print("No drug annotations found")
                
        except DROMAError as e:
            print(f"✗ Error in drug response analysis: {e}")
    else:
        print("Drug response data not available for this project")
    
    print()
    
    # =====================================================================
    # 6. Multi-Omics Integration Example
    # =====================================================================
    print("6. Multi-Omics Integration Example")
    print("-" * 40)
    
    try:
        # Get common samples across data types
        common_samples = None
        available_data = {}
        
        for data_type in ['mRNA', 'cnv', 'drug']:
            if data_summary[data_type]['available']:
                samples = droma.list_droma_samples(
                    example_project, 
                    data_type=data_type,
                    limit=50
                )
                
                if not samples.empty:
                    sample_ids = set(samples['sample_id'])
                    available_data[data_type] = sample_ids
                    
                    if common_samples is None:
                        common_samples = sample_ids
                    else:
                        common_samples = common_samples.intersection(sample_ids)
        
        if common_samples and len(common_samples) > 0:
            print(f"Common samples across data types: {len(common_samples)}")
            
            # Show data type availability
            print("Data type availability:")
            for data_type, samples in available_data.items():
                print(f"  {data_type}: {len(samples)} samples")
            
            # Example: Get TP53 expression and copy number for common samples
            if 'mRNA' in available_data and 'cnv' in available_data:
                try:
                    tp53_expr = droma.get_feature_from_database(
                        "mRNA", "TP53",
                        data_sources=[example_project]
                    )
                    
                    tp53_cnv = droma.get_feature_from_database(
                        "cnv", "TP53",
                        data_sources=[example_project]
                    )
                    
                    if (tp53_expr and example_project in tp53_expr and 
                        tp53_cnv and example_project in tp53_cnv):
                        
                        expr_samples = set(tp53_expr[example_project].keys())
                        cnv_samples = set(tp53_cnv[example_project].keys())
                        overlap_samples = expr_samples.intersection(cnv_samples)
                        
                        if overlap_samples:
                            print(f"\nTP53 multi-omics analysis:")
                            print(f"  Expression samples: {len(expr_samples)}")
                            print(f"  CNV samples: {len(cnv_samples)}")
                            print(f"  Overlapping samples: {len(overlap_samples)}")
                            
                            # Calculate correlation between expression and CNV
                            expr_values = [tp53_expr[example_project][s] for s in overlap_samples]
                            cnv_values = [tp53_cnv[example_project][s] for s in overlap_samples]
                            
                            correlation = np.corrcoef(expr_values, cnv_values)[0, 1]
                            print(f"  Expression-CNV correlation: {correlation:.3f}")
                
                except DROMAError as e:
                    print(f"Error in TP53 multi-omics analysis: {e}")
        else:
            print("No common samples found across data types")
            
    except DROMAError as e:
        print(f"✗ Error in multi-omics integration: {e}")
    
    print()
    
    # =====================================================================
    # 7. Data Export for Further Analysis
    # =====================================================================
    print("7. Data Export for Further Analysis")
    print("-" * 40)
    
    try:
        # Export sample annotations
        sample_anno = droma.get_droma_annotation(
            "sample", 
            project_name=example_project,
            limit=100
        )
        
        if not sample_anno.empty:
            output_file = f"{example_project}_sample_annotations.csv"
            sample_anno.to_csv(output_file, index=False)
            print(f"✓ Sample annotations exported to: {output_file}")
        
        # Export drug annotations
        drug_anno = droma.get_droma_annotation("drug", limit=100)
        if not drug_anno.empty:
            output_file = f"{example_project}_drug_annotations.csv"
            drug_anno.to_csv(output_file, index=False)
            print(f"✓ Drug annotations exported to: {output_file}")
        
        print("\nFiles ready for external analysis tools (R, Python notebooks, etc.)")
        
    except DROMAError as e:
        print(f"✗ Error exporting data: {e}")
    
    print()
    
    # =====================================================================
    # 8. Summary Report
    # =====================================================================
    print("8. Analysis Summary Report")
    print("-" * 40)
    
    print(f"Project analyzed: {example_project}")
    print(f"Data types available: {sum(1 for dt in data_summary.values() if dt['available'])}/{len(data_summary)}")
    
    total_features = sum(dt['feature_count'] for dt in data_summary.values())
    total_samples = sum(dt['sample_count'] for dt in data_summary.values())
    
    print(f"Total features across all data types: {total_features}")
    print(f"Total sample-data type combinations: {total_samples}")
    
    print("\nRecommended next steps:")
    print("1. Perform differential expression analysis")
    print("2. Conduct drug sensitivity prediction")
    print("3. Integrate multi-omics data for pathway analysis")
    print("4. Apply machine learning for biomarker discovery")
    
    # =====================================================================
    # 9. Cleanup
    # =====================================================================
    print("\n9. Cleanup")
    print("-" * 20)
    
    try:
        droma.close_droma_database()
        print("✓ Database connection closed")
    except DROMAError as e:
        print(f"Warning: Error during cleanup: {e}")
    
    print("\n=== Data analysis example completed! ===")

if __name__ == "__main__":
    main() 