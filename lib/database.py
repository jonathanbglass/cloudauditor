import logging
import json
import os
import boto3
import psycopg
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseClient:
    """
    Shared client for interacting with the CloudAuditor database.
    """
    
    def __init__(self):
        self._conn = None
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from environment and Secrets Manager."""
        config = {
            'host': os.environ.get('DB_HOST'),
            'dbname': os.environ.get('DB_NAME'),
            'user': os.environ.get('DB_USER'),
            'port': int(os.environ.get('DB_PORT', 5432)),
            'secret_arn': os.environ.get('DB_SECRET_ARN')
        }
        
        # If secret_arn is provided, get password from Secrets Manager
        if config['secret_arn']:
            try:
                sts = boto3.client('sts') # Use default session
                client = boto3.client('secretsmanager')
                response = client.get_secret_value(SecretId=config['secret_arn'])
                secret = json.loads(response['SecretString'])
                config['password'] = secret.get('password')
                config['user'] = secret.get('username') or config['user']
            except Exception as e:
                logger.error(f"Failed to fetch database secret: {e}")
                
        return config

    def _get_connection(self):
        """Get or create database connection."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(
                host=self._config['host'],
                port=self._config['port'],
                dbname=self._config['dbname'],
                user=self._config['user'],
                password=self._config['password'],
                autocommit=True
            )
        return self._conn

    def get_monitored_accounts(self) -> List[Dict[str, Any]]:
        """Fetch all active monitored accounts."""
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT account_id, role_arn, status FROM monitored_accounts WHERE status != 'disabled'")
            rows = cur.fetchall()
            return [{'account_id': r[0], 'role_arn': r[1], 'status': r[2]} for r in rows]

    def register_account(self, account_id: str, role_arn: str, account_name: Optional[str] = None):
        """Insert or update a monitored account."""
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO monitored_accounts (account_id, account_name, role_arn, status)
                VALUES (%s, %s, %s, 'pending')
                ON CONFLICT (account_id) DO UPDATE 
                SET role_arn = EXCLUDED.role_arn, status = 'pending'
            """, (account_id, account_name, role_arn))

    def update_account_status(self, account_id: str, status: str, last_error: Optional[str] = None):
        """Update account status and last verification time."""
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE monitored_accounts 
                SET status = %s, last_error_message = %s, last_verification_at = NOW()
                WHERE account_id = %s
            """, (status, last_error, account_id))

    def save_resources(self, resources: List[Dict[str, Any]]):
        """Batch upsert discovered resources."""
        conn = self._get_connection()
        with conn.cursor() as cur:
            for r in resources:
                cur.execute("""
                    INSERT INTO resources (
                        resource_id, resource_type, resource_arn, region, account_id, name, tags, properties
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (resource_id, resource_type, region, account_id) DO UPDATE SET
                        resource_arn = EXCLUDED.resource_arn,
                        name = EXCLUDED.name,
                        tags = EXCLUDED.tags,
                        properties = EXCLUDED.properties,
                        last_seen_at = NOW()
                """, (
                    r.get('id') or r.get('arn'), r['resource_type'], r.get('arn'), 
                    r['region'], r['account_id'], r.get('name'), 
                    json.dumps(r.get('tags', {})), json.dumps(r.get('properties', {}))
                ))
