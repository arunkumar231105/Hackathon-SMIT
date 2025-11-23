# Banggood Product Data Pipeline

A complete end-to-end data engineering and analysis project for scraping, processing, storing, and visualizing Banggood product data.

## 📋 Overview

This project implements a comprehensive data pipeline that:
- Scrapes product data from Banggood across multiple categories
- Cleans and transforms the raw data
- Loads processed data into SQL Server
- Provides an interactive Streamlit dashboard for data exploration

## ✨ Features

- **Web Scraping**: Automated scraping of 5 categories × 5 pages = 25 pages of product data using Selenium
- **Data Cleaning**: Robust data cleaning with derived feature engineering (IsHighValue, PricePerReview)
- **SQL Server Integration**: Automated data loading with validation
- **Interactive Dashboard**: Real-time data exploration with Streamlit
- **Production-Ready**: Error handling, retry logic, and progress tracking

## 🏗️ Architecture

```
┌─────────────┐
│   Scraper   │ → data/raw.csv
└─────────────┘
       ↓
┌─────────────┐
│   Cleaner   │ → data/cleaned_products.csv
└─────────────┘
       ↓
┌─────────────┐
│ SQL Server  │ → Structured Database
└─────────────┘
       ↓
┌─────────────┐
│  Dashboard  │ → Interactive UI
└─────────────┘
```

## 📁 Project Structure

```
banggood_data_pipeline/
├── src/
│   ├── scraper.py          # Web scraping module
│   ├── cleaner.py          # Data cleaning module
│   ├── db_load.py          # SQL Server loading module
│   └── main_pipeline.py    # Complete ETL pipeline
├── dashboard/
│   └── app.py              # Streamlit dashboard
├── data/
│   ├── raw.csv             # Raw scraped data
│   └── cleaned_products.csv # Cleaned data
├── plots/                  # Generated visualizations (optional)
├── sql/
│   └── queries.sql         # SQL analysis queries
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- SQL Server (with database `BanggoodAnalysisDB` created)
- ODBC Driver 17 for SQL Server (or SQL Server driver)
- Chrome browser (for Selenium)

### Installation

1. **Clone or download the project**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up SQL Server Database**
   ```sql
   CREATE DATABASE BanggoodAnalysisDB;
   
   USE BanggoodAnalysisDB;
   
   CREATE TABLE Banggood_Products (
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
   ```

4. **Update database connection** (if needed)
   - Edit `src/db_load.py` and `dashboard/app.py`
   - Update `SERVER` and `DATABASE` variables

## 📖 How to Run

### Option 1: Run Complete Pipeline (Recommended)

Run the entire ETL pipeline in one command:

```bash
python -m src.main_pipeline
```

This will:
1. Scrape data from Banggood (5 categories × 5 pages)
2. Clean and transform the data
3. Load data into SQL Server

### Option 2: Run Individual Steps

**Step 1: Scrape Data**
```bash
python -m src.scraper
```
- Scrapes 5 categories × 5 pages
- Saves raw data to `data/raw.csv`
- Uses Selenium with retry logic

**Step 2: Clean Data**
```bash
python -m src.cleaner
```
- Cleans raw data
- Creates derived features (IsHighValue, PricePerReview)
- Saves cleaned data to `data/cleaned_products.csv`

**Step 3: Load to SQL Server**
```bash
python -m src.db_load
```
- Loads cleaned data into SQL Server
- Validates insertion with row counts

### Launch Dashboard

```bash
streamlit run dashboard/app.py
```
- Opens interactive dashboard in browser
- Filter by category, price range, rating
- View metrics, top products, and visualizations

## 🔍 How Scraping Works

The scraper uses Selenium to extract product information:

1. **Categories**: RC_Toys, Smart_Home, Tools, Outdoor_Gear, Drones
2. **Pages per Category**: 5 pages (configurable)
3. **Extracted Fields**:
   - Product Name
   - Product URL
   - Price (extracted from `oriprice` attribute)
   - Rating
   - Review Count

**Features**:
- Headless Chrome browser
- Retry logic (3 attempts with exponential backoff)
- Progress bars with `tqdm`
- Respectful delays between requests

## 🔄 How ETL Works

### Extract
- Selenium-based web scraping
- Data extraction using CSS selectors
- CSV export for raw data

### Transform
- **Price Cleaning**: Remove currency symbols, convert to float, fill missing with category median
- **Rating Cleaning**: Extract numeric values, default to 0
- **Review Count**: Parse text like "3 reviews" → 3
- **Derived Features**:
  - `IsHighValue`: Rating ≥ 4.5 AND Price < category median
  - `PricePerReview`: Price / max(ReviewCount, 1)

### Load
- SQL Server insertion using `pyodbc`
- Batch processing with error handling
- Data validation and row count verification

## 📊 Dashboard Features

The Streamlit dashboard provides:

- **Category Filtering**: Select specific category or view all
- **Key Metrics**: Average price, rating, total reviews, high-value count
- **Overview Tab**: Category summary statistics
- **Top Products Tab**: Most reviewed products with configurable count
- **Visualizations Tab**: Interactive charts and saved plots
- **Value Score Tab**: Products ranked by (Rating × Reviews) / Price
- **Data Explorer Tab**: Full dataset with search functionality

## ⚠️ Important Notes

1. **Data Paths**: All CSV files are stored in the `data/` folder
2. **Database Connection**: Uses Windows Authentication by default
3. **Dashboard Fallback**: Dashboard can load from CSV if database is unavailable
4. **Scraping**: Uses headless Chrome - ensure Chrome is installed

## 🔮 Future Improvements

1. **Scraping**: Implement parallel scraping with `asyncio`
2. **Data Pipeline**: Add data quality checks and validation
3. **Analysis**: Add more advanced statistical analysis
4. **Dashboard**: Add more interactive filters and export functionality
5. **Infrastructure**: Containerize with Docker


**Built with**: Python, Selenium, pandas, SQL Server, Streamlit, matplotlib
