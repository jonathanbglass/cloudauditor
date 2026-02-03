#!/usr/bin/env python3
"""
Query CloudAuditor Database
Simple script to query and report on discovered resources
"""
import argparse
import sys
from lib.database import DatabaseClient

def main():
    parser = argparse.ArgumentParser(description='Query CloudAuditor database')
    parser.add_argument('--summary', action='store_true', help='Show summary statistics')
    parser.add_argument('--accounts', action='store_true', help='List monitored accounts')
    parser.add_argument('--resources', action='store_true', help='List all resources')
    parser.add_argument('--by-type', action='store_true', help='Group resources by type')
    parser.add_argument('--by-account', action='store_true', help='Group resources by account')
    parser.add_argument('--limit', type=int, default=100, help='Limit results (default: 100)')
    
    args = parser.parse_args()
    
    # If no flags, show summary by default
    if not any([args.summary, args.accounts, args.resources, args.by_type, args.by_account]):
        args.summary = True
    
    try:
        db = DatabaseClient()
        conn = db._get_connection()
        
        if args.summary:
            print("\n=== CLOUDAUDITOR DATABASE SUMMARY ===\n")
            
            with conn.cursor() as cur:
                # Total resources
                cur.execute("SELECT COUNT(*) FROM resources")
                total_resources = cur.fetchone()[0]
                print(f"Total Resources: {total_resources:,}")
                
                # Unique resource types
                cur.execute("SELECT COUNT(DISTINCT resource_type) FROM resources")
                unique_types = cur.fetchone()[0]
                print(f"Unique Resource Types: {unique_types}")
                
                # Unique accounts
                cur.execute("SELECT COUNT(DISTINCT account_id) FROM resources")
                unique_accounts = cur.fetchone()[0]
                print(f"Accounts with Resources: {unique_accounts}")
                
                # Monitored accounts
                cur.execute("SELECT COUNT(*) FROM monitored_accounts")
                monitored = cur.fetchone()[0]
                print(f"Monitored Accounts: {monitored}")
                
                # Latest scan
                cur.execute("SELECT MAX(discovered_at) FROM resources")
                latest_scan = cur.fetchone()[0]
                print(f"Latest Scan: {latest_scan}")
        
        if args.accounts:
            print("\n=== MONITORED ACCOUNTS ===\n")
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT account_id, account_name, status, auto_discovered, 
                           last_verification_at, last_error_message
                    FROM monitored_accounts
                    ORDER BY account_id
                """)
                
                print(f"{'Account ID':<15} {'Name':<30} {'Status':<10} {'Auto':<6} {'Last Verified':<20}")
                print("-" * 90)
                
                for row in cur.fetchall():
                    account_id, name, status, auto, verified, error = row
                    auto_flag = "Yes" if auto else "No"
                    verified_str = str(verified)[:19] if verified else "Never"
                    print(f"{account_id:<15} {name or 'N/A':<30} {status:<10} {auto_flag:<6} {verified_str:<20}")
                    if error:
                        print(f"  Error: {error}")
        
        if args.by_type:
            print("\n=== RESOURCES BY TYPE ===\n")
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT resource_type, COUNT(*) as count
                    FROM resources
                    GROUP BY resource_type
                    ORDER BY count DESC
                    LIMIT %s
                """, (args.limit,))
                
                print(f"{'Resource Type':<50} {'Count':>10}")
                print("-" * 62)
                
                for row in cur.fetchall():
                    resource_type, count = row
                    print(f"{resource_type:<50} {count:>10,}")
        
        if args.by_account:
            print("\n=== RESOURCES BY ACCOUNT ===\n")
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT account_id, COUNT(*) as count, COUNT(DISTINCT resource_type) as types
                    FROM resources
                    GROUP BY account_id
                    ORDER BY count DESC
                """)
                
                print(f"{'Account ID':<15} {'Resources':>12} {'Types':>8}")
                print("-" * 38)
                
                for row in cur.fetchall():
                    account_id, count, types = row
                    print(f"{account_id:<15} {count:>12,} {types:>8}")
        
        if args.resources:
            print("\n=== RESOURCES (Sample) ===\n")
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT account_id, region, resource_type, resource_id, discovered_at
                    FROM resources
                    ORDER BY discovered_at DESC
                    LIMIT %s
                """, (args.limit,))
                
                print(f"{'Account':<15} {'Region':<15} {'Type':<40} {'ID':<50}")
                print("-" * 125)
                
                for row in cur.fetchall():
                    account, region, rtype, rid, discovered = row
                    print(f"{account:<15} {region:<15} {rtype:<40} {rid[:50]:<50}")
        
        print()
        
    except Exception as e:
        print(f"Error querying database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
