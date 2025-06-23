import pymupdf
import re
import hashlib
import datetime
import logging

def calculate_file_hash(file_bytes):
    """Calculate SHA256 hash of a file"""
    return hashlib.sha256(file_bytes).hexdigest()

def extract_text_from_pdf(file_bytes):
    """Extract text from PDF using PyMuPDF"""
    try:
        # Use PyMuPDF only
        pdf_document = pymupdf.open(stream=file_bytes, filetype="pdf")
        pdf_text = ""
        
        # Extract text from all pages
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            pdf_text += page.get_text()
            
        # Close the document to free resources
        pdf_document.close()
            
        return pdf_text
    except Exception as e:
        # No fallback - if PyMuPDF fails, return the error
        raise Exception(f"Failed to extract text with PyMuPDF: {str(e)}")

def extract_tables_from_pdf(file_bytes):
    """Extract tables from PDF using PyMuPDF"""
    try:
        # Open the PDF document
        pdf_document = pymupdf.open(stream=file_bytes, filetype="pdf")
        
        # Extract tables from all pages
        all_table_rows = []
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            try:
                table_search = page.find_tables()
                if table_search.tables:
                    for table in table_search.tables:
                        table_rows = table.extract()
                        if table_rows and len(table_rows) > 0 and "Areas Of Assessment" in str(table_rows[0]):
                            # Skip the first two rows (headers) and return the rest
                            all_table_rows.extend(table_rows[2:])
            except Exception as e:
                # Silently handle table extraction errors
                continue
        
        # Close the document to free resources
        pdf_document.close()
        
        return all_table_rows
    except Exception as e:
        # Log error but don't print to console
        return []

def extract_metadata_from_content(pdf_text):
    """Extract metadata from the PDF content"""
    metadata = {
        'year': None,
        'semester': None,
        'report_number': None
    }
    
    # Look for the combined pattern: "Semester X, YYYY - Progress Report Z"
    combined_pattern = r"Semester\s*(\d),?\s*(\d{4})\s*-\s*Progress\s*Report\s*(\d)"
    combined_match = re.search(combined_pattern, pdf_text, re.IGNORECASE)
    
    if combined_match:
        metadata['semester'] = combined_match.group(1)
        metadata['year'] = combined_match.group(2)
        metadata['report_number'] = combined_match.group(3)
        
        # Add full_period
        metadata['full_period'] = f"{metadata['year']} S{metadata['semester']} R{metadata['report_number']}"
        
        return metadata
    else:
        # If the combined pattern isn't found, return None to indicate this PDF should be ignored
        return None

def extract_performance_indicators_from_tables(table_rows):
    """Extract performance indicators from table rows"""
    very_good_count = 0
    good_count = 0
    needs_improvement_count = 0
    
    # Process each row in the table
    for row in table_rows:
        if not row or len(row) < 2:  # Skip rows that don't have enough columns
            continue
        
        # Each row represents a subject, and columns 1-5 contain assessment results
        # Skip the first column (subject name) and check columns 1-5
        for cell in row[1:]:  # Start from index 1 to skip the subject column
            cell_text = str(cell).lower().strip() if cell else ""
            
            # Count based on the cell content
            if "very good" in cell_text:
                very_good_count += 1
            elif "good (meets expectations)" in cell_text:
                good_count += 1
            elif any(term in cell_text for term in ["needs improvement", "improvement needed", "not consistently meeting expectation"]):
                needs_improvement_count += 1
    
    return {
        'Very Good': very_good_count,
        'Good': good_count,
        'Needs Improvement': needs_improvement_count
    }

def process_pdf(file_bytes, filename, existing_hashes=None):
    """
    Process a PDF file to extract metadata and performance indicators
    
    Args:
        file_bytes: The PDF file as bytes
        filename: The name of the PDF file
        existing_hashes: Set of existing file hashes to check for duplicates
        
    Returns:
        tuple: (result_dict, error_message)
    """
    # Calculate hash to check for duplicates
    file_hash = calculate_file_hash(file_bytes)
    
    # Check if file has already been uploaded
    if existing_hashes and file_hash in existing_hashes:
        return None, "This file has already been uploaded in this session."
    
    # Process PDF content
    try:
        # Extract full text for metadata
        pdf_text = extract_text_from_pdf(file_bytes)
        
        # Check if PDF text is empty
        if not pdf_text or pdf_text.isspace():
            return None, f"The PDF file '{filename}' appears to be empty or contains no extractable text."
        
        # Extract metadata from content
        metadata = extract_metadata_from_content(pdf_text)
        
        # If metadata extraction failed, ignore this PDF
        if metadata is None:
            return None, f"Could not find required metadata pattern in '{filename}'. PDF ignored."
        
        # Extract tables for performance indicators
        table_rows = extract_tables_from_pdf(file_bytes)
        
        if table_rows and len(table_rows) > 0:
            # Use table extraction for performance indicators
            performance = extract_performance_indicators_from_tables(table_rows)
        else:
            # If no tables were found, return an error
            return None, f"No assessment tables found in the PDF file '{filename}'."
        
        # Combine metadata and performance data
        result = {**metadata, **performance, 'file_hash': file_hash}
        return result, None
        
    except Exception as e:
        return None, f"Error processing PDF: {str(e)}" 