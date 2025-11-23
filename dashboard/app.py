import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pyodbc
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
SERVER = 'MYPC'
DATABASE = 'BanggoodAnalysisDB'
TABLE_NAME = 'Banggood_Products'

# Set page config
st.set_page_config(
    page_title="Banggood Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design
st.markdown("""
<style>
    /* Main styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ------------------ DB CONNECTION HELPERS ------------------ #

@st.cache_resource
def get_connection():
    """Create SQL Server connection (cached as a resource)"""
    connection_string = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={SERVER};'
        f'DATABASE={DATABASE};'
        f'Trusted_Connection=yes;'
    )

    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except pyodbc.Error:
        try:
            connection_string = (
                f'DRIVER={{SQL Server}};'
                f'SERVER={SERVER};'
                f'DATABASE={DATABASE};'
                f'Trusted_Connection=yes;'
            )
            conn = pyodbc.connect(connection_string)
            return conn
        except pyodbc.Error as e:
            st.error(f"Error connecting to database: {e}")
            return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data_from_sql():
    """Load data from SQL Server"""
    conn = get_connection()
    if conn is None:
        return None

    try:
        query = f"SELECT * FROM {TABLE_NAME}"
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None
    finally:
        if conn:
            conn.close()

def load_data_from_csv():
    """Load data from CSV as fallback"""
    csv_path = 'data/cleaned_products.csv'
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None

# ------------------ MAIN APP ------------------ #

def main():
    """Main dashboard function"""

    # Header
    st.markdown('<h1 class="main-header">📊 Banggood Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Real-time product insights and analysis</p>', unsafe_allow_html=True)

    # Load data
    with st.spinner("Loading data from SQL Server..."):
        df = load_data_from_sql()
        if df is None:
            st.warning("⚠️ Could not connect to database. Trying to load from CSV...")
            df = load_data_from_csv()

    if df is None:
        st.error("❌ No data available. Please run the data pipeline first.")
        return

    # Convert IsHighValue from bit to boolean if needed
    if 'IsHighValue' in df.columns:
        df['IsHighValue'] = df['IsHighValue'].astype(int)

    # ============================== SIDEBAR ============================== #
    with st.sidebar:
        st.markdown("## 🎛️ **Dashboard Controls**")
        st.markdown("---")

        # Category filter
        st.markdown("### **Filters**")
        categories = ['All Categories'] + sorted(df['Category'].unique().tolist())
        selected_category = st.selectbox(
            "Select Category",
            categories,
            key="category_filter"
        )

        # Price range filter
        st.markdown("### **Price Range**")
        min_price = float(df['Price'].min())
        max_price = float(df['Price'].max())
        price_range = st.slider(
            "Price Range ($)",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price),
            key="price_filter"
        )

        # Rating filter
        st.markdown("### **Rating Filter**")
        min_rating = float(df['Rating'].min())
        max_rating = float(df['Rating'].max())
        rating_range = st.slider(
            "Rating Range",
            min_value=min_rating,
            max_value=max_rating,
            value=(min_rating, max_rating),
            key="rating_filter"
        )

        # High value filter
        st.markdown("### **Product Type**")
        show_high_value = st.checkbox("Show High Value Products Only", key="high_value_filter")

        st.markdown("---")

        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")

        # Statistics
        st.markdown("### **Quick Stats**")
        filtered_df = df.copy()
        if selected_category != 'All Categories':
            filtered_df = filtered_df[filtered_df['Category'] == selected_category]
        filtered_df = filtered_df[
            (filtered_df['Price'] >= price_range[0]) &
            (filtered_df['Price'] <= price_range[1]) &
            (filtered_df['Rating'] >= rating_range[0]) &
            (filtered_df['Rating'] <= rating_range[1])
        ]
        if show_high_value:
            filtered_df = filtered_df[filtered_df['IsHighValue'] == 1]

        st.metric("Total Products", f"{len(filtered_df):,}")
        st.metric("Avg Price", f"${filtered_df['Price'].mean():.2f}")
        st.metric("Avg Rating", f"{filtered_df['Rating'].mean():.2f}")

    # ============================ MAIN CONTENT =========================== #

    # Key Metrics Row
    st.markdown("---")
    st.markdown("## 📈 **Key Performance Indicators**")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        avg_price = filtered_df['Price'].mean()
        st.metric(
            "💰 Average Price",
            f"${avg_price:.2f}" if not pd.isna(avg_price) else "N/A",
            delta=None
        )

    with col2:
        avg_rating = filtered_df['Rating'].mean()
        st.metric(
            "⭐ Average Rating",
            f"{avg_rating:.2f}" if not pd.isna(avg_rating) else "N/A",
            delta=None
        )

    with col3:
        total_reviews = filtered_df['ReviewCount'].sum()
        st.metric(
            "💬 Total Reviews",
            f"{total_reviews:,}",
            delta=None
        )

    with col4:
        high_value_count = int(filtered_df['IsHighValue'].sum())
        st.metric(
            "🏆 High Value Products",
            f"{high_value_count}",
            delta=None
        )

    with col5:
        total_products = len(filtered_df)
        st.metric(
            "📦 Total Products",
            f"{total_products:,}",
            delta=None
        )

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🏆 Top Products",
        "📈 Visualizations",
        "💎 Value Analysis",
        "📋 Data Explorer"
    ])

    # ============================ TAB 1: Overview ============================ #
    with tab1:
        st.markdown("## 📊 **Category Overview**")

        if selected_category == 'All Categories':
            category_summary = filtered_df.groupby('Category').agg({
                'Price': ['mean', 'count'],
                'Rating': 'mean',
                'ReviewCount': 'sum',
                'IsHighValue': 'sum'
            }).round(2)
            category_summary.columns = ['Avg Price', 'Product Count', 'Avg Rating', 'Total Reviews', 'High Value Count']
            category_summary = category_summary.sort_values('Product Count', ascending=False)

            st.markdown("### **Summary by Category**")
            st.dataframe(
                category_summary,
                use_container_width=True,
                height=300
            )

            col1_, col2_ = st.columns(2)

            with col1_:
                st.markdown("### **Average Price by Category**")
                fig, ax = plt.subplots(figsize=(10, 6))
                category_summary['Avg Price'].sort_values(ascending=True).plot(
                    kind='barh', ax=ax, color='steelblue'
                )
                ax.set_xlabel('Average Price ($)', fontweight='bold')
                ax.set_ylabel('Category', fontweight='bold')
                ax.set_title('Price Comparison', fontweight='bold', fontsize=14)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            with col2_:
                st.markdown("### **Average Rating by Category**")
                fig, ax = plt.subplots(figsize=(10, 6))
                category_summary['Avg Rating'].sort_values(ascending=True).plot(
                    kind='barh', ax=ax, color='coral'
                )
                ax.set_xlabel('Average Rating', fontweight='bold')
                ax.set_ylabel('Category', fontweight='bold')
                ax.set_title('Rating Comparison', fontweight='bold', fontsize=14)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
        else:
            st.markdown(f"### **{selected_category} Category Details**")

            col1_, col2_ = st.columns(2)
            with col1_:
                st.info(f"**Total Products:** {len(filtered_df)}")
                st.info(f"**Average Price:** ${filtered_df['Price'].mean():.2f}")
                st.info(f"**Average Rating:** {filtered_df['Rating'].mean():.2f}")
            with col2_:
                st.info(f"**Total Reviews:** {filtered_df['ReviewCount'].sum():,}")
                st.info(f"**High Value Products:** {int(filtered_df['IsHighValue'].sum())}")
                st.info(f"**Price Range:** ${filtered_df['Price'].min():.2f} - ${filtered_df['Price'].max():.2f}")

    # ========================== TAB 2: Top Products ========================== #
    with tab2:
        st.markdown("## 🏆 **Top Products**")

        col1_, col2_ = st.columns([2, 1])
        with col1_:
            sort_by = st.selectbox(
                "Sort by",
                ["ReviewCount", "Rating", "Price", "PricePerReview"],
                key="sort_option"
            )
        with col2_:
            top_n = st.number_input(
                "Number of products",
                min_value=5,
                max_value=100,
                value=20,
                step=5
            )

        if sort_by == "ReviewCount":
            top_products = filtered_df.nlargest(top_n, 'ReviewCount')
        elif sort_by == "Rating":
            top_products = filtered_df.nlargest(top_n, 'Rating')
        elif sort_by == "Price":
            top_products = filtered_df.nlargest(top_n, 'Price')
        else:
            top_products = filtered_df.nlargest(top_n, 'PricePerReview')

        display_cols = ['ProductName', 'Category', 'Price', 'Rating', 'ReviewCount', 'IsHighValue']
        if sort_by == "PricePerReview":
            display_cols.append('PricePerReview')

        st.markdown(f"### **Top {top_n} Products by {sort_by}**")
        st.dataframe(
            top_products[display_cols],
            use_container_width=True,
            height=400
        )

        csv = top_products[display_cols].to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"top_products_{sort_by}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # ========================= TAB 3: Visualizations ========================= #
    with tab3:
        st.markdown("## 📈 **Data Visualizations**")

        plots_dir = 'plots'
        if os.path.exists(plots_dir):
            st.markdown("### **Saved Analysis Charts**")

            plot_categories = {
                "Price Analysis": [
                    '1_avg_price_per_category.png',
                    '5_price_range_per_category.png'
                ],
                "Rating Analysis": [
                    '2_avg_rating_per_category.png'
                ],
                "Product Analysis": [
                    '3_product_count_per_category.png'
                ],
                "Top Products": [
                    f'4_top5_reviewed_{cat}.png' for cat in filtered_df['Category'].unique()
                ]
            }

            for category, plots in plot_categories.items():
                st.markdown(f"#### **{category}**")
                cols_ = st.columns(min(len(plots), 2))
                for idx, plot_file in enumerate(plots):
                    plot_path = os.path.join(plots_dir, plot_file)
                    if os.path.exists(plot_path):
                        with cols_[idx % len(cols_)]:
                            st.image(plot_path, use_container_width=True)

        st.markdown("### **Interactive Charts**")

        chart_type = st.selectbox(
            "Select Chart Type",
            ["Price vs Rating", "Review Count Distribution", "Price Distribution", "Category Comparison"],
            key="chart_type"
        )

        if chart_type == "Price vs Rating":
            fig, ax = plt.subplots(figsize=(12, 6))
            scatter = ax.scatter(
                filtered_df['Price'], filtered_df['Rating'],
                c=filtered_df['ReviewCount'], cmap='viridis',
                alpha=0.6, s=50
            )
            ax.set_xlabel('Price ($)', fontweight='bold', fontsize=12)
            ax.set_ylabel('Rating', fontweight='bold', fontsize=12)
            ax.set_title('Price vs Rating (Color = Review Count)', fontweight='bold', fontsize=14)
            plt.colorbar(scatter, ax=ax, label='Review Count')
            plt.grid(True, alpha=0.3)
            st.pyplot(fig)
            plt.close()

        elif chart_type == "Review Count Distribution":
            fig, ax = plt.subplots(figsize=(12, 6))
            filtered_df[filtered_df['ReviewCount'] > 0]['ReviewCount'].hist(
                bins=50, ax=ax, color='steelblue', edgecolor='black'
            )
            ax.set_xlabel('Review Count', fontweight='bold', fontsize=12)
            ax.set_ylabel('Frequency', fontweight='bold', fontsize=12)
            ax.set_title('Review Count Distribution', fontweight='bold', fontsize=14)
            plt.grid(True, alpha=0.3)
            st.pyplot(fig)
            plt.close()

        elif chart_type == "Price Distribution":
            fig, ax = plt.subplots(figsize=(12, 6))
            filtered_df['Price'].hist(
                bins=50, ax=ax, color='coral', edgecolor='black'
            )
            ax.set_xlabel('Price ($)', fontweight='bold', fontsize=12)
            ax.set_ylabel('Frequency', fontweight='bold', fontsize=12)
            ax.set_title('Price Distribution', fontweight='bold', fontsize=14)
            plt.grid(True, alpha=0.3)
            st.pyplot(fig)
            plt.close()

        else:  # Category Comparison
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

            category_stats = filtered_df.groupby('Category').agg({
                'Price': 'mean',
                'Rating': 'mean'
            })

            category_stats['Price'].plot(
                kind='bar', ax=ax1, color='steelblue', edgecolor='black'
            )
            ax1.set_title('Average Price by Category', fontweight='bold', fontsize=12)
            ax1.set_xlabel('Category', fontweight='bold')
            ax1.set_ylabel('Price ($)', fontweight='bold')
            ax1.tick_params(axis='x', rotation=45)

            category_stats['Rating'].plot(
                kind='bar', ax=ax2, color='coral', edgecolor='black'
            )
            ax2.set_title('Average Rating by Category', fontweight='bold', fontsize=12)
            ax2.set_xlabel('Category', fontweight='bold')
            ax2.set_ylabel('Rating', fontweight='bold')
            ax2.tick_params(axis='x', rotation=45)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    # ========================= TAB 4: Value Analysis ========================= #
    with tab4:
        st.markdown("## 💎 **Value Score Analysis**")
        st.markdown("Value Score = (Rating × ReviewCount) / Price")

        filtered_df['ValueScore'] = (
            filtered_df['Rating'] * filtered_df['ReviewCount']
        ) / filtered_df['Price'].replace(0, 1)
        filtered_df['ValueScore'] = filtered_df['ValueScore'].fillna(0)

        col1_, col2_ = st.columns(2)
        with col1_:
            st.metric("Average Value Score", f"{filtered_df['ValueScore'].mean():.2f}")
        with col2_:
            st.metric("Max Value Score", f"{filtered_df['ValueScore'].max():.2f}")

        top_value = filtered_df.nlargest(30, 'ValueScore')[
            ['ProductName', 'Category', 'Price', 'Rating', 'ReviewCount', 'ValueScore', 'IsHighValue']
        ]
        top_value['ValueScore'] = top_value['ValueScore'].round(2)
        top_value = top_value.rename(columns={'IsHighValue': 'High Value'})

        st.markdown("### **Top 30 Best Value Products**")
        st.dataframe(
            top_value,
            use_container_width=True,
            height=500
        )

        fig, ax = plt.subplots(figsize=(12, 6))
        top_value['ValueScore'].hist(
            bins=30, ax=ax, color='mediumseagreen', edgecolor='black'
        )
        ax.set_xlabel('Value Score', fontweight='bold', fontsize=12)
        ax.set_ylabel('Frequency', fontweight='bold', fontsize=12)
        ax.set_title('Value Score Distribution (Top 30)', fontweight='bold', fontsize=14)
        plt.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close()

    # ========================= TAB 5: Data Explorer ========================= #
    with tab5:
        st.markdown("## 📋 **Data Explorer**")

        st.markdown("### **Full Dataset**")
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400
        )

        st.markdown("### **Search Products**")
        search_term = st.text_input("Enter product name to search", key="search_input")

        if search_term:
            search_results = filtered_df[
                filtered_df['ProductName'].str.contains(search_term, case=False, na=False)
            ]
            st.markdown(f"**Found {len(search_results)} products**")
            st.dataframe(
                search_results[['ProductName', 'Category', 'Price', 'Rating', 'ReviewCount']],
                use_container_width=True
            )

if __name__ == "__main__":
    main()
