"""
Lambda handler for resource discovery
Triggered by CloudWatch Events (scheduled)
"""
import json
import logging
import os
from typing import Dict, Any

from resource_discovery import ResourceDiscoveryEngine, DiscoveryConfig

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for scheduled resource discovery.
    
    Args:
        event: CloudWatch Events event
        context: Lambda context
        
    Returns:
        Response with discovery results
    """
    logger.info("Starting resource discovery")
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        # Configure discovery
        config = DiscoveryConfig(
            use_resource_explorer=True,
            use_config=True,
            use_cloud_control=False,  # Disabled by default for performance
            max_workers=10
        )
        
        # Run discovery
        engine = ResourceDiscoveryEngine(config=config)
        result = engine.discover_all_resources()
        
        # Log summary
        logger.info(f"Discovery complete: {result.total_count} resources in {result.duration_seconds:.2f}s")
        
        if result.errors:
            logger.warning(f"Errors encountered: {result.errors}")
        
        # Get summary by type
        summary = engine.get_resource_summary(result)
        logger.info(f"Resource types discovered: {len(summary)}")
        
        # TODO: Store results in database
        # For now, just log the summary
        for resource_type, count in list(summary.items())[:10]:  # Top 10
            logger.info(f"  {resource_type}: {count}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': result.success,
                'total_resources': result.total_count,
                'duration_seconds': result.duration_seconds,
                'resource_types': len(summary),
                'errors': result.errors
            })
        }
        
    except Exception as e:
        logger.exception("Resource discovery failed")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
