"""
PDF Parser for Prince George's County Daily Crime Reports

This module handles extraction of crime statistics from PDF reports using pdfplumber.
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dateutil import parser as date_parser
import pdfplumber

from config import DATE_PATTERNS, SKIP_EMPTY_ROWS, STRIP_WHITESPACE
from crime_categories import categorize, clean_records, is_junk_row

# Set up logging
logger = logging.getLogger(__name__)


def extract_date_from_header(text: str) -> Optional[str]:
    """
    Extract the report date from PDF header text.

    Args:
        text: Header text from PDF (typically first 500 characters)

    Returns:
        Date string in YYYY-MM-DD format, or None if not found
    """
    # Try each pattern
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            try:
                # Parse the date and return in standard format
                parsed_date = date_parser.parse(date_str)
                return parsed_date.strftime("%Y-%m-%d")
            except Exception as e:
                logger.warning(f"Failed to parse date '{date_str}': {e}")
                continue

    return None


def normalize_column_name(col_name: str, reference_year: Optional[int] = None) -> str:
    """
    Normalize column names to be machine-readable (lowercase with underscores).
    Also converts date column names from "Monday 2/2" format to ISO date format "YYYY-MM-DD".
    
    Args:
        col_name: Column name from the PDF table
        reference_year: Year to use for date conversion (defaults to current year)
    
    Returns:
        Normalized column name
    """
    if not reference_year:
        reference_year = datetime.now().year
    
    # Pattern to match "DayOfWeek M/D" format
    date_pattern = r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})/(\d{1,2})'
    match = re.search(date_pattern, col_name, re.IGNORECASE)
    
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        try:
            date_obj = datetime(reference_year, month, day)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            logger.warning(f"Invalid date in column name: {col_name}")
    
    # Normalize other common column names
    normalized = col_name.lower().strip()
    
    # Check for Prev. 7 pattern (with any date range)
    if normalized.startswith('prev. 7'):
        return 'prev_seven_day_total'
    
    # Map specific column names
    column_mapping = {
        '7-day totals': 'seven_day_total',
        '+/-': 'change',
        '% change': 'percent_change',
    }
    
    # Check for YTD patterns
    ytd_pattern = r'ytd\s+(\d{2})\s+'
    ytd_match = re.search(ytd_pattern, normalized)
    if ytd_match:
        year = ytd_match.group(1)
        return f'ytd_20{year}'
    
    # Check if in mapping
    if normalized in column_mapping:
        return column_mapping[normalized]
    
    # Default: replace spaces and special chars with underscores
    normalized = re.sub(r'[^\w\s-]', '', normalized)
    normalized = re.sub(r'[-\s]+', '_', normalized)
    
    return normalized


def parse_crime_table(table: List[List[str]], report_year: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Parse a crime statistics table into structured data.

    Args:
        table: Raw table data from pdfplumber
        report_year: Year of the report for date normalization

    Returns:
        List of dictionaries containing parsed crime statistics
    """
    if not table or len(table) < 2:
        return []

    # Extract header row (usually row 1)
    header = table[1] if len(table) > 1 else table[0]

    # Parse header to get column names and normalize dates
    columns = []
    for col in header:
        if col:
            # Clean up column names
            col_clean = col.replace('\n', ' ').strip()
            # Normalize column names (dates and other fields)
            col_normalized = normalize_column_name(col_clean, report_year)
            columns.append(col_normalized)
        else:
            columns.append('')

    # The table has two "+/-" and two "% Change" columns: the pair before the
    # YTD columns compares 7-day totals week-over-week, the pair after them
    # compares YTD years. Disambiguate so the second pair doesn't overwrite
    # the first when the row is stored as a dict.
    seen_ytd = False
    for i, col in enumerate(columns):
        if col.startswith('ytd_'):
            seen_ytd = True
        elif col == 'change':
            columns[i] = 'ytd_change' if seen_ytd else 'weekly_change'
        elif col == 'percent_change':
            columns[i] = 'ytd_percent_change' if seen_ytd else 'weekly_percent_change'

    # Parse data rows (skip first 2 rows: title and header)
    records = []
    for row in table[2:]:
        if not row or all(cell is None or str(cell).strip() == '' for cell in row):
            if SKIP_EMPTY_ROWS:
                continue

        # Create record dictionary
        record = {}
        offense_type = row[0] if row else None

        if not offense_type or offense_type.strip() == '':
            continue

        if STRIP_WHITESPACE:
            offense_type = offense_type.strip()

        # The PDF repeats its section-header row mid-table; skip it
        if is_junk_row(offense_type):
            continue

        record['offense_type'] = offense_type

        # Map remaining columns
        for i, value in enumerate(row[1:], start=1):
            if i < len(columns):
                col_name = columns[i]
                if col_name:
                    # Convert to appropriate type
                    if value is not None:
                        value_str = str(value).strip() if STRIP_WHITESPACE else str(value)
                        
                        # Handle percent change fields specially
                        if col_name.endswith('percent_change') and value_str:
                            # Strip +/- and % to get numeric value
                            numeric_str = value_str.replace('+', '').replace('%', '').strip()
                            try:
                                value = float(numeric_str)
                            except ValueError:
                                # Keep original if conversion fails
                                pass
                        # Try to convert to int for other numeric fields
                        elif value_str.lstrip('+-').isdigit():
                            try:
                                value = int(value_str)
                            except ValueError:
                                pass
                    record[col_name] = value

        records.append(record)

    return records


def calculate_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics from parsed records.

    Args:
        records: List of parsed crime records

    Returns:
        Dictionary containing summary statistics
    """
    summary = {
        'total_offense_types': len(records),
        'violent_crimes': [],
        'property_crimes': [],
        'total_rows': [],
        'other': [],
    }

    category_keys = {
        'violent': 'violent_crimes',
        'property': 'property_crimes',
        'total': 'total_rows',
        'other': 'other',
    }

    for record in records:
        offense_type = record.get('offense_type', '')
        summary[category_keys[categorize(offense_type)]].append(offense_type)

    summary['violent_crime_count'] = len(summary['violent_crimes'])
    summary['property_crime_count'] = len(summary['property_crimes'])

    return summary


def parse_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Main function to parse Prince George's County crime report PDF.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary containing all parsed data
    """
    logger.info(f"Starting to parse PDF: {pdf_path}")

    result = {
        'report_date': None,
        'extracted_date_text': None,
        'download_timestamp': datetime.utcnow().isoformat() + 'Z',
        'source_file': pdf_path,
        'crime_statistics': [],
        'summary': {},
        'parse_errors': []
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            logger.info(f"PDF has {len(pdf.pages)} page(s)")

            # Extract date from first page header
            if pdf.pages:
                first_page = pdf.pages[0]
                header_text = first_page.extract_text()[:500]

                # Extract date
                report_date = extract_date_from_header(header_text)
                if report_date:
                    result['report_date'] = report_date
                    logger.info(f"Extracted report date: {report_date}")
                else:
                    logger.warning("Could not extract report date from PDF header")
                    result['parse_errors'].append("Could not extract report date")

                # Store raw extracted text for reference
                result['extracted_date_text'] = header_text.split('\n')[2] if '\n' in header_text else None

            # Extract tables from all pages
            all_records = []
            report_year = None
            if result['report_date']:
                try:
                    report_year = datetime.strptime(result['report_date'], "%Y-%m-%d").year
                except ValueError:
                    pass
            
            for page_num, page in enumerate(pdf.pages, start=1):
                logger.info(f"Processing page {page_num}")
                tables = page.extract_tables()

                for table_num, table in enumerate(tables, start=1):
                    logger.info(f"Parsing table {table_num} on page {page_num}")
                    try:
                        records = parse_crime_table(table, report_year)
                        all_records.extend(records)
                        logger.info(f"Extracted {len(records)} records from table {table_num}")
                    except Exception as e:
                        error_msg = f"Error parsing table {table_num} on page {page_num}: {e}"
                        logger.error(error_msg)
                        result['parse_errors'].append(error_msg)

            # Drop artifact rows and the duplicated "Violent Crime Total"
            all_records = clean_records(all_records)

            result['crime_statistics'] = all_records
            result['summary'] = calculate_summary(all_records)

            logger.info(f"Successfully parsed {len(all_records)} crime statistics records")

    except Exception as e:
        error_msg = f"Failed to parse PDF: {e}"
        logger.error(error_msg)
        result['parse_errors'].append(error_msg)
        raise

    # Archiving/renaming the PDF is the caller's job (download_crime_report.py
    # moves it into data/pdf/). Moving it here used to resolve data/pdf
    # relative to the temp download path, stranding archived PDFs in /tmp on
    # CI runners and breaking the caller's own archive step.
    if result['report_date']:
        result['source_file'] = result['report_date'].replace('-', '') + '.pdf'
    else:
        result['source_file'] = os.path.basename(pdf_path)

    return result


if __name__ == "__main__":
    # Set up basic logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test with a sample PDF
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        result = parse_pdf(pdf_path)

        # Pretty print result
        import json
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python parse_crime_pdf.py <path_to_pdf>")
