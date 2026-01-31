"""
AWS Resource Discovery Package
Intelligent resource discovery using Resource Explorer, Config, and Cloud Control API
"""

__version__ = "0.1.0"
__author__ = "CloudAuditor Team"

from .discovery_engine import ResourceDiscoveryEngine
from .models import Resource, DiscoveryConfig

__all__ = [
    'ResourceDiscoveryEngine',
    'Resource',
    'DiscoveryConfig',
]
