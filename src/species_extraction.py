"""
Species extraction and validation for butterfly observations.

Extracts butterfly identification from unstructured text using:
- Fuzzy matching against reference databases
- Multi-source taxonomic validation
- Genus/species parsing from scientific names

Reference databases:
- Bangladesh butterfly checklist (PDF extraction)
- Photographic guide data
- Custom curated species list
"""

import re
import pandas as pd
from thefuzz import fuzz
from thefuzz import fuzz
import pandas as pd
from pyinaturalist import get_taxa

def extract_genus_species(scientific_name):
    """
    Extract genus and species from binomial scientific name.
    
    Uses regex to parse standard taxonomic naming (Genus species).
    
    Args:
        scientific_name (str): Scientific name (e.g., "Papilio polytes")
        
    Returns:
        tuple: (genus, species) both lowercase, or (None, None) if parsing fails
        
    Examples:
        >>> extract_genus_species("Papilio polytes")
        ('papilio', 'polytes')
        
        >>> extract_genus_species("Graphium doson doson")
        ('graphium', 'doson')
    """
    if not isinstance(scientific_name, str) or not scientific_name.strip():
        return None, None
    
    # Extract Genus (capitalized word)
    genus_match = re.search(r'\b([A-Z][a-z]+)\b', scientific_name)
    genus = genus_match.group(1).lower() if genus_match else None
    
    # Extract Species (lowercase word after genus)
    species_match = re.search(r'\b[A-Z][a-z]+\s+([a-z]+)\b', scientific_name)
    species = species_match.group(1).lower() if species_match else None
    
    return genus, species


def clean_text_for_matching(text):
    """
    Remove special characters that interfere with fuzzy matching.
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not isinstance(text, str):
        return ""
    
    # Remove brackets, parentheses, asterisks, punctuation
    cleaned = re.sub(r'[\[\]\*\(\)\.,]', '', text)
    return cleaned.strip()


def fuzzy_match_wordwise(text, choices, threshold=100):
    """
    Find best matching choice using word-wise fuzzy matching.
    
    Compares each word in the choice against all words in the text,
    then averages scores. More robust than full-string matching for
    noisy social media text.
    
    Args:
        text (str): Text to search in
        choices (list): List of possible matches
        threshold (int): Minimum average score (0-100) to accept match
        
    Returns:
        str: Best matching choice or None
        
    Examples:
        >>> choices = ['papilio', 'graphium', 'danaus']
        >>> fuzzy_match_wordwise("saw papilio butterfly", choices)
        'papilio'
    """
    # Clean and tokenize input text
    cleaned_text = clean_text_for_matching(text.lower())
    text_words = cleaned_text.split()
    
    if not text_words:
        return None
    
    best_match = None
    best_score = 0
    
    for choice in choices:
        cleaned_choice = clean_text_for_matching(choice.lower())
        choice_words = cleaned_choice.split()
        
        if not choice_words:
            continue
        
        # Calculate word-wise scores
        word_scores = []
        for choice_word in choice_words:
            # Find best match for this choice word among all text words
            best_word_score = max(
                fuzz.ratio(choice_word, text_word) 
                for text_word in text_words
            )
            word_scores.append(best_word_score)
        
        # Average score across all words
        avg_score = sum(word_scores) / len(word_scores)
        
        if avg_score > best_score and avg_score >= threshold:
            best_match = choice
            best_score = avg_score
    
    return best_match


def extract_species_from_text(text, reference_df, 
                             genus_threshold=100,
                             species_threshold=100, 
                             common_name_threshold=95):
    """
    Extract butterfly identification from text using reference database.
    
    Args:
        text (str): Text to extract from
        reference_df (pd.DataFrame): Reference database with columns:
            - 'Genus': Genus names
            - 'Species': Species names  
            - 'Common_Name': Common names
        genus_threshold (int): Minimum score for genus match (default: 100)
        species_threshold (int): Minimum score for species match (default: 100)
        common_name_threshold (int): Minimum score for common name (default: 95)
        
    Returns:
        dict: Dictionary with keys 'genus', 'species', 'common_name'
        
    Examples:
        >>> ref = pd.DataFrame({
        ...     'Genus': ['papilio', 'graphium'],
        ...     'Species': ['polytes', 'doson'],
        ...     'Common_Name': ['Common Mormon', 'Common Jay']
        ... })
        >>> extract_species_from_text("Saw Common Mormon today", ref)
        {'genus': 'papilio', 'species': 'polytes', 'common_name': 'Common Mormon'}
    """
    result = {
        'genus': None,
        'species': None,
        'common_name': None
    }
    
    # Extract genus
    if 'Genus' in reference_df.columns:
        genus_choices = reference_df['Genus'].dropna().unique().tolist()
        result['genus'] = fuzzy_match_wordwise(text, genus_choices, genus_threshold)
    
    # Extract species
    if 'Species' in reference_df.columns:
        species_choices = reference_df['Species'].dropna().unique().tolist()
        result['species'] = fuzzy_match_wordwise(text, species_choices, species_threshold)
    
    # Extract common name (lower threshold, names can be longer/more variable)
    if 'Common_Name' in reference_df.columns:
        common_choices = reference_df['Common_Name'].dropna().unique().tolist()
        result['common_name'] = fuzzy_match_wordwise(text, common_choices, common_name_threshold)
    
    return result


def process_dataframe_species(df, reference_csv_path, text_column='post_text'):
    """
    Extract species information for entire DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with text data
        reference_csv_path (str): Path to reference butterfly database CSV
        text_column (str): Column name containing text (default: 'post_text')
        
    Returns:
        pd.DataFrame: DataFrame with added columns:
            - Butterfly_Genus
            - Butterfly_Species  
            - Butterfly_Common_Name
    """
    # Load reference database
    reference_df = pd.read_csv(reference_csv_path)
    
    # Ensure reference has required columns
    required_cols = ['Genus', 'Species', 'Common_Name']
    if not all(col in reference_df.columns for col in required_cols):
        raise ValueError(f"Reference CSV must contain columns: {required_cols}")
    
    df = df.copy()
    
    # Extract species information
    genus_choices = reference_df['Genus'].dropna().unique().tolist()
    species_choices = reference_df['Species'].dropna().unique().tolist()
    common_choices = reference_df['Common_Name'].dropna().unique().tolist()
    
    df['Butterfly_Genus'] = df[text_column].apply(
        lambda text: fuzzy_match_wordwise(text, genus_choices, threshold=100)
    )
    
    df['Butterfly_Species'] = df[text_column].apply(
        lambda text: fuzzy_match_wordwise(text, species_choices, threshold=100)
    )
    
    df['Butterfly_Common_Name'] = df[text_column].apply(
        lambda text: fuzzy_match_wordwise(text, common_choices, threshold=95)
    )
    
    return df


def build_reference_database_from_pdf(pdf_path, pages='1-10', 
                                      additional_species=None,
                                      photographic_guide_csv=None,
                                      output_path='reference_butterflies.csv'):
    """
    Build reference database from multiple sources.
    
    Combines:
    1. PDF checklist extraction (using Camelot)
    2. Additional curated species (manual additions)
    3. Photographic guide data (if available)
    
    Args:
        pdf_path (str): Path to butterfly checklist PDF
        pages (str): Pages to extract (default: '1-10')
        additional_species (dict): Manual additions {common_name: (genus, species)}
        photographic_guide_csv (str): Optional path to photographic guide CSV
        output_path (str): Where to save combined reference database
        
    Returns:
        pd.DataFrame: Combined reference database
    """
    try:
        import camelot
    except ImportError:
        raise ImportError("camelot-py required: pip install camelot-py[cv]")
    
    # Extract from PDF
    tables = camelot.read_pdf(pdf_path, pages=pages, flavor='lattice')
    pdf_df = pd.concat([table.df for table in tables], ignore_index=True)
    
    # Process PDF data
    pdf_df = pdf_df[[1, 2]]  # Assuming columns 1=scientific, 2=common
    pdf_df.columns = ['Scientific_Name', 'Common_Name']
    pdf_df['Scientific_Name'] = pdf_df['Scientific_Name'].str.replace(r'\d+', '', regex=True)
    
    # Extract genus/species from scientific names
    pdf_df['Genus'], pdf_df['Species'] = zip(*pdf_df['Scientific_Name'].apply(extract_genus_species))
    pdf_df = pdf_df.dropna(subset=['Genus', 'Species']).reset_index(drop=True)
    
    # Add manual species if provided
    if additional_species:
        manual_df = pd.DataFrame([
            {
                'Common_Name': common,
                'Genus': genus.lower(),
                'Species': species.lower(),
                'Scientific_Name': f"{genus} {species}"
            }
            for common, (genus, species) in additional_species.items()
        ])
        pdf_df = pd.concat([pdf_df, manual_df], ignore_index=True)
    
    # Add photographic guide if provided
    if photographic_guide_csv:
        photo_df = pd.read_csv(photographic_guide_csv)
        photo_df.rename(columns={
            'Scientific Name': 'Scientific_Name',
            'Common Name': 'Common_Name'
        }, inplace=True)
        
        photo_df['Genus'], photo_df['Species'] = zip(*photo_df['Scientific_Name'].apply(extract_genus_species))
        photo_df = photo_df[['Common_Name', 'Scientific_Name', 'Genus', 'Species']].dropna()
        
        pdf_df = pd.concat([pdf_df, photo_df], ignore_index=True)
    
    # Remove duplicates
    pdf_df = pdf_df.drop_duplicates().reset_index(drop=True)
    
    # Save
    pdf_df.to_csv(output_path, index=False)
    print(f"Reference database saved: {output_path} ({len(pdf_df)} species)")
    
    return pdf_df



def fill_genus_species(df, text_column='post_text', common_name_column='Butterfly_Common_Name'):
    for idx, row in df.iterrows():
        common_name = row.get(common_name_column)
        text = row.get(text_column, "")
        
        if pd.isna(common_name) or common_name.strip() == "":
            continue
        
        # Only call get_taxa once per row
        response = get_taxa(q=common_name)
        candidates = [r['name'] for r in response.get('results', [])]

        # Fill genus if empty
        if pd.isna(row.get('Butterfly_Genus')) or row.get('Butterfly_Genus') == '':
            genus_found = None
            for sci_name in candidates:
                parts = sci_name.split()
                if len(parts) < 1:
                    continue
                genus = parts[0]
                if fuzz.partial_ratio(genus.lower(), text.lower()) >= 100:
                    genus_found = genus
                    break
            if genus_found:
                df.at[idx, 'Butterfly_Genus'] = genus_found

        # Fill species if empty
        if pd.isna(row.get('Butterfly_Species')) or row.get('Butterfly_Species') == '':
            species_found = None
            for sci_name in candidates:
                parts = sci_name.split()
                if len(parts) < 2:
                    continue
                species = parts[1]
                if fuzz.partial_ratio(species.lower(), text.lower()) == 100:
                    species_found = species
                    break
            if species_found:
                df.at[idx, 'Butterfly_Species'] = species_found
