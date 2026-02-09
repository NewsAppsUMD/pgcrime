"""
Main script to download and parse Prince George's County Daily Crime Reports

This script:
1. Downloads the PDF from the county website
2. Parses it using pdfplumber
3. Saves the structured data as JSON
4. Archives the PDF file
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from config import (
    PDF_URL,
    JSON_OUTPUT_DIR,
    PDF_ARCHIVE_DIR,
    LOG_FILE,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    LOG_LEVEL,
    MAX_RETRIES,
    RETRY_DELAY,
    REQUEST_TIMEOUT,
    REQUEST_HEADERS,
)
from parse_crime_pdf import parse_pdf

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def download_pdf(url: str, output_path: Path, max_retries: int = MAX_RETRIES) -> bool:
    """
    Download PDF from URL with retry logic.

    Args:
        url: URL to download from
        output_path: Where to save the PDF
        max_retries: Maximum number of retry attempts

    Returns:
        True if successful, False otherwise
    """
    headers = REQUEST_HEADERS.copy()

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Downloading PDF from {url} (attempt {attempt}/{max_retries})")

            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            # Check if response is actually a PDF
            content_type = response.headers.get('Content-Type', '').lower()
            if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
                logger.warning(f"Response content type is {content_type}, may not be a PDF")

            # Save the PDF
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Successfully downloaded PDF to {output_path} ({len(response.content)} bytes)")
            return True

        except requests.RequestException as e:
            logger.error(f"Download attempt {attempt} failed: {e}")

            if attempt < max_retries:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed to download PDF after {max_retries} attempts")
                return False

    return False


def save_json(data: dict, output_path: Path) -> bool:
    """
    Save parsed data as JSON file.

    Args:
        data: Dictionary to save
        output_path: Where to save the JSON

    Returns:
        True if successful, False otherwise
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully saved JSON to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save JSON: {e}")
        return False


def get_date_filename(report_date: Optional[str]) -> str:
    """
    Generate filename in yyyymmdd format.

    Args:
        report_date: Date string in YYYY-MM-DD format, or None for today

    Returns:
        Filename string (e.g., "20260209")
    """
    if report_date:
        try:
            # Parse and reformat to ensure correct format
            dt = datetime.strptime(report_date, "%Y-%m-%d")
            return dt.strftime("%Y%m%d")
        except ValueError:
            logger.warning(f"Invalid date format: {report_date}, using today's date")

    # Fallback to today's date
    return datetime.now().strftime("%Y%m%d")


def main(download_url: Optional[str] = None, date_override: Optional[str] = None, debug: bool = False):
    """
    Main function to orchestrate download and parsing.

    Args:
        download_url: URL to download from (defaults to config)
        date_override: Override date for filename (format: YYYY-MM-DD)
        debug: Enable debug logging
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    logger.info("="*80)
    logger.info("Starting Prince George's County Crime Report download and parse")
    logger.info("="*80)

    # Use provided URL or default from config
    url = download_url or PDF_URL

    # Temporary PDF path
    temp_pdf_path = Path("/tmp/crime_report_temp.pdf")

    # Step 1: Download PDF
    logger.info("Step 1: Downloading PDF...")
    if not download_pdf(url, temp_pdf_path):
        logger.error("Failed to download PDF. Exiting.")
        return 1

    # Step 2: Parse PDF
    logger.info("Step 2: Parsing PDF...")
    try:
        parsed_data = parse_pdf(str(temp_pdf_path))
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        return 1

    # Step 3: Determine date and filenames
    report_date = date_override or parsed_data.get('report_date')
    date_filename = get_date_filename(report_date)

    logger.info(f"Report date: {report_date}")
    logger.info(f"Date filename: {date_filename}")

    # Step 4: Save JSON
    json_path = JSON_OUTPUT_DIR / f"{date_filename}.json"
    logger.info(f"Step 3: Saving JSON to {json_path}...")
    if not save_json(parsed_data, json_path):
        logger.error("Failed to save JSON. Exiting.")
        return 1

    # Step 5: Archive PDF
    pdf_archive_path = PDF_ARCHIVE_DIR / f"{date_filename}.pdf"
    logger.info(f"Step 4: Archiving PDF to {pdf_archive_path}...")
    try:
        pdf_archive_path.parent.mkdir(parents=True, exist_ok=True)
        temp_pdf_path.rename(pdf_archive_path)
        logger.info(f"PDF archived successfully")
    except Exception as e:
        logger.warning(f"Failed to archive PDF: {e}")

    # Step 6: Summary
    logger.info("="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Report Date: {parsed_data.get('report_date', 'Unknown')}")
    logger.info(f"Crime Statistics Records: {len(parsed_data.get('crime_statistics', []))}")
    logger.info(f"Violent Crimes: {parsed_data.get('summary', {}).get('violent_crime_count', 0)}")
    logger.info(f"Property Crimes: {parsed_data.get('summary', {}).get('property_crime_count', 0)}")
    logger.info(f"Parse Errors: {len(parsed_data.get('parse_errors', []))}")
    logger.info(f"Output JSON: {json_path}")
    logger.info(f"Archived PDF: {pdf_archive_path}")
    logger.info("="*80)
    logger.info("Process completed successfully!")
    logger.info("="*80)

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download and parse Prince George's County Daily Crime Report"
    )
    parser.add_argument(
        '--url',
        help=f"PDF URL to download (default: {PDF_URL})",
        default=None
    )
    parser.add_argument(
        '--date',
        help="Override report date (format: YYYY-MM-DD)",
        default=None
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help="Enable debug logging"
    )

    args = parser.parse_args()

    sys.exit(main(download_url=args.url, date_override=args.date, debug=args.debug))
