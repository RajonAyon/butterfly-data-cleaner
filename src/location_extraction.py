import pandas as pd
from flashtext import KeywordProcessor


def load_geonames_data(filepath, sep="\t"):
    """
    Load GeoNames database from tab-separated file.
    
    Args:
        filepath (str): Path to GeoNames .txt file
        sep (str): Delimiter (default: tab)
        
    Returns:
        pd.DataFrame: Processed GeoNames data with Name, Alternate_Names, Coordinates
    """
    # Load raw GeoNames data
    places_df = pd.read_csv(filepath, sep=sep, header=None, engine='python')
    
    # Rename columns (GeoNames standard format)
    places_df.rename(columns={
        2: "Name",
        3: "Alternate_Names",
        4: "Latitude",
        5: "Longitude"
    }, inplace=True)
    
    # Combine lat/lon into coordinate tuples
    places_df["Coordinates"] = (
        places_df["Latitude"].astype(str) + ", " + 
        places_df["Longitude"].astype(str)
    )
    
    # Keep only relevant columns
    places_df = places_df[['Name', 'Alternate_Names', 'Coordinates']]
    
    return places_df


def prepare_location_database(places_df):
    """
    Prepare location database for keyword matching.
    
    Groups by main name, merges alternate names, and sorts by length
    (longer names matched first to avoid partial matches).
    
    Args:
        places_df (pd.DataFrame): Raw GeoNames data
        
    Returns:
        pd.DataFrame: Processed location database
    """
    # Ensure Alternate_Names is always a list
    places_df['Alternate_Names'] = places_df['Alternate_Names'].fillna('')
    places_df['Alternate_Names'] = places_df['Alternate_Names'].apply(
        lambda x: x if isinstance(x, list) else [n.strip() for n in x.split(',') if n.strip()]
    )
    
    # Group by main Name, keep first Coordinates, merge alternate names
    grouped_places = (
        places_df
        .groupby('Name', as_index=False)
        .agg({
            'Coordinates': 'first',
            'Alternate_Names': lambda x: sorted(set(sum(x, [])))  # flatten and deduplicate
        })
    )
    
    # Sort by length of Name descending (longest first)
    # This ensures "Chittagong Hill Tracts" matches before "Chittagong"
    grouped_places = grouped_places.sort_values(
        by='Name', 
        key=lambda col: col.str.len(), 
        ascending=False
    )
    
    return grouped_places

def build_keyword_processor(grouped_places, 
                            exclude_names=None,
                            custom_mappings=None):
    """
    Build flashtext KeywordProcessor for fast location extraction.
    
    Args:
        grouped_places (pd.DataFrame): Prepared location database
        exclude_names (list): Names to exclude from matching (default: None)
        custom_mappings (dict): Custom name variants to add
            Format: {variant: (standard_name, coordinates)}
        
    Returns:
        KeywordProcessor: Configured keyword processor
    """
    keyword_processor = KeywordProcessor(case_sensitive=False)
    
    # Set word boundaries (only match full words)
    keyword_processor.non_word_boundaries = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    )
    
    # Default exclusions (common words that aren't locations)
    if exclude_names is None:
        exclude_names = ['Aria', 'Asia', 'Bangladesh', 'Dana', 'dia', 
                        'Had', 'Indra', 'Kayes']
    
    # Add main names and alternates
    for _, row in grouped_places.iterrows():
        main_name = row['Name'].strip()
        coords = row['Coordinates']
        all_names = set([main_name] + row['Alternate_Names'])
        
        for name in all_names:
            if name and name not in exclude_names:
                # Normalize quotes
                normalized_name = name.replace('\u2019', "'")  # Unicode escape for right single quote
                keyword_processor.add_keyword(normalized_name, (main_name, coords))
    # Add custom mappings (common misspellings, abbreviations)
    if custom_mappings:
        for variant, (standard_name, coords) in custom_mappings.items():
            keyword_processor.add_keyword(variant, (standard_name, coords))
    
    return keyword_processor

def extract_location(text, keyword_processor):
    """
    Extract first matching location from text.
    
    Args:
        text (str): Text to search
        keyword_processor (KeywordProcessor): Pre-built processor
        
    Returns:
        tuple: (location_name, coordinates) or (None, None)
    """
    if not isinstance(text, str):
        return (None, None)
    
    # Normalize quotes in text
    text = text.replace('\u2019', "'").replace('\u2018', "'")

    
    # Extract keywords
    matches = keyword_processor.extract_keywords(text)
    
    if matches:
        return matches[0]  # (main_name, coordinates)
    
    return (None, None)


def standardize_location_names(df, location_column='Location', 
                               coord_column='Coordinates',
                               location_mappings=None):
    """
    Standardize location name variants.
    
    Args:
        df (pd.DataFrame): DataFrame with location data
        location_column (str): Column containing location names
        coord_column (str): Column containing coordinates
        location_mappings (dict): Mapping of variants to standard names
            Format: {variant: (standard_name, new_coordinates)}
        
    Returns:
        pd.DataFrame: DataFrame with standardized locations
    """
    if location_mappings is None:
        # Default Bangladesh location standardizations
        location_mappings = {
            'Sundarban': ('Sundarbans', '22.0, 89.0'),
            'Sylhet Division': ('Sylhet', '24.89904, 91.87198'),
            'Sreemangal': ('Srimangal', '24.30652, 91.72955'),
            'Rajshahi University': ('Rajshahi', '24.374, 88.60114'),
            'Lakshmipu': ('Laxmipur', '25.81429, 88.27485'),
            'Kishorganj': ('Kishoregonj', '24.41667, 90.95'),
            'Hathazari Upazila': ('Hathazari', '22.50515, 91.81339'),
            'Chattogram': ('Chittagong', '22.4875, 91.96333'),
        }
    
    df = df.copy()
    
    # Apply standardization
    for variant, (standard_name, coords) in location_mappings.items():
        mask = df[location_column] == variant
        df.loc[mask, location_column] = standard_name
        df.loc[mask, coord_column] = coords
    
    return df


def filter_unwanted_locations(df, location_column='Location', 
                              unwanted=None):
    """
    Remove rows with unwanted location matches.
    
    Args:
        df (pd.DataFrame): DataFrame with location data
        location_column (str): Column containing location names
        unwanted (list): List of unwanted location names
        
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    if unwanted is None:
        # Default unwanted matches (common false positives)
        unwanted = ['Bangla', 'Dia', 'Dina', 'Kumar N', 'Tara']
    
    df = df[~df[location_column].isin(unwanted)].copy()
    return df


def parse_coordinates(coord_string):
    """
    Parse coordinate string to (lat, lon) tuple.
    
    Args:
        coord_string (str): Coordinates as string (e.g., "22.4875, 91.96333")
        
    Returns:
        tuple: (latitude, longitude) or None if parsing fails
    """
    if pd.isna(coord_string):
        return None
    
    # Remove brackets and whitespace
    coord_string = str(coord_string).replace('(', '').replace(')', '').strip()
    
    try:
        # Split by comma and convert to floats
        lat, lon = map(float, coord_string.split(','))
        return (lat, lon)
    except:
        return None


def process_dataframe_locations(df, 
                                geonames_filepath,
                                text_column='post_text',
                                exclude_names=None,
                                custom_mappings=None,
                                location_standardization=None,
                                unwanted_locations=None):
    """
    Extract and process locations for entire DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with text data
        geonames_filepath (str): Path to GeoNames .txt file
        text_column (str): Column containing text (default: 'post_text')
        exclude_names (list): Location names to exclude
        custom_mappings (dict): Custom location name mappings
        location_standardization (dict): Location name standardization rules
        unwanted_locations (list): Unwanted location matches to filter
        
    Returns:
        pd.DataFrame: DataFrame with added columns:
            - Location: Extracted location name
            - lat: Latitude
            - lon: Longitude
    """
    # Load and prepare GeoNames data
    places_df = load_geonames_data(geonames_filepath)
    grouped_places = prepare_location_database(places_df)
    
    # Default custom mappings for Bangladesh
    if custom_mappings is None:
        custom_mappings = {
            "chattagram": ("Chittagong", "22.4875, 91.96333"),
            "chapanawabganj": ("Chapai Nawabganj", "24.59895, 88.28339"),
            "chapainawabganj": ("Chapai Nawabganj", "24.59895, 88.28339"),
            "khagrachori": ("Khagrachari", "22.66881, 92.38407"),
            "bandorban": ("Bandarban", "22.19534, 92.21946"),
            "banderban": ("Bandarban", "22.19534, 92.21946"),
            "coxbazar": ("Coxs Bazar", "21.44795, 92.10732"),
            "habigonj": ("Habiganj", "24.38044, 91.41299"),
            "moulavibazar": ("Maulavi Bazar", "24.48888, 91.77075"),
            "moulovibazar": ("Maulavi Bazar", "24.48888, 91.77075"),
            "hazarikhil wildlife sanctuary": ("Hazarikhil Wildlife Sanctuary", "22.7059, 91.6909"),
            "Sreemongol": ("Sreemangal", "24.3, 91.68")
        }
    
    # Build keyword processor
    keyword_processor = build_keyword_processor(
        grouped_places,
        exclude_names=exclude_names,
        custom_mappings=custom_mappings
    )
    
    df = df.copy()
    
    # Extract locations
    df[['Location', 'Coordinates']] = df[text_column].apply(
        lambda x: pd.Series(extract_location(x, keyword_processor))
    )
    
    # Filter unwanted locations
    df = filter_unwanted_locations(df, unwanted=unwanted_locations)
    
    # Standardize location names
    df = standardize_location_names(df, location_mappings=location_standardization)
    
    # Parse coordinates
    df['Coordinates'] = df['Coordinates'].apply(parse_coordinates)
    
    # Drop rows without coordinates
    df = df.dropna(subset=['Coordinates'])
    
    # Split coordinates into lat/lon
    df['lat'] = df['Coordinates'].apply(lambda x: x[0] if x else None)
    df['lon'] = df['Coordinates'].apply(lambda x: x[1] if x else None)
    
    # Drop temporary Coordinates column
    df = df.drop(columns=['Coordinates'])
    
    return df


# Convenience function for getting custom Bangladesh mappings
def get_bangladesh_custom_mappings():
    """
    Get default custom location mappings for Bangladesh.
    
    Returns:
        dict: Custom location name variants and their standardizations
    """
    return {
        "chattagram": ("Chittagong", "22.4875, 91.96333"),
        "chapanawabganj": ("Chapai Nawabganj", "24.59895, 88.28339"),
        "chapainawabganj": ("Chapai Nawabganj", "24.59895, 88.28339"),
        "khagrachori": ("Khagrachari", "22.66881, 92.38407"),
        "bandorban": ("Bandarban", "22.19534, 92.21946"),
        "banderban": ("Bandarban", "22.19534, 92.21946"),
        "coxbazar": ("Coxs Bazar", "21.44795, 92.10732"),
        "habigonj": ("Habiganj", "24.38044, 91.41299"),
        "moulavibazar": ("Maulavi Bazar", "24.48888, 91.77075"),
        "moulovibazar": ("Maulavi Bazar", "24.48888, 91.77075"),
        "hazarikhil wildlife sanctuary": ("Hazarikhil Wildlife Sanctuary", "22.7059, 91.6909"),
        "Sreemongol": ("Sreemangal", "24.3, 91.68")
    }


def get_bangladesh_location_standardization():
    """
    Get default location standardization rules for Bangladesh.
    
    Returns:
        dict: Location variant to standard name mappings
    """
    return {
        'Sundarban': ('Sundarbans', '22.0, 89.0'),
        'Sylhet Division': ('Sylhet', '24.89904, 91.87198'),
        'Sreemangal': ('Srimangal', '24.30652, 91.72955'),
        'Rajshahi University': ('Rajshahi', '24.374, 88.60114'),
        'Lakshmipu': ('Laxmipur', '25.81429, 88.27485'),
        'Kishorganj': ('Kishoregonj', '24.41667, 90.95'),
        'Hathazari Upazila': ('Hathazari', '22.50515, 91.81339'),
        'Chattogram': ('Chittagong', '22.4875, 91.96333'),
    }