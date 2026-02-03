import logging
import os
from typing import List, Dict, Any
from datetime import datetime

import pandas as pd
from resource_discovery.models import Resource, DiscoveryResult

logger = logging.getLogger(__name__)

class ExcelGenerator:
    """
    Generates high-quality Excel reports from discovery results.
    Creates an Executive Summary and individual tabs for each AWS service.
    """
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
    def generate_report(self, result: DiscoveryResult, filename: str = None) -> str:
        """
        Produce a multi-tab Excel spreadsheet from discovery resources.
        
        Args:
            result: The discovery result containing all resources
            filename: Output filename (defaults to timestamped name)
            
        Returns:
            Path to the generated report
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"CloudAuditor_Report_{timestamp}.xlsx"
            
        output_path = os.path.join(self.output_dir, filename)
        
        # Convert resources to a Flat DataFrame for processing
        data = [r.to_dict() for r in result.resources]
        df = pd.DataFrame(data)
        
        if df.empty:
            logger.warning("No resources found to report.")
            return ""

        # Create the Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            
            # 1. Executive Summary Tab
            summary_stats = self._create_summary_stats(df)
            summary_stats.to_excel(writer, sheet_name='Executive Summary', index=False)
            
            # 2. Per-Service Tabs
            # Group by Service (extracted from resource_type prefix e.g., 'ec2' from 'ec2:instance')
            df['service'] = df['resource_type'].apply(lambda x: x.split(':')[0] if ':' in x else x)
            
            services = sorted(df['service'].unique())
            for service in services:
                service_df = df[df['service'] == service].copy()
                
                # Drop internal helper columns before writing
                cols_to_drop = ['service']
                service_df.drop(columns=cols_to_drop, inplace=True, errors='ignore')
                
                # Sanitize sheet name (Excel limit 31 chars)
                sheet_name = service.upper()[:31]
                service_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Formatting (optional but recommended for 'wow' factor)
                # Note: Minimal formatting for now, can be expanded with openpyxl
                
        logger.info(f"Report generated successfully: {output_path}")
        return output_path

    def _create_summary_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create high-level asset counts for the summary tab."""
        summary = df.groupby(['account_id', 'resource_type']).size().reset_index(name='count')
        
        # Add a grand total row
        total_resources = df.shape[0]
        total_accounts = df['account_id'].nunique()
        
        # Create a nice header for the summary
        header_data = [
            {'account_id': 'REPORT SUMMARY', 'resource_type': 'Total Accounts', 'count': total_accounts},
            {'account_id': 'REPORT SUMMARY', 'resource_type': 'Total Resources', 'count': total_resources},
            {'account_id': '', 'resource_type': '', 'count': None} # Spacer
        ]
        
        header_df = pd.DataFrame(header_data)
        return pd.concat([header_df, summary], ignore_index=True)
