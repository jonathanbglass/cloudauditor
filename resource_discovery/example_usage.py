"""
Example usage of the Resource Discovery Engine
"""
import logging
from resource_discovery import ResourceDiscoveryEngine, DiscoveryConfig

# Configure logging
logging.basicConfig(level=logging.INFO)

# Example 1: Simple discovery with defaults
print("Example 1: Simple Discovery")
engine = ResourceDiscoveryEngine()
result = engine.discover_all_resources()
print(f"Found {result.total_count} resources")

# Example 2: Discovery with custom configuration
print("\nExample 2: Custom Configuration")
config = DiscoveryConfig(
    use_resource_explorer=True,
    use_config=True,
    use_cloud_control=False,
    include_types=['AWS::EC2::Instance', 'AWS::S3::Bucket'],
    regions=['us-east-1', 'us-west-2']
)
engine = ResourceDiscoveryEngine(config=config)
result = engine.discover_all_resources()

# Get summary by resource type
summary = engine.get_resource_summary(result)
for resource_type, count in summary.items():
    print(f"{resource_type}: {count}")

# Example 3: Access individual resources
print("\nExample 3: Individual Resources")
for resource in result.resources[:5]:  # First 5 resources
    print(f"  {resource.resource_type}: {resource.name or resource.arn}")
    print(f"    Region: {resource.region}")
    print(f"    Tags: {resource.tags}")
    print(f"    Source: {resource.source.value}")
    print()
