# app.py - Streamlit Dashboard for FY26 Performance
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# --- Page Configuration ---
st.set_page_config(
    page_title="FY26 Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c3c 0%, #2F4F4F 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .status-on-track {
        background-color: #006400;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-at-risk {
        background-color: #FFA500;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-behind {
        background-color: #8B0000;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    /* Center align table headers and data */
    .dataframe th {
        text-align: center !important;
        background-color: #2F4F4F !important;
        color: white !important;
        font-weight: bold !important;
    }
    .dataframe td {
        text-align: center !important;
    }
    /* Table container styling */
    .table-container {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    /* Section headers */
    .section-header {
        color: #2F4F4F;
        border-bottom: 2px solid #2F4F4F;
        padding-bottom: 5px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)


# --- Fiscal Month Order ---
FISCAL_MONTH_ORDER = [
    'Dec-25', 'Jan-26', 'Feb-26', 'Mar-26', 'Apr-26', 'May-26',
    'Jun-26', 'Jul-26', 'Aug-26', 'Sep-26', 'Oct-26', 'Nov-26'
]

def get_fiscal_month_order():
    """Return month order for sorting"""
    return {month: i for i, month in enumerate(FISCAL_MONTH_ORDER)}


# --- Helper Functions ---
def style_achievement_3level(value):
    """3-level gradient for achievement percentages - centered, bold, bright colors"""
    if isinstance(value, (int, float)):
        if value >= 1.0:
            # Bright green - on track
            return 'color: #00B050; font-weight: bold; text-align: center'
        elif value >= 0.75:
            # Bright orange - at risk
            return 'color: #FF6600; font-weight: bold; text-align: center'
        else:
            # Bright red - behind
            return 'color: #FF0000; font-weight: bold; text-align: center'
    return 'text-align: center'


def style_ytg_3level(value):
    """3-level gradient for YTG percentages - centered, bold, bright colors"""
    if isinstance(value, (int, float)):
        # For YTG%, lower is better (less remaining)
        if value <= 0.25:  # <= 25% remaining = good (bright green)
            return 'color: #00B050; font-weight: bold; text-align: center'
        elif value <= 0.50:  # <= 50% remaining = medium (bright orange)
            return 'color: #FF6600; font-weight: bold; text-align: center'
        else:  # > 50% remaining = at risk (bright red)
            return 'color: #FF0000; font-weight: bold; text-align: center'
    return 'text-align: center'


def style_general(value):
    """General styling for centered text"""
    return 'text-align: center'


# --- Load Data ---
@st.cache_data(ttl=86400)  # Cache for 24 hours
def load_dashboard_data():
    """Load pre-processed data from Excel file"""
    try:
        monthly_details = pd.read_excel('fy26_dashboard_data.xlsx', sheet_name='Monthly_Details')
        category_summary = pd.read_excel('fy26_dashboard_data.xlsx', sheet_name='Category_Summary')
        metadata = pd.read_excel('fy26_dashboard_data.xlsx', sheet_name='Metadata')

        # Ensure proper data types
        numeric_cols = ['TARGET', 'Monthly Ach', 'Monthly Ach %', 'MTG', 'MTG%', 'YTG', 'YTG%', 'YoY %XG']
        for col in numeric_cols:
            if col in monthly_details.columns:
                monthly_details[col] = pd.to_numeric(monthly_details[col], errors='coerce')

        # Sort monthly data by fiscal month order
        month_order = get_fiscal_month_order()
        monthly_details['MonthOrder'] = monthly_details['MonthName'].map(month_order)
        monthly_details = monthly_details.sort_values(['CATEGORY', 'MonthOrder']).drop(columns=['MonthOrder'])

        return monthly_details, category_summary, metadata

    except FileNotFoundError:
        return None, None, None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None, None


# --- Helper Functions ---
def create_performance_chart(summary_df):
    """Create interactive performance chart"""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=summary_df['CATEGORY'],
        y=summary_df['YTD Achievement %'],
        name='YTD Achievement',
        text=summary_df['YTD Achievement %'].apply(lambda x: f'{x:.1%}'),
        textposition='auto',
        marker_color=['#00B050' if x >= 1 else '#FF6600' if x >= 0.75 else '#FF0000'
                      for x in summary_df['YTD Achievement %']]
    ))
    fig.update_layout(
        title='YTD Achievement by Category',
        yaxis_title='Achievement %',
        yaxis_tickformat='.0%',
        height=400,
        showlegend=False
    )
    return fig


def create_monthly_trend_chart(monthly_df, categories):
    """Create monthly trend chart"""
    fig = go.Figure()
    for category in categories:
        cat_data = monthly_df[monthly_df['CATEGORY'] == category]
        fig.add_trace(go.Scatter(
            x=cat_data['MonthName'],
            y=cat_data['Monthly Ach %'],
            name=category,
            mode='lines+markers',
            line=dict(width=2),
            marker=dict(size=8)
        ))

    # Add target line
    fig.add_hline(y=1.0, line_dash="dash", line_color="gray",
                  annotation_text="Target (100%)")
    fig.update_layout(
        title='Monthly Achievement Trend',
        xaxis_title='Month',
        yaxis_title='Achievement %',
        yaxis_tickformat='.0%',
        height=400,
        hovermode='x unified'
    )
    return fig


# --- Main App ---
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 FY26 Performance Dashboard</h1>
        <p>Real-time tracking of category performance against targets</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("## 🔧 Dashboard Controls")

        # File upload section
        st.markdown("### 📁 Update Data")
        uploaded_file = st.file_uploader(
            "Upload new data file",
            type=['xlsx'],
            help="Upload an updated Excel file to refresh the dashboard"
        )

        if uploaded_file is not None:
            with open('fy26_dashboard_data.xlsx', 'wb') as f:
                f.write(uploaded_file.getbuffer())
            st.success("✅ Data updated! Refreshing...")
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")

        # Load data
        monthly_df, summary_df, metadata = load_dashboard_data()

        if monthly_df is not None:
            # Filters
            st.markdown("### 🎯 Filters")
            categories = monthly_df['CATEGORY'].unique()

            # Multi category selection - select ALL by default
            selected_categories = st.multiselect(
                "Select Categories",
                options=categories,
                default=list(categories),  # All categories selected by default
                help="Filter data by category"
            )

            # Month range filter (multiselect for multiple months)
            months = monthly_df['MonthName'].unique()
            # Sort months in fiscal order
            sorted_months = sorted(months, key=lambda x: get_fiscal_month_order().get(x, 999))
            selected_months = st.multiselect(
                "Select Months",
                options=sorted_months,
                default=sorted_months,
                help="Filter data by month range"
            )

            st.markdown("---")

            # Data info
            if metadata is not None and len(metadata) > 0:
                st.markdown("### ℹ️ Data Information")
                st.markdown(f"**Generated:** {metadata['generated_date'].iloc[0]}")
                st.markdown(f"**Fiscal Year:** {metadata['fiscal_year'].iloc[0]}")
                st.markdown(f"**Categories:** {metadata['total_categories'].iloc[0]}")
                st.markdown(
                    f"**Data Version:** {metadata['data_version'].iloc[0] if 'data_version' in metadata.columns else '1.0'}")

            st.markdown("---")

            # Help section
            with st.expander("📊 Metrics Explained"):
                st.markdown("""
                - **MTG (Monthly Target Gap):** Difference between target and actual
                  - *Positive* = Still need to achieve
                  - *Negative* = Target exceeded
                - **YTG (Year-to-Go):** Remaining budget to achieve
                - **ACH%:** Achievement percentage vs monthly target
                - **YoY:** Year-over-Year growth vs previous year
                """)

            # Store in session state for use in main content
            st.session_state.monthly_df = monthly_df
            st.session_state.summary_df = summary_df
            st.session_state.selected_categories = selected_categories
            st.session_state.selected_months = selected_months
        else:
            st.session_state.monthly_df = None
            st.session_state.summary_df = None

    # Main content area
    if hasattr(st.session_state, 'monthly_df') and st.session_state.monthly_df is not None:
        monthly_df = st.session_state.monthly_df
        summary_df = st.session_state.summary_df
        selected_categories = st.session_state.selected_categories
        selected_months = st.session_state.selected_months

        # Filter data for multiple categories
        filtered_monthly = monthly_df[
            (monthly_df['CATEGORY'].isin(selected_categories)) &
            (monthly_df['MonthName'].isin(selected_months))
        ]
        filtered_summary = summary_df[summary_df['CATEGORY'].isin(selected_categories)]

        # KPI Cards - 5 columns for better insight
        st.markdown("## 📈 Key Performance Indicators")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            total_budget = filtered_summary['Annual Budget'].sum()
            st.metric(
                "💰 Annual Budget",
                f"${total_budget:,.0f}",
                help="Total annual budget for selected categories"
            )

        with col2:
            total_achieved = filtered_summary['Cumulative ACH'].sum()
            st.metric(
                "✅ Achieved",
                f"${total_achieved:,.0f}",
                help="Cumulative achievement to date"
            )

        with col3:
            overall_ach = (total_achieved / total_budget) if total_budget > 0 else 0
            st.metric(
                "📈 Achievement",
                f"{overall_ach:.1%}",
                help="Percentage of annual budget achieved"
            )

        with col4:
            total_remaining = filtered_summary['Remaining YTG'].sum()
            st.metric(
                "🎯 Remaining",
                f"${total_remaining:,.0f}",
                help="Year-to-Go remaining budget"
            )

        with col5:
            # Year-over-Year Analysis Card
            avg_yoy = filtered_summary['YTD YoY Growth'].mean()
            if avg_yoy > 0:
                last_year_val = total_achieved / (1 + avg_yoy)
            else:
                last_year_val = total_achieved * (1 - abs(avg_yoy))
            variance = total_achieved - last_year_val

            # Display all 3 values: Current, Last Year, Variance
            st.metric(
                "📊 YoY Growth",
                f"{avg_yoy:+.1%}",
                delta=f"+${variance:,.0f}" if variance >= 0 else f"-${abs(variance):,.0f}",
                help=f"Current: ${total_achieved:,.0f} | Last Year: ${last_year_val:,.0f} | Variance: ${variance:,.0f}"
            )

        st.markdown("---")

        # Charts Section
        st.markdown("## 📊 Performance Analytics")
        col1, col2 = st.columns(2)

        with col1:
            if len(filtered_summary) > 0:
                fig1 = create_performance_chart(filtered_summary)
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No data available for the selected filters")

        with col2:
            if len(filtered_monthly) > 0:
                fig2 = create_monthly_trend_chart(filtered_monthly, selected_categories)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No data available for the selected filters")

        # Category Performance Table
        st.markdown("## 📋 Category Performance Summary")

        styled_summary = filtered_summary.style.format({
            'Annual Budget': '${:,.0f}',
            'Cumulative Target': '${:,.0f}',
            'Cumulative ACH': '${:,.0f}',
            'YTD Achievement %': '{:.1%}',
            'YTD Target Attainment %': '{:.1%}',
            'Remaining YTG': '${:,.0f}',
            'Remaining YTG %': '{:.1%}',
            'Avg Monthly ACH %': '{:.1%}',
            'YTD YoY Growth': '{:.1%}'
        }).map(style_achievement_3level, subset=['YTD Achievement %', 'YTD Target Attainment %', 'Avg Monthly ACH %'])\
         .map(style_ytg_3level, subset=['Remaining YTG %'])\
         .map(style_general, subset=['Annual Budget', 'Cumulative Target', 'Cumulative ACH', 'Remaining YTG', 'YTD YoY Growth'])\
         .set_properties(**{'text-align': 'center'})\
         .set_table_styles([
            {'selector': 'th', 'props': [('text-align', 'center'), ('background-color', '#2F4F4F'), ('color', 'white'), ('font-weight', 'bold')]},
            {'selector': 'td', 'props': [('text-align', 'center')]}
         ])
        st.dataframe(styled_summary, use_container_width=True, height=300)

        # Monthly Details Section
        st.markdown("## 📅 Monthly Performance Details")

        view_option = st.radio(
            "Select View:",
            ["Summary View", "Detailed View"],
            horizontal=True
        )

        if view_option == "Summary View":
            # Sort months properly for pivot table
            pivot_table = filtered_monthly.pivot_table(
                index='CATEGORY',
                columns='MonthName',
                values='Monthly Ach %',
                aggfunc='first'
            )
            # Reorder columns by fiscal month order - ensure proper sorting
            sorted_columns = sorted(pivot_table.columns, key=lambda x: get_fiscal_month_order().get(x, 999))
            pivot_table = pivot_table[sorted_columns]

            # Apply styling with 3-level gradient and centered text
            st.dataframe(
                pivot_table.style.format('{:.0%}')\
                    .map(style_achievement_3level)\
                    .set_properties(**{'text-align': 'center'})\
                    .set_table_styles([
                        {'selector': 'th', 'props': [('text-align', 'center'), ('background-color', '#2F4F4F'), ('color', 'white'), ('font-weight', 'bold')]},
                        {'selector': 'td', 'props': [('text-align', 'center')]}
                    ]),
                use_container_width=True
            )

        else:
            # Enhanced Detailed View - More appealing layout
            st.markdown("##### 📊 Monthly Performance Breakdown")

            # Create a styled detailed table with all metrics
            display_cols = ['CATEGORY', 'MonthName', 'TARGET', 'Monthly Ach', 'Monthly Ach %', 'MTG', 'MTG%', 'YTG', 'YTG%', 'YoY %XG']

            # Sort by fiscal month order for detailed view
            detailed_df = filtered_monthly[display_cols].copy()
            detailed_df = detailed_df.sort_values(['CATEGORY', 'MonthName'], key=lambda x: x.map(lambda v: get_fiscal_month_order().get(v, 999)) if x.name == 'MonthName' else x)

            # Create enhanced styled dataframe
            styled_monthly = detailed_df.style.format({
                'TARGET': '${:,.0f}',
                'Monthly Ach': '${:,.0f}',
                'Monthly Ach %': '{:.1%}',
                'MTG': '${:,.0f}',
                'MTG%': '{:.1%}',
                'YTG': '${:,.0f}',
                'YTG%': '{:.1%}',
                'YoY %XG': '{:.1%}'
            }).map(style_achievement_3level, subset=['Monthly Ach %'])\
             .map(style_ytg_3level, subset=['YTG%', 'MTG%'])\
             .map(style_general, subset=['CATEGORY', 'TARGET', 'Monthly Ach', 'MTG', 'YTG', 'YoY %XG'])\
             .set_properties(**{'text-align': 'center'})\
             .set_table_styles([
                {'selector': 'th', 'props': [('text-align', 'center'), ('background-color', '#2F4F4F'), ('color', 'white'), ('font-weight', 'bold'), ('font-size', '12px')]},
                {'selector': 'td', 'props': [('text-align', 'center'), ('font-size', '11px')]},
                {'selector': 'tr:hover', 'props': [('background-color', '#f5f5f5')]}
             ])

            st.dataframe(styled_monthly, use_container_width=True, height=400)

            # Additional metrics cards for detailed view
            st.markdown("##### 📈 Quick Stats")
            stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns(5)

            with stat_col1:
                avg_ach = detailed_df['Monthly Ach %'].mean()
                st.metric("Avg ACH%", f"{avg_ach:.1%}", help="Average monthly achievement")

            with stat_col2:
                max_ach = detailed_df['Monthly Ach %'].max()
                st.metric("Best Month", f"{max_ach:.1%}", help="Highest monthly achievement")

            with stat_col3:
                min_ach = detailed_df['Monthly Ach %'].min()
                st.metric("Lowest Month", f"{min_ach:.1%}", help="Lowest monthly achievement")

            with stat_col4:
                total_target = detailed_df['TARGET'].sum()
                st.metric("Total Target", f"${total_target:,.0f}", help="Sum of monthly targets")

            with stat_col5:
                total_ach = detailed_df['Monthly Ach'].sum()
                st.metric("Total Achieved", f"${total_ach:,.0f}", help="Sum of monthly achievements")

        # Download Section
        st.markdown("---")
        st.markdown("## 📥 Export Reports")
        col1, col2, col3 = st.columns(3)

        with col1:
            summary_csv = filtered_summary.to_csv(index=False)
            st.download_button(
                label="📊 Download Summary CSV",
                data=summary_csv,
                file_name=f"FY26_Summary_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            monthly_csv = filtered_monthly.to_csv(index=False)
            st.download_button(
                label="📅 Download Monthly CSV",
                data=monthly_csv,
                file_name=f"FY26_Monthly_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col3:
            import io
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                filtered_summary.to_excel(writer, sheet_name='Summary', index=False)
                filtered_monthly.to_excel(writer, sheet_name='Monthly_Details', index=False)
            excel_buffer.seek(0)
            st.download_button(
                label="📑 Download Excel Report",
                data=excel_buffer,
                file_name=f"FY26_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        # Footer
        st.markdown("---")
        st.markdown(
            f"<p style='text-align: center; color: gray; font-size: 12px;'>"
            f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Data source: Local SQL Server | Dashboard version 1.0"
            f"</p>",
            unsafe_allow_html=True
        )

    else:
        st.info("""
        ### 🚀 Getting Started
        Upload your `fy26_dashboard_data.xlsx` file using the sidebar to load the dashboard.
        The file should contain three sheets: **Monthly_Details**, **Category_Summary**, and **Metadata**.
        """)


if __name__ == "__main__":
    main()