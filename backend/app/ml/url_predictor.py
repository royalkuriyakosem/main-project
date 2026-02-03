"""
URL Feature Extraction and ML Prediction Module

This module handles:
- URL feature extraction (length, digits, special chars, etc.)
- Loading the trained Keras model
- Making phishing predictions on URLs
- Typosquatting detection for brand impersonation
"""

import os
import re
import pickle
import numpy as np
import tensorflow as tf
import tldextract

# Define paths - will be set from main.py
MODEL_DIR = None
model = None
tokenizer = None
scaler = None

# Known brands for typosquatting detection
KNOWN_BRANDS = [
    "facebook", "google", "amazon", "paypal", "instagram", "netflix",
    "microsoft", "apple", "twitter", "linkedin", "dropbox", "spotify",
    "whatsapp", "telegram", "outlook", "yahoo", "ebay", "chase", "wellsfargo",
    "bankofamerica", "citibank", "usbank", "capitalone"
]


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein (edit) distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def detect_typosquatting(domain: str) -> tuple:
    """
    Detect if a domain is a typosquatting attempt on a known brand.
    
    Returns:
        tuple: (is_typosquatting, closest_brand, similarity_score)
    """
    domain_lower = domain.lower().replace("-", "").replace("_", "")
    
    # Quick check: if domain exactly matches a brand, it's legitimate
    for brand in KNOWN_BRANDS:
        if domain_lower == brand:
            return (False, brand, 1.0)
    
    # Check for typosquatting (similar but not exact match)
    best_match = None
    min_distance = float('inf')
    
    for brand in KNOWN_BRANDS:
        # Check if brand is contained or similar
        if brand in domain_lower and domain_lower != brand:
            # Brand name is embedded (e.g., "facebook-login", "myfacebook")
            return (True, brand, 0.8)
        
        # Calculate edit distance for close matches
        distance = levenshtein_distance(domain_lower, brand)
        max_len = max(len(domain_lower), len(brand))
        
        # Consider it similar if edit distance is small relative to length
        # Allow up to 3 edits for longer words, 2 for shorter
        threshold = 3 if max_len > 6 else 2
        
        if distance <= threshold and distance > 0:
            similarity = 1 - (distance / max_len)
            if distance < min_distance:
                min_distance = distance
                best_match = (brand, similarity)
    
    if best_match:
        return (True, best_match[0], best_match[1])
    
    return (False, None, 0.0)


def initialize_model(models_dir: str):
    """Initialize the URL prediction model and related objects."""
    global MODEL_DIR, model, tokenizer, scaler
    
    MODEL_DIR = os.path.join(models_dir, "url_model")
    
    model_path = os.path.join(MODEL_DIR, "hybrid_best_model.keras")
    tokenizer_path = os.path.join(MODEL_DIR, "tokenizer.pkl")
    scaler_path = os.path.join(MODEL_DIR, "url_feature_scaler.pkl")
    
    model = tf.keras.models.load_model(model_path)
    with open(tokenizer_path, "rb") as f:
        tokenizer = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    
    print("✓ URL model loaded successfully!")


def extract_features(url: str) -> dict:
    """Extract numerical features from a URL for ML prediction."""
    url = url.lower()
    if not url.startswith("http"):
        url = "http://" + url
    
    ext = tldextract.extract(url)
    domain = ext.domain
    suffix = ext.suffix
    hostname = domain + "." + suffix if suffix else domain
    
    return {
        "url_length": len(url),
        "count_digits": sum(c.isdigit() for c in url),
        "count_special": sum(c in "-@_./=:" for c in url),
        "has_login": int("login" in url),
        "has_secure": int("secure" in url),
        "has_bank": int("bank" in url),
        "tld_is_suspicious": int(suffix in ["xyz", "top", "help", "club"]),
        "is_ip": int(bool(re.match(r"^\d+\.\d+\.\d+\.\d+$", hostname))),
        "subdomain_count": ext.subdomain.count(".") + (1 if ext.subdomain else 0)
    }


def get_url_score(url: str) -> float:
    """
    Get the phishing probability score for a URL.
    
    Combines ML model prediction with typosquatting detection.
    
    Returns:
        float: Score between 0.0 (safe) and 1.0 (likely phishing)
    """
    if model is None:
        raise RuntimeError("Model not initialized. Call initialize_model() first.")
    
    # Get ML model prediction
    seq = tokenizer.texts_to_sequences([url])
    padded = tf.keras.preprocessing.sequence.pad_sequences(seq, maxlen=200)
    feat = np.array([list(extract_features(url).values())])
    feat = scaler.transform(feat)
    ml_pred = model.predict([padded, feat])[0][0]
    
    # Check for typosquatting
    ext = tldextract.extract(url)
    domain = ext.domain
    
    is_typosquat, matched_brand, similarity = detect_typosquatting(domain)
    
    if is_typosquat:
        # Typosquatting detected - boost the phishing score significantly
        print(f"⚠ TYPOSQUATTING DETECTED: '{domain}' looks like '{matched_brand}' (similarity: {similarity:.2f})")
        # Use maximum of ML prediction and typosquatting suspicion score
        typosquat_score = 0.85  # High suspicion for typosquatting
        final_score = max(float(ml_pred), typosquat_score)
    else:
        final_score = float(ml_pred)
    
    return final_score

