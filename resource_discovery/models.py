"""
Data models for resource discovery
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class DiscoverySource(Enum):
    """Source of resource discovery"""
    RESOURCE_EXPLORER = "resource_explorer"
    CONFIG = "config"
    CLOUD_CONTROL = "cloud_control"


@dataclass
class Resource:
    """Standardized AWS resource representation"""
    arn: str
    resource_type: str
    region: str
    account_id: str
    name: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)
    relationships: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    source: DiscoverySource = DiscoverySource.RESOURCE_EXPLORER
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion"""
        return {
            'arn': self.arn,
            'resource_type': self.resource_type,
            'region': self.region,
            'account_id': self.account_id,
            'name': self.name,
            'tags': self.tags,
            'configuration': self.configuration,
            'relationships': self.relationships,
            'created_at': self.created_at,
            'last_modified': self.last_modified,
            'discovery_source': self.source.value
        }


@dataclass
class DiscoveryConfig:
    """Configuration for resource discovery"""
    # Which discovery methods to use
    use_resource_explorer: bool = True
    use_config: bool = True
    use_cloud_control: bool = False  # Fallback only
    
    # Resource type filters
    include_types: Optional[List[str]] = None  # None = all types
    exclude_types: List[str] = field(default_factory=list)
    
    # Region configuration
    regions: Optional[List[str]] = None  # None = all regions
    
    # Account configuration
    accounts: Optional[List[str]] = None  # None = only local account
    
    # Performance tuning
    batch_size: int = 100
    max_workers: int = 10
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: int = 2
    
    def should_include_type(self, resource_type: str) -> bool:
        """Check if resource type should be included"""
        if resource_type in self.exclude_types:
            return False
        if self.include_types is None:
            return True
        return resource_type in self.include_types


@dataclass
class DiscoveryResult:
    """Result of a discovery operation"""
    resources: List[Resource]
    total_count: int
    success: bool
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    
    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
        self.success = False
