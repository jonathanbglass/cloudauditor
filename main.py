import argparse
import logging
import json
import sys
from datetime import datetime

from resource_discovery.discovery_engine import ResourceDiscoveryEngine
from resource_discovery.models import DiscoveryConfig
from reporting.excel_generator import ExcelGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CloudAuditor-CLI")

def main():
    parser = argparse.ArgumentParser(description="CloudAuditor - AWS Resource Discovery & Reporting")
    
    # Discovery args
    parser.add_argument("--accounts", nargs="+", help="AWS Account IDs to scan")
    parser.add_argument("--regions", nargs="+", help="AWS Regions to scan (defaults to all enabled)")
    parser.add_argument("--include", nargs="+", help="Resource types to include (e.g. ec2:instance)")
    parser.add_argument("--exclude", nargs="+", help="Resource types to exclude")
    
    # Storage/Output args
    parser.add_argument("--format", choices=["json", "excel", "both"], default="excel", help="Output format")
    parser.add_argument("--output-dir", default="reports", help="Directory for reports")
    parser.add_argument("--filename", help="Custom filename for the report")
    
    args = parser.parse_args()
    
    # 1. Setup Configuration
    config = DiscoveryConfig(
        accounts=args.accounts,
        regions=args.regions,
        include_types=args.include,
        exclude_types=args.exclude or []
    )
    
    # 2. Run Discovery
    logger.info("Initializing Discovery Engine...")
    engine = ResourceDiscoveryEngine(config=config)
    
    logger.info("Starting Resource Discovery (this may take a few minutes)...")
    result = engine.discover_all_resources()
    
    if not result.success:
        logger.error(f"Discovery finished with errors: {result.errors}")
    
    logger.info(f"Discovered {result.total_count} resources across {len(args.accounts or ['local'])} accounts.")
    
    # 3. Generate Reports
    if args.format in ["json", "both"]:
        json_path = f"{args.output_dir}/{args.filename or 'discovery'}.json"
        with open(json_path, 'w') as f:
            json.dump([r.to_dict() for r in result.resources], f, indent=2, default=str)
        logger.info(f"JSON report saved to {json_path}")
        
    if args.format in ["excel", "both"]:
        logger.info("Generating Excel Report...")
        generator = ExcelGenerator(output_dir=args.output_dir)
        report_path = generator.generate_report(result, filename=args.filename)
        if report_path:
            logger.info(f"Excel report generated: {report_path}")
        else:
            logger.warning("Excel report generation skipped (no data).")

if __name__ == "__main__":
    main()
