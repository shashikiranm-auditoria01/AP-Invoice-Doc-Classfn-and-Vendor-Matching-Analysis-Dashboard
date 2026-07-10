"""
Targeted data pull for tenant_id: 674288818571972608
Uses the same logic as ap_invoice_data.py v5 but configured for a single tenant.
Run: python3 pull_tenant_674288818571972608.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ap_invoice_data import (
    authenticate, list_databases, find_tenant_db,
    fetch_tenant_data, update_vendor_names_from_json,
    format_datetime_columns, run_post_processing_queries,
    format_dates_in_json_columns, save_to_excel,
    METABASE_REGULAR_URL, METABASE_ENT_URL,
    USERNAME_REGULAR, USERNAME_ENT
)
import time, getpass

TARGET_TENANT = '674288818571972608'
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           f'AP_Invoice_Tenant_{TARGET_TENANT}.xlsx')

# Wide date range to get good data volume
DATE_FROM = '2026-06-01 00:00:00'
DATE_TO   = '2026-07-08 23:59:59'

# Monkey-patch the date range used by the imported module
import ap_invoice_data
ap_invoice_data.QUERY_DATE_FROM = DATE_FROM
ap_invoice_data.QUERY_DATE_TO = DATE_TO
ap_invoice_data.ALL_TENANT_IDS = [TARGET_TENANT]

def main():
    st = time.time()
    print("\n" + "="*70)
    print(f"  TARGETED DATA PULL — Tenant {TARGET_TENANT}")
    print(f"  Date range: {DATE_FROM} → {DATE_TO}")
    print("="*70)

    pw_r = getpass.getpass(f"\nRegular Metabase ({METABASE_REGULAR_URL}) password: ")

    instances = []

    t_r = authenticate(METABASE_REGULAR_URL, USERNAME_REGULAR, pw_r)
    if t_r:
        dbs_r = list_databases(METABASE_REGULAR_URL, t_r)
        ids_r = [d['id'] for d in dbs_r if any(k in d['name'].lower() for k in ('sor', 'shard'))]
        if not ids_r: ids_r = [d['id'] for d in dbs_r]
        instances.append({'name': 'Regular', 'url': METABASE_REGULAR_URL,
                          'token': t_r, 'db_ids': ids_r})

    pw_e = getpass.getpass(f"\nENT Metabase ({METABASE_ENT_URL}) password: ")
    t_e = authenticate(METABASE_ENT_URL, USERNAME_ENT, pw_e)
    if t_e:
        dbs_e = list_databases(METABASE_ENT_URL, t_e)
        ids_e = [d['id'] for d in dbs_e if any(k in d['name'].lower() for k in ('sor', 'shard'))]
        if not ids_e: ids_e = [d['id'] for d in dbs_e]
        if 6 in ids_e: ids_e.remove(6); ids_e.insert(0, 6)
        if 18 not in ids_e: ids_e.append(18)
        instances.append({'name': 'ENT', 'url': METABASE_ENT_URL,
                          'token': t_e, 'db_ids': ids_e})

    if not instances:
        print("\n✗ No Metabase instances authenticated"); sys.exit(1)

    print(f"\n{'='*70}")
    print(f"  Probing for tenant {TARGET_TENANT}...")
    print(f"{'='*70}")

    db_info = find_tenant_db(TARGET_TENANT, instances)
    if not db_info:
        print(f"\n✗ Tenant {TARGET_TENANT} not found on any instance in date range")
        print("  Try widening the date range or checking the tenant ID")
        sys.exit(1)

    print(f"\n→ Found on {db_info['name']} DB {db_info['db_id']} (~{db_info['rows']} rows)")

    df = fetch_tenant_data(TARGET_TENANT, db_info)
    if df is None or df.empty:
        print(f"\n✗ No data returned for tenant {TARGET_TENANT}")
        sys.exit(1)

    print(f"\n✓ Fetched {len(df):,} rows")

    tenant_db_map = {TARGET_TENANT: db_info}

    df = update_vendor_names_from_json(df)
    df = format_datetime_columns(df)
    df = run_post_processing_queries(df, instances, tenant_db_map)
    df = format_dates_in_json_columns(df)

    save_to_excel(df, OUTPUT_FILE, truncate=False)

    elapsed = time.time() - st
    print(f"\n{'='*70}")
    print(f"✓ Done — {len(df):,} rows in {elapsed:.1f}s")
    print(f"  Output: {OUTPUT_FILE}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠ Interrupted"); sys.exit(0)
    except Exception as e:
        import traceback; traceback.print_exc(); sys.exit(1)
