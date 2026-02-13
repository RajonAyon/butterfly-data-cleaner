"""
Text normalization utilities for cleaning social media posts.

Handles common issues in user-generated content:
- Unicode characters and encoding problems
- Zero-width spaces and invisible characters
- Inconsistent whitespace
- Mixed case text
- Punctuation and special characters

Designed for processing wildlife observation posts from Facebook groups.
"""

import unicodedata
import re


def normalize_text(text):
    """
    Normalize and clean text from social media posts.
    
    Performs the following operations:
    1. Unicode normalization (NFKD) to ASCII
    2. Removes zero-width spaces and control characters
    3. Converts to lowercase
    4. Normalizes whitespace
    
    Args:
        text (str): Raw text from social media post
        
    Returns:
        str: Cleaned and normalized text
        
    Examples:
        >>> normalize_text("Saw  butterfly\u200B today")
        'saw butterfly today'
        
        >>> normalize_text("FOUND Papilio polytes!!!")
        'found papilio polytes!!!'
    """
    if not isinstance(text, str):
        return ""
    
    # Normalize Unicode characters to their closest ASCII equivalent
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8', 'ignore')
    
    # Remove zero-width spaces and control characters
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def remove_punctuation(text):
    """
    Extract scientific names from parentheses and remove punctuation.
    
    First attempts to extract text within parentheses (commonly used
    for scientific names), then removes all punctuation characters.
    
    Args:
        text (str): Text potentially containing scientific names
        
    Returns:
        str: Text with punctuation removed
        
    Examples:
        >>> remove_punctuation("Common Jay (Graphium doson)")
        'Graphium doson'
        
        >>> remove_punctuation("Beautiful butterfly!!!")
        'Beautiful butterfly'
    """
    if not isinstance(text, str):
        return ""
    
    # Extract scientific name from parentheses if present
    match = re.search(r'\((.*?)\)', text)
    if match:
        return match.group(1)
    
    # Remove all punctuation
    clean_text = re.sub(r'[^\w\s]', '', text)
    return clean_text.strip()


def remove_urls(text):
    """
    Remove URLs from text.
    
    Args:
        text (str): Text potentially containing URLs
        
    Returns:
        str: Text with URLs removed
        
    Examples:
        >>> remove_urls("Check this out https://example.com")
        'Check this out'
    """
    if not isinstance(text, str):
        return ""
    
    # Remove URLs (http/https)
    text = re.sub(r'https?://\S+', '', text)
    # Remove www URLs
    text = re.sub(r'www\.\S+', '', text)
    
    return text.strip()


def remove_emojis(text):
    """
    Remove emoji characters from text.
    
    Args:
        text (str): Text potentially containing emojis
        
    Returns:
        str: Text with emojis removed
        
    Examples:
        >>> remove_emojis("Beautiful butterfly 🦋")
        'Beautiful butterfly'
    """
    if not isinstance(text, str):
        return ""
    
    # Remove emojis using Unicode ranges
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    
    return emoji_pattern.sub('', text).strip()


def normalize_hashtags(text):
    """
    Extract text from hashtags (remove # symbol).
    
    Args:
        text (str): Text containing hashtags
        
    Returns:
        str: Text with hashtags converted to words
        
    Examples:
        >>> normalize_hashtags("Saw #butterfly today #nature")
        'Saw butterfly today nature'
    """
    if not isinstance(text, str):
        return ""
    
    # Replace #word with word (keep the text)
    text = re.sub(r'#(\w+)', r'\1', text)
    
    return text.strip()


def clean_text_full(text, remove_urls_flag=True, remove_emojis_flag=True, 
                    remove_hashtags=False, remove_punctuation_flag=False):
    """
    Apply full cleaning pipeline to text.
    
    Combines multiple cleaning operations in the optimal order.
    
    Args:
        text (str): Raw text to clean
        remove_urls_flag (bool): Remove URLs (default: True)
        remove_emojis_flag (bool): Remove emojis (default: True)
        remove_hashtags (bool): Remove hashtag symbols (default: False)
        remove_punctuation_flag (bool): Remove all punctuation (default: False)
        
    Returns:
        str: Fully cleaned text
        
    Examples:
        >>> clean_text_full("Check 🦋 #butterfly https://example.com")
        'check butterfly'
    """
    if not isinstance(text, str):
        return ""
    
    # Apply cleaning operations in order
    if remove_urls_flag:
        text = remove_urls(text)
    
    if remove_emojis_flag:
        text = remove_emojis(text)
    
    if remove_hashtags:
        text = normalize_hashtags(text)
    
    if remove_punctuation_flag:
        text = remove_punctuation(text)
    
    # Always apply basic normalization last
    text = normalize_text(text)
    
    return text


def batch_normalize(texts):
    """
    Normalize a list of texts efficiently.
    
    Args:
        texts (list): List of text strings
        
    Returns:
        list: List of normalized text strings
    """
    return [normalize_text(text) for text in texts]