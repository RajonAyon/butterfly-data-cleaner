"""
Date extraction and normalization from social media posts.

Handles various date formats commonly found in wildlife observation posts:
- DD/MM/YYYY, DD-MM-YYYY
- "19 July 2025", "July 06, 2025"
- "March'25", "2k25"
- Free-form dates in text
"""

import re
import pandas as pd
from dateutil import parser
import datefinder


# Compiled regex patterns for performance
DATE_PATTERN_NUMERIC = re.compile(
    r'\b\d{1,2}[\/\.-](?:\d{1,2}|[A-Za-z]{3,9})[\/\.-]\d{2,4}\b',
    re.IGNORECASE
)

DATE_PATTERN_TEXT = re.compile(
    r'\b('
    r'\d{1,3}(?:st|nd|rd|th)?\s*[A-Za-z]{3,9}(?:,?\s+\d{2,4})?'  # 19 July
    r'|[A-Za-z]{3,9}\s*,?\.?-?\'?\s*\d{2,4}'                     # March 2025
    r'|[A-Za-z]{3,9}\'\s*\d{2,4}'                                # July'25
    r'|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4}'                      # July 06 2025
    r'|([A-Za-z]{3,9})?[ ,\.]*2k\d{2,4}'                         # 2k25
    r')\b',
    re.IGNORECASE
)


def is_valid_year(year, min_year=2011, max_year=2025):
    """
    Validate if year is within acceptable range.
    
    Args:
        year (int): Year to validate
        min_year (int): Minimum acceptable year (default: 2011)
        max_year (int): Maximum acceptable year (default: 2025)
        
    Returns:
        bool: True if year is valid
    """
    return min_year <= year <= max_year


def extract_numeric_date(text):
    """
    Extract dates in numeric format (DD/MM/YYYY, DD-MM-YYYY).
    
    Args:
        text (str): Text to search
        
    Returns:
        tuple: (date_string, cleaned_text) or (None, original_text)
    """
    match = DATE_PATTERN_NUMERIC.search(text)
    if match:
        date_str = match.group(0)
        cleaned_text = text.replace(date_str, '').strip()
        return date_str, cleaned_text
    return None, text


def extract_text_date(text):
    """
    Extract dates in text format (e.g., "19 July 2025", "March'25").
    
    Args:
        text (str): Text to search
        
    Returns:
        str: Extracted date string or None
    """
    match = DATE_PATTERN_TEXT.search(text)
    if match:
        return match.group(0)
    return None


def normalize_year_format(date_str):
    """
    Normalize year formats like '2k25' to '2025'.
    
    Args:
        date_str (str): Date string potentially containing '2k' format
        
    Returns:
        str: Normalized date string
    """
    if not date_str:
        return date_str
    return re.sub(r'2[kK](\d{2})', r'20\1', date_str)


def validate_date(date_str):
    """
    Validate and parse date string.
    
    Args:
        date_str (str): Date string to validate
        
    Returns:
        bool: True if date is valid and within acceptable range
    """
    if not date_str:
        return False
    
    try:
        parsed = parser.parse(date_str, fuzzy=True)
        return is_valid_year(parsed.year)
    except (parser.ParserError, ValueError, TypeError):
        return False


def extract_date_from_text(text, current_date=None):
    """
    Extract date from text using multiple strategies.
    
    Tries in order:
    1. Numeric formats (DD/MM/YYYY)
    2. Text formats (19 July 2025)
    3. Standalone years (2025)
    4. Fuzzy matching with datefinder
    
    Args:
        text (str): Text to extract date from
        current_date (str): Previously extracted date (optional)
        
    Returns:
        tuple: (extracted_date, cleaned_text)
    """
    # If we already have a valid date, return it
    if current_date and validate_date(current_date):
        return current_date, text
    
    # Strategy 1: Numeric date patterns
    date_str, cleaned_text = extract_numeric_date(text)
    if date_str and validate_date(date_str):
        return date_str, cleaned_text
    
    # Strategy 2: Text date patterns
    date_str = extract_text_date(text)
    if date_str and validate_date(date_str):
        cleaned_text = text.replace(date_str, '').strip()
        return normalize_year_format(date_str), cleaned_text
    
    # Strategy 3: Standalone year
    year_match = re.search(r'\b(20[1-2][0-9]|2025|201[3-9])\b', text)
    if year_match:
        year = int(year_match.group(0))
        if is_valid_year(year):
            return str(year), text.replace(year_match.group(0), '').strip()
    
    # Strategy 4: Fuzzy datefinder (last resort, slower)
    try:
        matches = list(datefinder.find_dates(text, strict=False))
        if matches:
            date_obj = matches[0]
            if is_valid_year(date_obj.year):
                date_str = date_obj.strftime('%Y-%m-%d')
                return date_str, text
    except Exception:
        pass
    
    return None, text


def process_dataframe_dates(df, text_column='post_text', date_column='extracted_date'):
    """
    Extract and validate dates from entire DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with text data
        text_column (str): Column name containing text
        date_column (str): Column name to store extracted dates
        
    Returns:
        pd.DataFrame: DataFrame with extracted dates and cleaned text
    """
    df = df.copy()
    df[date_column] = None
    
    # Extract dates row by row
    for idx, row in df.iterrows():
        extracted_date, cleaned_text = extract_date_from_text(
            row[text_column],
            current_date=row.get(date_column)
        )
        df.at[idx, date_column] = extracted_date
        df.at[idx, text_column] = cleaned_text
    
    # Drop rows without valid dates
    df = df.dropna(subset=[date_column]).reset_index(drop=True)
    
    return df


# Convenience function for single text processing
def extract_date(text):
    """
    Simple wrapper to extract date from single text string.
    
    Args:
        text (str): Text to process
        
    Returns:
        str: Extracted date or None
    """
    date_str, _ = extract_date_from_text(text)
    return date_str