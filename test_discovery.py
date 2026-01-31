#!/usr/bin/env python3
"""
Test script for resource discovery POC
Run this to test the discovery engine locally
"""
import logging
import sys
import json
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


def test_resource_explorer_only():
    """Test discovery using only Resource Explorer"""
    print("\n🔍 Testing Resource Explorer Only...")
    
    config = DiscoveryConfig(
        use_resource_explorer=True,
        use_config=False,
        use_cloud_control=False
    )
    
    engine = ResourceDiscoveryEngine(config=config)
    result = engine.discover_all_resources()
    
    print(f"✅ Found {result.total_count} resources in {result.duration_seconds:.2f}s")
    
    if result.errors:
        print(f"⚠️  Errors: {', '.join(result.errors)}")
    
    summary = engine.get_resource_summary(result)
    print_summary(summary)
    
    return result


def test_config_only():
    """Test discovery using only AWS Config"""
    print("\n🔍 Testing AWS Config Only...")
    
    config = DiscoveryConfig(
        use_resource_explorer=False,
        use_config=True,
        use_cloud_control=False
    )
    
    engine = ResourceDiscoveryEngine(config=config)
    result = engine.discover_all_resources()
    
    print(f"✅ Found {result.total_count} resources in {result.duration_seconds:.2f}s")
    
    if result.errors:
        print(f"⚠️  Errors: {', '.join(result.errors)}")
    
    summary = engine.get_resource_summary(result)
    print_summary(summary)
    
    return result


def test_hybrid_approach():
    """Test discovery using hybrid approach (default)"""
    print("\n🔍 Testing Hybrid Approach (Resource Explorer + Config)...")
    
    config = DiscoveryConfig(
        use_resource_explorer=True,
        use_config=True,
        use_cloud_control=False
    )
    
    engine = ResourceDiscoveryEngine(config=config)
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


def test_filtered_discovery():
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
    
    engine = ResourceDiscoveryEngine(config=config)
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
    print("="*80)
    print("AWS RESOURCE DISCOVERY POC - TEST SUITE")
    print("="*80)
    
    # Check AWS credentials
    try:
        session = boto3.Session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"\n✅ AWS Credentials OK")
        print(f"   Account: {identity['Account']}")
        print(f"   User/Role: {identity['Arn']}")
    except Exception as e:
        print(f"\n❌ AWS Credentials Error: {e}")
        print("   Please configure AWS credentials and try again.")
        return
    
    # Run tests
    try:
        # Test 1: Hybrid approach (recommended)
        result = test_hybrid_approach()
        
        # Export results
        if result.total_count > 0:
            export_to_json(result)
        
        # Test 2: Resource Explorer only (if available)
        # test_resource_explorer_only()
        
        # Test 3: Config only (if available)
        # test_config_only()
        
        # Test 4: Filtered discovery
        # test_filtered_discovery()
        
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
