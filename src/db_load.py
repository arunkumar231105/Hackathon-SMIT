"""
SQL Server Data Loading Module
Loads cleaned data into SQL Server database
"""

import pyodbc
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
SERVER = 'MYPC'
DATABASE = 'BanggoodAnalysisDB'
TABLE_NAME = 'Banggood_Products'

def get_connection():
    """Create SQL Server connection"""
    connection_string = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={SERVER};'
        f'DATABASE={DATABASE};'
        f'Trusted_Connection=yes;'
    )
    
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except pyodbc.Error as e:
        print(f"Error connecting to SQL Server: {e}")
        # Try alternative connection string
        try:
            connection_string = (
                f'DRIVER={{SQL Server}};'
                f'SERVER={SERVER};'
                f'DATABASE={DATABASE};'
                f'Trusted_Connection=yes;'
            )
            conn = pyodbc.connect(connection_string)
            return conn
        except pyodbc.Error as e2:
            print(f"Alternative connection also failed: {e2}")
            raise

def create_table_if_not_exists(conn):
    """Create table if it doesn't exist"""
    cursor = conn.cursor()
    
    create_table_sql = f"""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[{TABLE_NAME}]') AND type in (N'U'))
    BEGIN
        CREATE TABLE {TABLE_NAME} (
            ProductID INT PRIMARY KEY IDENTITY(1,1),
            Category NVARCHAR(50),
            ProductName NVARCHAR(255),
            Price DECIMAL(10, 2),
            Rating DECIMAL(3, 2),
            ReviewCount INT,
            IsHighValue BIT,
            PricePerReview DECIMAL(10, 2),
            ProductURL NVARCHAR(MAX)
        );
    END
    """
    
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        print(f"Table {TABLE_NAME} verified/created successfully")
    except pyodbc.Error as e:
        print(f"Error creating table: {e}")
        conn.rollback()
    finally:
        cursor.close()

def clear_table(conn):
    """Clear existing data from table"""
    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM {TABLE_NAME}")
        conn.commit()
        print(f"Cleared existing data from {TABLE_NAME}")
    except pyodbc.Error as e:
        print(f"Error clearing table: {e}")
        conn.rollback()
    finally:
        cursor.close()

def load_data_to_sql(csv_path='data/cleaned_products.csv'):
    """Load cleaned CSV data into SQL Server"""
    
    # Check if file exists
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        return
    
    # Load cleaned data
    print(f"Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from CSV")
    
    # Validate DataFrame before SQL insert - print first 5 rows
    print("\n" + "="*80)
    print("VALIDATION: First 5 rows before SQL insert:")
    print("="*80)
    validation_cols = ['Category', 'ProductName', 'Price', 'Rating', 'ReviewCount', 'IsHighValue', 'PricePerReview']
    print(df[validation_cols].head(5).to_string(index=False))
    print("\nData Summary:")
    print(f"  Total rows: {len(df)}")
    print(f"  Price - Non-zero: {(df['Price'] > 0).sum()}, Min: ${df['Price'].min():.2f}, Max: ${df['Price'].max():.2f}")
    print(f"  ReviewCount - Non-zero: {(df['ReviewCount'] > 0).sum()}, Min: {df['ReviewCount'].min()}, Max: {df['ReviewCount'].max()}")
    print(f"  IsHighValue - Count of 1: {(df['IsHighValue'] == 1).sum()}, Count of 0: {(df['IsHighValue'] == 0).sum()}")
    print(f"  NULL check - Price: {df['Price'].isna().sum()}, PricePerReview: {df['PricePerReview'].isna().sum()}")
    print("="*80 + "\n")
    
    # Connect to database
    print(f"Connecting to SQL Server: {SERVER}/{DATABASE}")
    conn = get_connection()
    
    try:
        # Create table if not exists
        create_table_if_not_exists(conn)
        
        # Clear existing data (optional - comment out if you want to append)
        # clear_table(conn)
        
        # Prepare data for insertion
        cursor = conn.cursor()
        
        insert_sql = f"""
        INSERT INTO {TABLE_NAME} 
        (Category, ProductName, Price, Rating, ReviewCount, IsHighValue, PricePerReview, ProductURL)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Insert rows
        inserted_count = 0
        for _, row in df.iterrows():
            try:
                # IsHighValue should already be 0 or 1 (int), but ensure it's correct
                is_high_value = int(row['IsHighValue']) if pd.notna(row['IsHighValue']) else 0
                if is_high_value not in [0, 1]:
                    is_high_value = 1 if is_high_value else 0
                
                # Ensure all numeric fields are filled (should never be NULL after cleaning)
                price = float(row['Price']) if pd.notna(row['Price']) else 0.0
                rating = float(row['Rating']) if pd.notna(row['Rating']) else 0.0
                review_count = int(row['ReviewCount']) if pd.notna(row['ReviewCount']) else 0
                price_per_review = float(row['PricePerReview']) if pd.notna(row['PricePerReview']) else 0.0
                
                # Final validation - Price and PricePerReview must never be NULL
                if pd.isna(price) or price is None:
                    price = 0.0
                if pd.isna(price_per_review) or price_per_review is None:
                    price_per_review = 0.0
                
                cursor.execute(insert_sql, (
                    str(row['Category'])[:50],
                    str(row['ProductName'])[:255],
                    price,
                    rating,
                    review_count,
                    is_high_value,
                    price_per_review,
                    str(row['ProductURL'])
                ))
                inserted_count += 1
            except Exception as e:
                print(f"Error inserting row: {e}")
                continue
        
        conn.commit()
        print(f"\nSuccessfully inserted {inserted_count} rows into {TABLE_NAME}")
        
        # Validate insertion
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        total_count = cursor.fetchone()[0]
        print(f"Total rows in database: {total_count}")
        
    except pyodbc.Error as e:
        print(f"Error loading data: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        print("Database connection closed")

if __name__ == "__main__":
    load_data_to_sql()

