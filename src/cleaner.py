"""
Data Cleaning Module
Cleans raw scraped data and creates derived features
"""

import pandas as pd
import numpy as np
import os
import re

def clean_price(price):
    """Clean price: remove currency symbols, convert to float"""
    if pd.isna(price):
        return None
    if isinstance(price, (int, float)):
        return float(price)
    # Remove currency symbols and extract numbers
    price_str = str(price).replace('US$', '').replace('$', '').strip()
    price_clean = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(price_clean)
    except:
        return None

def clean_rating(rating):
    """Clean rating: convert to float, missing → 0"""
    if pd.isna(rating):
        return 0.0
    if isinstance(rating, (int, float)):
        return float(rating)
    try:
        return float(rating)
    except:
        return 0.0

def clean_review_count(review_count):
    """Clean review count: extract number from text"""
    if pd.isna(review_count):
        return 0
    if isinstance(review_count, (int, float)):
        return int(review_count)
    # Extract number from text like "3 reviews"
    review_match = re.search(r'(\d+)', str(review_count))
    if review_match:
        try:
            return int(review_match.group(1))
        except:
            return 0
    return 0

def create_derived_features(df):
    """Create derived features: IsHighValue and PricePerReview"""
    df = df.copy()
    
    # Ensure ReviewCount is integer (fill missing with 0)
    df['ReviewCount'] = df['ReviewCount'].fillna(0).astype(int)
    
    # Ensure Rating is float (fill missing with 0.0)
    df['Rating'] = df['Rating'].fillna(0.0).astype(float)
    
    # Fill missing prices with median of category, then overall median
    # This ensures Price is NEVER NULL
    df['Price'] = df.groupby('Category')['Price'].transform(
        lambda x: x.fillna(x.median()) if x.median() is not None and not pd.isna(x.median()) else x
    )
    # Fill any remaining NaN with overall median, or 0 if no prices exist
    overall_median = df['Price'].median()
    if pd.isna(overall_median) or overall_median is None:
        overall_median = 0.0
    df['Price'] = df['Price'].fillna(overall_median).astype(float)
    
    # Calculate median price per category for IsHighValue calculation
    category_medians = df.groupby('Category')['Price'].median()
    
    # IsHighValue: 1 if Rating >= 4.5 AND Price < median(category_price), else 0
    def calculate_is_high_value(row):
        category_median = category_medians.get(row['Category'], row['Price'])
        if pd.isna(category_median) or category_median is None:
            category_median = row['Price']
        # Ensure we have valid values
        if pd.isna(row['Rating']) or pd.isna(row['Price']):
            return 0
        # Calculate: Rating >= 4.5 AND Price < category median
        is_high = (row['Rating'] >= 4.5) and (row['Price'] < category_median)
        return 1 if is_high else 0
    
    df['IsHighValue'] = df.apply(calculate_is_high_value, axis=1).astype(int)
    
    # PricePerReview: Price / max(ReviewCount, 1) - NEVER NULL
    df['PricePerReview'] = df.apply(
        lambda row: row['Price'] / max(row['ReviewCount'], 1),
        axis=1
    ).astype(float)
    
    return df

def clean_data(input_path='data/raw.csv', output_path='data/cleaned_products.csv'):
    """Main cleaning function"""
    # Load raw data
    print(f"Loading raw data from: {input_path}")
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows")
    
    # Clean columns
    print("Cleaning data...")
    
    # Clean ProductName: strip extra spaces
    df['ProductName'] = df['ProductName'].astype(str).str.strip()
    
    # Clean Price
    df['Price'] = df['Price'].apply(clean_price)
    
    # Clean Rating
    df['Rating'] = df['Rating'].apply(clean_rating)
    
    # Clean ReviewCount
    df['ReviewCount'] = df['ReviewCount'].apply(clean_review_count)
    
    # Clean Category: strip extra spaces
    df['Category'] = df['Category'].astype(str).str.strip()
    
    # Clean ProductURL: strip extra spaces
    df['ProductURL'] = df['ProductURL'].astype(str).str.strip()
    
    # Remove rows with missing critical fields
    df = df[df['ProductName'].notna() & (df['ProductName'] != '')]
    
    # Create derived features
    print("Creating derived features...")
    df = create_derived_features(df)
    
    # Ensure data types match SQL schema
    df['Category'] = df['Category'].astype(str)
    df['ProductName'] = df['ProductName'].astype(str)
    df['Price'] = df['Price'].astype(float)
    df['Rating'] = df['Rating'].astype(float)
    df['ReviewCount'] = df['ReviewCount'].astype(int)
    df['IsHighValue'] = df['IsHighValue'].astype(int)  # 0 or 1, not bool
    df['PricePerReview'] = df['PricePerReview'].astype(float)
    df['ProductURL'] = df['ProductURL'].astype(str)
    
    # Round Price and PricePerReview to 2 decimal places
    df['Price'] = df['Price'].round(2)
    df['PricePerReview'] = df['PricePerReview'].round(2)
    
    # Round Rating to 2 decimal places
    df['Rating'] = df['Rating'].round(2)
    
    # Final validation: Ensure Price and PricePerReview are NEVER NULL
    assert df['Price'].notna().all(), "Price column contains NULL values!"
    assert df['PricePerReview'].notna().all(), "PricePerReview column contains NULL values!"
    assert df['ReviewCount'].notna().all(), "ReviewCount column contains NULL values!"
    assert df['Rating'].notna().all(), "Rating column contains NULL values!"
    
    # Save cleaned data
    os.makedirs('data', exist_ok=True)
    print(f"Saving cleaned data to: {output_path}")
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"Cleaned {len(df)} rows")
    print(f"\nData summary:")
    print(df.describe())
    print(f"\nMissing values:")
    print(df.isnull().sum())
    
    return df

if __name__ == "__main__":
    df = clean_data()

