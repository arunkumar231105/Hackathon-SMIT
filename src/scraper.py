"""
Banggood Product Scraper
Scrapes product data from multiple categories and pages using Selenium
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm
import os
import re

# Categories configuration
categories = {
    "RC_Toys": "https://www.banggood.com/search/rc-toys.html?page=",
    "Smart_Home": "https://www.banggood.com/search/smart-home.html?page=",
    "Tools": "https://www.banggood.com/search/tools.html?page=",
    "Outdoor_Gear": "https://www.banggood.com/search/outdoor-gear.html?page=",
    "Drones": "https://www.banggood.com/search/drones.html?page="
}

# Pagination configuration
PAGES_PER_CATEGORY = 5  # Number of pages to scrape per category
MAX_RETRIES_PER_PAGE = 3  # Maximum retry attempts for failed pages
PAGE_LOAD_TIMEOUT = 20  # Timeout in seconds for page load

def get_driver():
    """Initialize and return Chrome WebDriver with options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def clean_text(text):
    """Clean text: remove non-breaking spaces, hidden characters, and extra symbols"""
    if not text:
        return ""
    # Convert to string and strip
    text = str(text).strip()
    # Replace non-breaking spaces and other Unicode spaces
    text = text.replace('\u00A0', ' ')  # Non-breaking space
    text = text.replace('\u2009', ' ')  # Thin space
    text = text.replace('\u200B', '')   # Zero-width space
    text = text.replace('\u200C', '')   # Zero-width non-joiner
    text = text.replace('\u200D', '')  # Zero-width joiner
    text = text.replace('\uFEFF', '')   # Zero-width no-break space
    # Remove other hidden characters
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)  # Control characters
    return text.strip()

def wait_for_page_load(driver, timeout=None):
    """Wait for page to load and products to be visible"""
    if timeout is None:
        timeout = PAGE_LOAD_TIMEOUT
    try:
        # Wait for product blocks to load
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.p-wrap, .product-item, [class*='product']"))
        )
        time.sleep(2)  # Additional wait for JavaScript to render prices
        return True
    except:
        return False

def check_pagination_exists(driver):
    """Check if there are more pages available"""
    try:
        # Look for pagination elements (next page button, page numbers, etc.)
        next_button = driver.find_elements(By.CSS_SELECTOR, "a.next, .pagination a[aria-label*='next'], .page-next")
        page_numbers = driver.find_elements(By.CSS_SELECTOR, ".pagination a, .page-num")
        
        # If we find pagination elements, there are likely more pages
        if next_button or len(page_numbers) > 1:
            return True
        return False
    except:
        return False

def get_max_pages(driver, base_url):
    """Try to determine maximum pages available for a category"""
    try:
        # Navigate to first page
        driver.get(base_url + "1")
        time.sleep(2)
        
        # Look for pagination info
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Try to find max page number
        pagination = soup.find('div', class_='pagination')
        if not pagination:
            pagination = soup.find('ul', class_='pagination')
        if not pagination:
            pagination = soup.find('nav', class_='pagination')
        
        if pagination:
            # Find all page number links
            page_links = pagination.find_all('a', href=True)
            max_page = 1
            
            for link in page_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                # Extract page number from href or text
                page_match = re.search(r'page[=\s]*(\d+)', href, re.I)
                if not page_match:
                    page_match = re.search(r'(\d+)', text)
                
                if page_match:
                    page_num = int(page_match.group(1))
                    max_page = max(max_page, page_num)
            
            return min(max_page, 50)  # Cap at 50 pages max
        
        return PAGES_PER_CATEGORY  # Default if can't determine
    except:
        return PAGES_PER_CATEGORY

def extract_price(price_text):
    """Extract numeric price from text - clean and convert to float"""
    if not price_text:
        return None
    # Clean text first
    price_text = clean_text(str(price_text))
    # Remove currency symbols, commas, and extract numbers with decimal point
    price_clean = re.sub(r'[^\d.]', '', price_text)
    try:
        price_value = float(price_clean) if price_clean else None
        return price_value if price_value and price_value > 0 else None
    except:
        return None

def extract_rating(rating_text):
    """Extract rating from text - clean and convert to float"""
    if not rating_text:
        return None
    # Clean text first
    rating_text = clean_text(str(rating_text))
    # Extract numeric rating (supports formats like "4.5", "4,5", "4 5")
    rating_match = re.search(r'(\d+[.,]?\d*)', rating_text)
    if rating_match:
        try:
            rating_str = rating_match.group(1).replace(',', '.')
            rating_value = float(rating_str)
            return rating_value if 0 <= rating_value <= 5 else None
        except:
            return None
    return None

def extract_review_count(review_text):
    """Extract review count from text - strip 'reviews' text and keep digits only"""
    if not review_text:
        return 0
    # Clean text first
    review_text = clean_text(str(review_text))
    # Remove "reviews", "review" text and extract digits only
    review_text = re.sub(r'reviews?', '', review_text, flags=re.IGNORECASE)
    review_text = review_text.strip()
    # Extract number (digits only)
    review_match = re.search(r'(\d+)', review_text)
    if review_match:
        try:
            return int(review_match.group(1))
        except:
            return 0
    return 0

def scrape_page(driver, category, url, page_num, retry_count=0):
    """Scrape a single page using Selenium with retry logic"""
    page_url = url + str(page_num)
    products = []
    
    try:
        # Navigate to page
        driver.get(page_url)
        
        # Wait for price elements to load (wait for span.price with oriprice attribute)
        try:
            WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.price[oriprice]"))
            )
            time.sleep(3)  # Additional wait for all JavaScript to render prices
        except:
            # Fallback: wait for any price elements
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.price"))
                )
                time.sleep(3)  # Wait for oriprice attributes to be set
            except:
                # Final fallback: wait for product blocks
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.p-wrap"))
                    )
                    time.sleep(3)
                except:
                    if retry_count < MAX_RETRIES_PER_PAGE:
                        print(f"  Retrying page {page_num} (attempt {retry_count + 1}/{MAX_RETRIES_PER_PAGE})...")
                        time.sleep(2)
                        return scrape_page(driver, category, url, page_num, retry_count + 1)
                    else:
                        print(f"  Warning: Page {page_num} did not load properly after {MAX_RETRIES_PER_PAGE} attempts")
                        return products
        
        # Get page source after JavaScript execution
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all product blocks
        product_blocks = soup.find_all('div', class_='p-wrap')
        
        # If p-wrap not found, try alternative selectors
        if not product_blocks:
            product_blocks = soup.find_all('div', {'class': re.compile(r'product|item', re.I)})
        
        for block in product_blocks:
            try:
                # Product Name
                name_elem = block.find('a', class_='title')
                if not name_elem:
                    name_elem = block.find('a', {'class': re.compile(r'title|name', re.I)})
                product_name = name_elem.get_text(strip=True) if name_elem else None
                
                if not product_name:
                    continue
                
                # Product URL
                url_elem = block.find('a', class_='exclick')
                if not url_elem:
                    url_elem = block.find('a', class_='title')
                if not url_elem:
                    url_elem = block.find('a', href=True)
                product_url = url_elem.get('href', '') if url_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = 'https://www.banggood.com' + product_url
                
                # Price - Extract from "oriprice" attribute (primary method from Selenium-rendered page)
                price = None
                # Try multiple selectors for price element
                price_elem = block.find('span', class_='price')
                if not price_elem:
                    # Try with "notranslate" class too
                    price_elem = block.find('span', class_=re.compile(r'price'))
                if not price_elem:
                    # Try any span with oriprice attribute
                    price_elem = block.find('span', attrs={'oriprice': True})
                
                if price_elem:
                    # Primary method: Extract oriprice attribute (this is what we want!)
                    oriprice = price_elem.get('oriprice')
                    if oriprice:
                        price = extract_price(oriprice)
                    
                    # Fallback: Try text content if oriprice not found
                    if price is None:
                        price_text = price_elem.get_text(strip=True)
                        if price_text:
                            price = extract_price(price_text)
                
                # Rating - Extract as float
                rating = None
                review_box = block.find('div', class_='reivew-box')
                if not review_box:
                    review_box = block.find('div', class_='review-box')
                if review_box:
                    rating_elem = review_box.find('span', class_='review-text')
                    if rating_elem:
                        rating_text = clean_text(rating_elem.get_text(strip=True))
                        rating = extract_rating(rating_text)
                
                # Review Count - Extract as integer
                review_count = 0
                review_link = block.find('a', class_='review')
                if review_link:
                    review_text = clean_text(review_link.get_text(strip=True))
                    review_count = extract_review_count(review_text)
                else:
                    # Try alternative selectors
                    review_elem = block.find('span', class_='review')
                    if not review_elem:
                        review_elem = block.find('div', class_='review')
                    if review_elem:
                        review_text = clean_text(review_elem.get_text(strip=True))
                        review_count = extract_review_count(review_text)
                
                products.append({
                    'Category': category,
                    'ProductName': product_name,
                    'Price': price,
                    'Rating': rating,
                    'ReviewCount': review_count,
                    'ProductURL': product_url
                })
            except Exception as e:
                continue
        
    except Exception as e:
        print(f"  Error scraping page {page_num}: {e}")
    
    return products

def main(pages_per_category=None):
    """
    Main scraping function using Selenium with enhanced pagination
    
    Args:
        pages_per_category: Number of pages to scrape per category (default: PAGES_PER_CATEGORY)
    """
    if pages_per_category is None:
        pages_per_category = PAGES_PER_CATEGORY
    
    all_products = []
    
    # Initialize Selenium driver
    print("Initializing Selenium WebDriver...")
    driver = get_driver()
    
    try:
        # Scrape each category
        for category, base_url in categories.items():
            print(f"\nScraping category: {category}")
            category_products = []
            
            # Try to determine max pages for this category
            try:
                max_pages = get_max_pages(driver, base_url)
                pages_to_scrape = min(pages_per_category, max_pages)
                print(f"  Scraping {pages_to_scrape} pages (max available: {max_pages})")
            except:
                pages_to_scrape = pages_per_category
                print(f"  Scraping {pages_to_scrape} pages (default)")
            
            # Scrape pages with pagination
            for page in tqdm(range(1, pages_to_scrape + 1), desc=f"{category} pages"):
                products = scrape_page(driver, category, base_url, page)
                
                if len(products) == 0 and page > 1:
                    # If no products found and we're past page 1, might be end of pagination
                    print(f"  No products found on page {page}, stopping pagination for {category}")
                    break
                
                category_products.extend(products)
                
                # Be respectful with delays between pages
                if page < pages_to_scrape:
                    time.sleep(2)
            
            all_products.extend(category_products)
            print(f"  Scraped {len(category_products)} products from {category}")
    
    finally:
        # Close driver
        driver.quit()
        print("\nWebDriver closed")
    
    # Create DataFrame
    df = pd.DataFrame(all_products)
    
    # Save to CSV in data/ folder
    os.makedirs('data', exist_ok=True)
    output_path = 'data/raw.csv'
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"\nTotal products scraped: {len(df)}")
    print(f"Data saved to: {output_path}")
    
    return df

if __name__ == "__main__":
    df = main()

