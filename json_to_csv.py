"""
Convert JSON crime reports to CSV format

This utility converts the structured JSON files to CSV for easier analysis
in spreadsheet applications.
"""

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

from config import JSON_OUTPUT_DIR, CSV_OUTPUT_DIR, LOG_FORMAT

# Set up logging
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def flatten_record(record: Dict[str, Any], parent_key: str = '') -> Dict[str, Any]:
    """
    Flatten nested dictionary into a single level.

    Args:
        record: Dictionary to flatten
        parent_key: Prefix for nested keys

    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in record.items():
        new_key = f"{parent_key}.{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_record(v, new_key).items())
        elif isinstance(v, list):
            # Convert lists to comma-separated strings
            items.append((new_key, ', '.join(map(str, v)) if v else ''))
        else:
            items.append((new_key, v))

    return dict(items)


def json_to_csv(json_path: Path, csv_path: Path) -> bool:
    """
    Convert a single JSON file to CSV.

    Args:
        json_path: Path to input JSON file
        csv_path: Path to output CSV file

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Converting {json_path} to {csv_path}")

        # Load JSON data
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        crime_statistics = data.get('crime_statistics', [])

        if not crime_statistics:
            logger.warning(f"No crime statistics found in {json_path}")
            return False

        # Add metadata to each record
        report_date = data.get('report_date')
        extracted_date_text = data.get('extracted_date_text')

        enhanced_records = []
        for record in crime_statistics:
            enhanced = {
                'report_date': report_date,
                'extracted_date_text': extracted_date_text,
                **record
            }
            enhanced_records.append(enhanced)

        # Flatten all records
        flattened_records = [flatten_record(record) for record in enhanced_records]

        # Get all possible fieldnames
        fieldnames = set()
        for record in flattened_records:
            fieldnames.update(record.keys())

        fieldnames = sorted(list(fieldnames))

        # Ensure report_date and offense_type are first columns
        priority_fields = ['report_date', 'offense_type']
        for field in reversed(priority_fields):
            if field in fieldnames:
                fieldnames.remove(field)
                fieldnames.insert(0, field)

        # Write CSV
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_records)

        logger.info(f"Successfully converted to CSV: {csv_path}")
        logger.info(f"  Records: {len(flattened_records)}")
        logger.info(f"  Columns: {len(fieldnames)}")

        return True

    except Exception as e:
        logger.error(f"Failed to convert {json_path} to CSV: {e}")
        return False


def convert_all_json_files(json_dir: Path, csv_dir: Path) -> int:
    """
    Convert all JSON files in a directory to CSV.

    Args:
        json_dir: Directory containing JSON files
        csv_dir: Directory to save CSV files

    Returns:
        Number of files successfully converted
    """
    json_files = sorted(json_dir.glob("*.json"))

    if not json_files:
        logger.warning(f"No JSON files found in {json_dir}")
        return 0

    logger.info(f"Found {len(json_files)} JSON file(s) to convert")

    success_count = 0
    for json_path in json_files:
        csv_path = csv_dir / f"{json_path.stem}.csv"
        if json_to_csv(json_path, csv_path):
            success_count += 1

    logger.info(f"Successfully converted {success_count}/{len(json_files)} files")
    return success_count


def create_combined_csv(json_dir: Path, output_path: Path) -> bool:
    """
    Create a single CSV file combining all JSON files.

    Args:
        json_dir: Directory containing JSON files
        output_path: Path to output combined CSV

    Returns:
        True if successful, False otherwise
    """
    try:
        json_files = sorted(json_dir.glob("*.json"))

        if not json_files:
            logger.warning(f"No JSON files found in {json_dir}")
            return False

        logger.info(f"Combining {len(json_files)} JSON file(s) into {output_path}")

        all_records = []

        # Load and collect all records
        for json_path in json_files:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            crime_statistics = data.get('crime_statistics', [])
            report_date = data.get('report_date')
            extracted_date_text = data.get('extracted_date_text')

            for record in crime_statistics:
                enhanced = {
                    'report_date': report_date,
                    'extracted_date_text': extracted_date_text,
                    'source_file': json_path.name,
                    **record
                }
                all_records.append(enhanced)

        if not all_records:
            logger.warning("No crime statistics found in any JSON files")
            return False

        # Flatten all records
        flattened_records = [flatten_record(record) for record in all_records]

        # Get all fieldnames
        fieldnames = set()
        for record in flattened_records:
            fieldnames.update(record.keys())

        fieldnames = sorted(list(fieldnames))

        # Prioritize key fields
        priority_fields = ['report_date', 'offense_type', 'source_file']
        for field in reversed(priority_fields):
            if field in fieldnames:
                fieldnames.remove(field)
                fieldnames.insert(0, field)

        # Write combined CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_records)

        logger.info(f"Successfully created combined CSV: {output_path}")
        logger.info(f"  Total records: {len(flattened_records)}")
        logger.info(f"  Files combined: {len(json_files)}")
        logger.info(f"  Columns: {len(fieldnames)}")

        return True

    except Exception as e:
        logger.error(f"Failed to create combined CSV: {e}")
        return False


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Convert crime report JSON files to CSV format"
    )
    parser.add_argument(
        'input',
        nargs='?',
        help='Input JSON file or directory (default: data/json/)'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output CSV file or directory (default: data/csv/)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Convert all JSON files in the input directory'
    )
    parser.add_argument(
        '--combined',
        action='store_true',
        help='Create a single combined CSV from all JSON files'
    )

    args = parser.parse_args()

    # Determine input
    if args.input:
        input_path = Path(args.input)
    else:
        input_path = JSON_OUTPUT_DIR

    # Convert all files in directory
    if args.all or (input_path.is_dir() and not args.input):
        output_dir = Path(args.output) if args.output else CSV_OUTPUT_DIR
        success = convert_all_json_files(input_path, output_dir)
        return 0 if success > 0 else 1

    # Create combined CSV
    elif args.combined:
        output_path = Path(args.output) if args.output else CSV_OUTPUT_DIR / "combined.csv"
        json_dir = input_path if input_path.is_dir() else JSON_OUTPUT_DIR
        success = create_combined_csv(json_dir, output_path)
        return 0 if success else 1

    # Convert single file
    elif input_path.is_file():
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = CSV_OUTPUT_DIR / f"{input_path.stem}.csv"

        success = json_to_csv(input_path, output_path)
        return 0 if success else 1

    else:
        logger.error(f"Input path does not exist: {input_path}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
