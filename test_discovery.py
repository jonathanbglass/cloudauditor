#!/usr/bin/env python3
"""
Test script for resource discovery POC
Run this to test the discovery engine locally

Usage:
    python test_discovery.py                          # Use default credentials
    python test_discovery.py --profile cloudAuditor   # Use specific profile
    AWS_PROFILE=cloudAuditor python test_discovery.py # Use env variable
"""
import argparse
import logging
import sys
import json
import os
from typing import Dict

import boto3

# Add parent directory to path
sys.path.insert(0, '.')

from resource_discovery import ResourceDiscoveryEngine, DiscoveryConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_summary(summary: Dict[str, int]):
    """Print resource summary in a nice format"""
    print("\n" + "="*80)
    print("RESOURCE DISCOVERY SUMMARY")
    print("="*80)
    print(f"{'Resource Type':<50} {'Count':>10}")
    print("-"*80)
    
    total = 0
    for resource_type, count in summary.items():
        print(f"{resource_type:<50} {count:>10}")
        total += count
    
    print("-"*80)
    print(f"{'TOTAL':<50} {total:>10}")
    print("="*80 + "\n")


def test_resource_explorer_only(session=None):
    """Test discovery using only Resource Explorer"""
    print("\n🔍 Testing Resource Explorer Only...")
    
    config = DiscoveryConfig(
        use_resource_explorer=True,
        use_config=False,
        use_cloud_control=False
    )
    
    engine = ResourceDiscoveryEngine(config=config, session=session)
    result = engine.discover_all_resources()
    
    print(f"✅ Found {result.total_count} resources in {result.duration_seconds:.2f}s")
    
    if result.errors:
        print(f"⚠️  Errors: {', '.join(result.errors)}")
    
    summary = engine.get_resource_summary(result)
    print_summary(summary)
    
    return result


def test_config_only(session=None):
    """Test discovery using only AWS Config"""
    print("\n🔍 Testing AWS Config Only...")
    
    config = DiscoveryConfig(
        use_resource_explorer=False,
        use_config=True,
        use_cloud_control=False
    )
    
    engine = ResourceDiscoveryEngine(config=config, session=session)
    result = engine.discover_all_resources()
    
    print(f"✅ Found {result.total_count} resources in {result.duration_seconds:.2f}s")
    
    if result.errors:
        print(f"⚠️  Errors: {', '.join(result.errors)}")
    
    summary = engine.get_resource_summary(result)
    print_summary(summary)
    
    return result


def test_hybrid_approach(session=None):
    """Test discovery using hybrid approach (default)"""
    print("\n🔍 Testing Hybrid Approach (Resource Explorer + Config)...")
    
    config = DiscoveryConfig(
        use_resource_explorer=True,
        use_config=True,
        use_cloud_control=False
    )
    
    engine = ResourceDiscoveryEngine(config=config, session=session)
    result = engine.discover_all_resources()
    
    print(f"✅ Found {result.total_count} resources in {result.duration_seconds:.2f}s")
    
    if result.errors:
        print(f"⚠️  Errors: {', '.join(result.errors)}")
    
    summary = engine.get_resource_summary(result)
    print_summary(summary)
    
    # Show breakdown by source
    sources = {}
    for resource in result.resources:
        source = resource.source.value
        sources[source] = sources.get(source, 0) + 1
    
    print("\nResources by Discovery Source:")
    for source, count in sources.items():
        print(f"  {source}: {count}")
    
    return result


def test_filtered_discovery(session=None):
    """Test discovery with resource type filters"""
    print("\n🔍 Testing Filtered Discovery (EC2 and S3 only)...")
    
    config = DiscoveryConfig(
        use_resource_explorer=True,
        use_config=True,
        use_cloud_control=False,
        include_types=[
            'AWS::EC2::Instance',
            'AWS::EC2::Volume',
            'AWS::EC2::SecurityGroup',
            'AWS::S3::Bucket'
        ]
    )
    
    engine = ResourceDiscoveryEngine(config=config, session=session)
    result = engine.discover_all_resources()
    
    print(f"✅ Found {result.total_count} resources in {result.duration_seconds:.2f}s")
    
    summary = engine.get_resource_summary(result)
    print_summary(summary)
    
    return result


def export_to_json(result, filename='discovered_resources.json'):
    """Export discovered resources to JSON file"""
    print(f"\n💾 Exporting to {filename}...")
    
    data = {
        'total_count': result.total_count,
        'success': result.success,
        'duration_seconds': result.duration_seconds,
        'errors': result.errors,
        'resources': [r.to_dict() for r in result.resources]
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"✅ Exported {result.total_count} resources to {filename}")


def main():
    """Main test function"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Test AWS Resource Discovery Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default credentials
  python test_discovery.py
  
  # Use specific AWS profile
  python test_discovery.py --profile cloudAuditor
  
  # Use environment variable
  AWS_PROFILE=cloudAuditor python test_discovery.py
  
  # Export to custom file
  python test_discovery.py --output my_resources.json
        """
    )
    parser.add_argument(
        '--profile',
        help='AWS profile name to use (overrides AWS_PROFILE env var)',
        default=None
    )
    parser.add_argument(
        '--output',
        help='Output JSON file path',
        default='discovered_resources.json'
    )
    parser.add_argument(
        '--test',
        choices=['hybrid', 'explorer', 'config', 'filtered'],
        default='hybrid',
        help='Which test to run (default: hybrid)'
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("AWS RESOURCE DISCOVERY POC - TEST SUITE")
    print("="*80)
    
    # Create AWS session with profile support
    profile_name = args.profile or os.environ.get('AWS_PROFILE')
    
    try:
        if profile_name:
            print(f"\n🔑 Using AWS profile: {profile_name}")
            session = boto3.Session(profile_name=profile_name)
        else:
            print("\n🔑 Using default AWS credentials")
            session = boto3.Session()
        
        # Verify credentials
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Credentials OK")
        print(f"   Account: {identity['Account']}")
        print(f"   User/Role: {identity['Arn']}")
        print(f"   Region: {session.region_name or 'default'}")
        
    except Exception as e:
        print(f"\n❌ AWS Credentials Error: {e}")
        print("   Please configure AWS credentials and try again.")
        print("\n   Options:")
        print("   1. Use --profile flag: python test_discovery.py --profile myprofile")
        print("   2. Set AWS_PROFILE env var: export AWS_PROFILE=myprofile")
        print("   3. Configure default credentials: aws configure")
        return
    
    # Run tests
    try:
        if args.test == 'hybrid':
            result = test_hybrid_approach(session)
        elif args.test == 'explorer':
            result = test_resource_explorer_only(session)
        elif args.test == 'config':
            result = test_config_only(session)
        elif args.test == 'filtered':
            result = test_filtered_discovery(session)
        
        # Export results
        if result.total_count > 0:
            export_to_json(result, args.output)
        
        print("\n" + "="*80)
        print("✅ POC TEST COMPLETE")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        logger.exception("Test failed")
        print(f"\n❌ Test failed: {e}")


if __name__ == '__main__':
    main()
