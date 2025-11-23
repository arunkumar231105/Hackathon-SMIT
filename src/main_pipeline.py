"""
Complete ETL Pipeline: Scrape → Clean → Load to SQL Server
Runs all steps in sequence automatically
"""

import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.scraper import main as scrape_main
from src.cleaner import clean_data
from src.db_load import load_data_to_sql

print("="*80)
print("BANGGOOD DATA PIPELINE")
print("="*80)
print("Step 1: Scraping -> data/raw.csv")
print("Step 2: Cleaning -> data/cleaned_products.csv")
print("Step 3: Loading -> SQL Server")
print("="*80)

# ============================================================================
# STEP 1: Scrape data and save to data/raw.csv
# ============================================================================
print("\n" + "="*80)
print("STEP 1: Scraping data with Selenium...")
print("="*80)

try:
    df_raw = scrape_main()
    
    if df_raw is None or len(df_raw) == 0:
        print("ERROR: No data scraped!")
        sys.exit(1)
    
    print(f"\n[OK] Scraping complete: {len(df_raw)} products saved to data/raw.csv")
    prices_found = df_raw['Price'].notna().sum()
    print(f"[OK] Products with prices: {prices_found}/{len(df_raw)}")
    if prices_found > 0:
        print(f"[OK] Price range: ${df_raw['Price'].min():.2f} - ${df_raw['Price'].max():.2f}")
    
except Exception as e:
    print(f"ERROR in scraping: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# STEP 2: Clean data and save to data/cleaned_products.csv
# ============================================================================
print("\n" + "="*80)
print("STEP 2: Cleaning data...")
print("="*80)

try:
    df_cleaned = clean_data('data/raw.csv', 'data/cleaned_products.csv')
    
    if df_cleaned is None or len(df_cleaned) == 0:
        print("ERROR: No data cleaned!")
        sys.exit(1)
    
    print(f"\n[OK] Cleaning complete: {len(df_cleaned)} products saved to data/cleaned_products.csv")
    
    # Validate cleaned data
    print("\nCleaned Data Summary:")
    print(f"  Total rows: {len(df_cleaned)}")
    print(f"  Price - Non-zero: {(df_cleaned['Price'] > 0).sum()}, NULL: {df_cleaned['Price'].isna().sum()}")
    print(f"  PricePerReview - Non-zero: {(df_cleaned['PricePerReview'] > 0).sum()}, NULL: {df_cleaned['PricePerReview'].isna().sum()}")
    print(f"  IsHighValue - Count of 1: {(df_cleaned['IsHighValue'] == 1).sum()}, Count of 0: {(df_cleaned['IsHighValue'] == 0).sum()}")
    print(f"  Rating - Min: {df_cleaned['Rating'].min():.2f}, Max: {df_cleaned['Rating'].max():.2f}")
    print(f"  ReviewCount - Total: {df_cleaned['ReviewCount'].sum():,}")
    
    # Check for NULLs
    nulls = {
        'Price': df_cleaned['Price'].isna().sum(),
        'PricePerReview': df_cleaned['PricePerReview'].isna().sum(),
        'IsHighValue': df_cleaned['IsHighValue'].isna().sum(),
        'Rating': df_cleaned['Rating'].isna().sum(),
        'ReviewCount': df_cleaned['ReviewCount'].isna().sum()
    }
    
    if any(nulls.values()):
        print(f"\n[WARNING] Found NULL values: {nulls}")
    else:
        print("\n[OK] No NULL values found - all columns filled!")
    
except Exception as e:
    print(f"ERROR in cleaning: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# STEP 3: Load cleaned data to SQL Server
# ============================================================================
print("\n" + "="*80)
print("STEP 3: Loading to SQL Server...")
print("="*80)

try:
    load_data_to_sql('data/cleaned_products.csv')
    
    print("\n[OK] SQL loading complete!")
    
except Exception as e:
    print(f"ERROR in SQL loading: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print("PIPELINE COMPLETE!")
print("="*80)
print("\nSummary:")
print(f"  [OK] Raw CSV: {len(df_raw)} products")
print(f"  [OK] Cleaned CSV: {len(df_cleaned)} products")
print(f"  [OK] SQL Server: Data loaded successfully")
print(f"\nFiles created:")
print(f"  - data/raw.csv")
print(f"  - data/cleaned_products.csv")
print("\n" + "="*80)

