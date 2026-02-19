"""
Database Query Lambda Function
Allows remote querying of the CloudAuditor database via Lambda invocation
"""
import json
import logging
from lib.database import DatabaseClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Query the CloudAuditor database.
    
    Event parameters:
    - report_type: 'summary', 'accounts', 'by_type', 'by_account', 'resources'
    - query: Custom SQL query (optional, use with caution)
    - limit: Result limit for list queries (default: 100)
    """
    try:
        report_type = event.get('report_type', 'summary')
        custom_query = event.get('query')
        limit = event.get('limit', 100)
        
        db = DatabaseClient()
        conn = db._get_connection()
        
        results = {}
        account_ids = event.get('account_ids')
        
        if custom_query:
            # Execute custom query (be careful with this!)
            logger.info(f"Executing custom query: {custom_query}")
            with conn.cursor() as cur:
                cur.execute(custom_query)
                rows = cur.fetchall()
                results = {
                    'query': custom_query,
                    'rows': [list(row) for row in rows],
                    'row_count': len(rows)
                }
        
        elif report_type == 'summary':
            with conn.cursor() as cur:
                # Build account filter
                acct_where = ""
                acct_params = []
                if account_ids:
                    placeholders = ", ".join(["%s"] * len(account_ids))
                    acct_where = f"WHERE account_id IN ({placeholders})"
                    acct_params = list(account_ids)
                    logger.info(f"Summary filtered by {len(account_ids)} accounts")

                # Total resources
                cur.execute(f"SELECT COUNT(*) FROM resources {acct_where}", acct_params or None)
                total_resources = cur.fetchone()[0]
                
                # Unique resource types
                cur.execute(f"SELECT COUNT(DISTINCT resource_type) FROM resources {acct_where}", acct_params or None)
                unique_types = cur.fetchone()[0]
                
                # Unique accounts
                cur.execute(f"SELECT COUNT(DISTINCT account_id) FROM resources {acct_where}", acct_params or None)
                unique_accounts = cur.fetchone()[0]
                
                # Monitored accounts (scoped if account_ids provided)
                if account_ids:
                    cur.execute(f"SELECT COUNT(*) FROM monitored_accounts WHERE account_id IN ({placeholders})", acct_params)
                else:
                    cur.execute("SELECT COUNT(*) FROM monitored_accounts")
                monitored = cur.fetchone()[0]
                
                # Latest scan
                cur.execute(f"SELECT MAX(discovered_at) FROM resources {acct_where}", acct_params or None)
                latest_scan = cur.fetchone()[0]
                
                results = {
                    'total_resources': total_resources,
                    'unique_resource_types': unique_types,
                    'accounts_with_resources': unique_accounts,
                    'monitored_accounts': monitored,
                    'latest_scan': str(latest_scan) if latest_scan else None
                }
        
        elif report_type == 'accounts':
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT account_id, account_name, status, auto_discovered, 
                           last_verification_at, last_error_message
                    FROM monitored_accounts
                    ORDER BY account_id
                """)
                
                accounts = []
                for row in cur.fetchall():
                    accounts.append({
                        'account_id': row[0],
                        'account_name': row[1],
                        'status': row[2],
                        'auto_discovered': row[3],
                        'last_verification_at': str(row[4]) if row[4] else None,
                        'last_error_message': row[5]
                    })
                
                results = {'accounts': accounts, 'count': len(accounts)}
        
        elif report_type == 'by_type':
            with conn.cursor() as cur:
                acct_where = ""
                acct_params = []
                if account_ids:
                    placeholders = ", ".join(["%s"] * len(account_ids))
                    acct_where = f"WHERE account_id IN ({placeholders})"
                    acct_params = list(account_ids)

                cur.execute(f"""
                    SELECT resource_type, COUNT(*) as count
                    FROM resources
                    {acct_where}
                    GROUP BY resource_type
                    ORDER BY count DESC
                    LIMIT %s
                """, acct_params + [limit])
                
                resource_types = []
                for row in cur.fetchall():
                    resource_types.append({
                        'resource_type': row[0],
                        'count': row[1]
                    })
                
                results = {'resource_types': resource_types, 'count': len(resource_types)}
        
        elif report_type == 'by_account':
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT account_id, COUNT(*) as count, COUNT(DISTINCT resource_type) as types
                    FROM resources
                    GROUP BY account_id
                    ORDER BY count DESC
                """)
                
                accounts = []
                for row in cur.fetchall():
                    accounts.append({
                        'account_id': row[0],
                        'resource_count': row[1],
                        'resource_types': row[2]
                    })
                
                results = {'accounts': accounts, 'count': len(accounts)}
        
        elif report_type == 'resources':
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT account_id, region, resource_type, resource_id, name, discovered_at
                    FROM resources
                    ORDER BY discovered_at DESC
                    LIMIT %s
                """, (limit,))
                
                resources = []
                for row in cur.fetchall():
                    resources.append({
                        'account_id': row[0],
                        'region': row[1],
                        'resource_type': row[2],
                        'resource_id': row[3],
                        'name': row[4],
                        'discovered_at': str(row[5]) if row[5] else None
                    })
                
                results = {'resources': resources, 'count': len(resources)}
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Unknown report_type: {report_type}',
                    'valid_types': ['summary', 'accounts', 'by_type', 'by_account', 'resources']
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'report_type': report_type,
                'results': results
            }, default=str)
        }
        
    except Exception as e:
        logger.exception("Query failed")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
