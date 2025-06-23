import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from collections import defaultdict
import time

# Import our PDF processor module
import pdf_processor

# Set page configuration
st.set_page_config(
    page_title="School Reports Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
    }
    .footer {
        font-size: 0.8rem;
        color: #9e9e9e;
        text-align: center;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB limit per file
MAX_FILES = 30  # Maximum number of files to process

# Initialize session state variables if they don't exist
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'file_hashes' not in st.session_state:
    st.session_state.file_hashes = set()
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = []
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = int(time.time())

def generate_charts(data_df):
    """Generate charts based on the extracted data"""
    if data_df.empty:
        return
    
    # Convert year, semester, and report_number to numeric for proper sorting
    data_df['year'] = pd.to_numeric(data_df['year'])
    data_df['semester'] = pd.to_numeric(data_df['semester'])
    data_df['report_number'] = pd.to_numeric(data_df['report_number'])
    
    # Sort DataFrame by year, semester, and report_number
    data_df = data_df.sort_values(by=['year', 'semester', 'report_number'])
    
    # Create a column with period labels for x-axis
    data_df['period_label'] = data_df.apply(
        lambda row: f"{row['year']} S{row['semester']} R{row['report_number']}", 
        axis=1
    )
    
    # Create tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["Performance Trends", "Comparison by Period", "Data Table"])
    
    with tab1:
        st.markdown('<div class="sub-header">Performance Indicator Trends Over Time</div>', unsafe_allow_html=True)
        
        # Melt the DataFrame to create a format suitable for line chart
        melted_df = pd.melt(
            data_df, 
            id_vars=['period_label'], 
            value_vars=['Very Good', 'Good', 'Needs Improvement'],
            var_name='Indicator', 
            value_name='Count'
        )
        
        # Create line chart with Plotly
        fig = px.line(
            melted_df, 
            x='period_label', 
            y='Count', 
            color='Indicator',
            markers=True,
            title="Performance Indicators Over Time",
            labels={'period_label': 'Reporting Period', 'Count': 'Number of Occurrences'},
            color_discrete_map={
                'Very Good': '#4CAF50',
                'Good': '#2196F3',
                'Needs Improvement': '#FF9800'
            }
        )
        
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(tickangle=45)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add a summary section
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### Summary of Trends")
        
        # Calculate trend information
        if len(data_df) > 1:
            first_report = data_df.iloc[0]
            last_report = data_df.iloc[-1]
            
            vg_change = last_report['Very Good'] - first_report['Very Good']
            g_change = last_report['Good'] - first_report['Good']
            ni_change = last_report['Needs Improvement'] - first_report['Needs Improvement']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Very Good", int(last_report['Very Good']), int(vg_change))
            
            with col2:
                st.metric("Good", int(last_report['Good']), int(g_change))
                
            with col3:
                st.metric("Needs Improvement", int(last_report['Needs Improvement']), int(ni_change * -1))  # Invert for better visualization
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="sub-header">Performance Indicators by Reporting Period</div>', unsafe_allow_html=True)
        
        # Create a grouped bar chart
        fig = px.bar(
            data_df,
            x='period_label',
            y=['Very Good', 'Good', 'Needs Improvement'],
            title="Performance Indicators by Reporting Period",
            labels={'period_label': 'Reporting Period', 'value': 'Count', 'variable': 'Indicator'},
            barmode='group',
            color_discrete_map={
                'Very Good': '#4CAF50',
                'Good': '#2196F3',
                'Needs Improvement': '#FF9800'
            }
        )
        
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(tickangle=45)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add a stacked percentage chart
        st.markdown('<div class="sub-header">Relative Distribution of Performance Indicators</div>', unsafe_allow_html=True)
        
        # Calculate percentages
        data_df_pct = data_df.copy()
        # Convert columns to float type before performing percentage calculations
        data_df_pct[['Very Good', 'Good', 'Needs Improvement']] = data_df_pct[['Very Good', 'Good', 'Needs Improvement']].astype(float)
        
        for idx, row in data_df_pct.iterrows():
            total = row['Very Good'] + row['Good'] + row['Needs Improvement']
            if total > 0:
                data_df_pct.at[idx, 'Very Good'] = row['Very Good'] / total * 100
                data_df_pct.at[idx, 'Good'] = row['Good'] / total * 100
                data_df_pct.at[idx, 'Needs Improvement'] = row['Needs Improvement'] / total * 100
        
        # Create stacked percentage bar chart
        fig = px.bar(
            data_df_pct,
            x='period_label',
            y=['Very Good', 'Good', 'Needs Improvement'],
            title="Percentage Distribution of Performance Indicators",
            labels={'period_label': 'Reporting Period', 'value': 'Percentage', 'variable': 'Indicator'},
            barmode='stack',
            color_discrete_map={
                'Very Good': '#4CAF50',
                'Good': '#2196F3',
                'Needs Improvement': '#FF9800'
            }
        )
        
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(tickangle=45),
            yaxis=dict(ticksuffix="%")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown('<div class="sub-header">Raw Data</div>', unsafe_allow_html=True)
        
        # Add download button for CSV
        csv = data_df.to_csv(index=False)
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name="school_reports_data.csv",
            mime="text/csv",
        )
        
        # Show raw data
        st.dataframe(
            data_df[['year', 'semester', 'report_number', 'period_label', 'Very Good', 'Good', 'Needs Improvement']],
            use_container_width=True
        )
        
        # Add debug information
        with st.expander("Debug Information"):
            st.write("Raw Performance Indicator Counts:")
            for idx, row in data_df.iterrows():
                st.write(f"File {idx+1}: Very Good: {row['Very Good']}, Good: {row['Good']}, Needs Improvement: {row['Needs Improvement']}")

def main():
    """Main application function"""
    st.markdown('<div class="main-header">School Reports Analytics</div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/school.png", width=100)
        st.markdown("## About")
        st.markdown("""
        This application analyzes school reports to track performance trends over time.
        
        **Privacy Features:**
        - No personal data is stored
        - All processing is in-memory
        - Data is cleared when session ends
        """)
        
        st.markdown("---")
        st.markdown("## How to Use")
        st.markdown("""
        1. Upload one or more school report PDFs
        2. View the generated charts
        3. Download data as CSV if needed
        
        **Supported Files:**
        PDF files containing school progress reports with performance indicators.
        """)
        
        # Add a button to clear session data
        if st.button("Clear All Data"):
            st.session_state.uploaded_files = []
            st.session_state.file_hashes = set()
            st.session_state.extracted_data = []
            # Generate a new key for the file uploader to force it to reset
            st.session_state.uploader_key = int(time.time())
            st.rerun()
    
    st.markdown("""
    This application analyzes school reports to track performance trends over time.
    Upload one or more school report PDFs to get started.
    
    **Privacy Note:** No personal data is stored or processed. All analysis is done in-memory during your session.
    """)
    
    # File uploader with size and count limits - use the dynamic key from session state
    uploaded_files = st.file_uploader(
        "Upload School Report PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"pdf_uploader_{st.session_state.uploader_key}",
        help=f"Upload one or more school report PDFs (max {MAX_FILES} files, {MAX_FILE_SIZE/1024/1024:.1f}MB each)."
    )
    
    if uploaded_files:
        # Check file count
        if len(uploaded_files) > MAX_FILES:
            st.warning(f"You've uploaded {len(uploaded_files)} files, but only the first {MAX_FILES} will be processed due to resource limitations.")
            uploaded_files = uploaded_files[:MAX_FILES]
        
        with st.spinner("Processing PDF files..."):
            # Process each uploaded file
            for uploaded_file in uploaded_files:
                # Skip if file has already been processed
                if uploaded_file.name in [f.name for f in st.session_state.uploaded_files]:
                    continue
                
                # Check file size
                if uploaded_file.size > MAX_FILE_SIZE:
                    st.error(f"File '{uploaded_file.name}' exceeds the maximum size limit of {MAX_FILE_SIZE/1024/1024:.1f}MB.")
                    continue
                
                # Process the PDF
                try:
                    file_bytes = uploaded_file.getvalue()
                    result, error = pdf_processor.process_pdf(
                        file_bytes, 
                        uploaded_file.name,
                        st.session_state.file_hashes
                    )
                    
                    if error:
                        st.error(error)
                    else:
                        # Add to session state
                        st.session_state.uploaded_files.append(uploaded_file)
                        st.session_state.file_hashes.add(result['file_hash'])
                        st.session_state.extracted_data.append(result)
                        
                        # Clear memory
                        del file_bytes
                except Exception as e:
                    st.error(f"Error processing '{uploaded_file.name}': {str(e)}")
        
        # Display success message
        if st.session_state.extracted_data:
            st.success(f"Successfully processed {len(st.session_state.uploaded_files)} files.")
            
            # Convert data to DataFrame
            data_df = pd.DataFrame(st.session_state.extracted_data)
            
            # Generate charts
            generate_charts(data_df)
    
    # Add footer
    st.markdown('<div class="footer">School Reports Analytics - Privacy-Focused Analysis Tool</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 