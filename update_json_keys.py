"""
Script to update JSON keys to machine-readable format (lowercase with underscores)
"""
import json
import re

def normalize_key(key):
    """Normalize a key to machine-readable format"""
    # Handle specific mappings
    key_lower = key.lower().strip()
    
    mapping = {
        '7-day totals': 'seven_day_total',
        '+/-': 'change',
        '% change': 'percent_change',
    }
    
    # Check for Prev. 7 pattern with dates
    if key_lower.startswith('prev. 7'):
        return 'prev_seven_day_total'
    
    # Check for YTD patterns
    ytd_pattern = r'ytd\s+(\d{2})\s+'
    ytd_match = re.search(ytd_pattern, key_lower)
    if ytd_match:
        year = ytd_match.group(1)
        return f'ytd_20{year}'
    
    # Check if in mapping
    if key_lower in mapping:
        return mapping[key_lower]
    
    # Check if it's already an ISO date (YYYY-MM-DD)
    if re.match(r'\d{4}-\d{2}-\d{2}', key):
        return key
    
    # Check if it's a standard field name
    if key in ['report_date', 'extracted_date_text', 'download_timestamp', 
               'source_file', 'crime_statistics', 'summary', 'parse_errors',
               'offense_type', 'total_offense_types', 'violent_crimes', 
               'property_crimes', 'violent_crime_count', 'property_crime_count']:
        return key
    
    # Default: replace spaces and special chars with underscores
    normalized = re.sub(r'[^\w\s-]', '', key_lower)
    normalized = re.sub(r'[-\s]+', '_', normalized)
    
    return normalized

def update_dict_keys(obj):
    """Recursively update dictionary keys"""
    if isinstance(obj, dict):
        return {normalize_key(k): update_dict_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [update_dict_keys(item) for item in obj]
    else:
        return obj

if __name__ == "__main__":
    input_file = 'data/json/20260208.json'
    
    # Read the JSON file
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Update keys
    updated_data = update_dict_keys(data)
    
    # Write back to file
    with open(input_file, 'w') as f:
        json.dump(updated_data, f, indent=2)
    
    print(f"Updated keys in {input_file}")
