"""
URL Feature Extraction and ML Prediction Module

This module handles:
- URL feature extraction (length, digits, special chars, etc.)
- Loading the trained Keras model
- Making phishing predictions on URLs
- Typosquatting & brand impersonation detection
"""

import os
import re
import pickle
import numpy as np
import tensorflow as tf
import tldextract

# ==============================
# Global model objects
# ==============================
MODEL_DIR = None
model = None
tokenizer = None
scaler = None

# ==============================
# Known brands for impersonation
# ==============================
KNOWN_BRANDS = [
    "facebook", "google", "amazon", "paypal", "instagram", "netflix",
    "microsoft", "apple", "twitter", "linkedin", "dropbox", "spotify",
    "whatsapp", "telegram", "outlook", "yahoo", "ebay",
    "chase", "wellsfargo", "bankofamerica", "citibank",
    "usbank", "capitalone",
    "github", "ktu", "fisat",
    "paytm", "flipkart", "zomato", "swiggy", "ubereats",
    "dominos", "kfc", "mcdonalds",
    "gpay", "phonepe", "googlepay",
    "axisbank", "hdfc", "icici"
]

# ==============================
# Utility: Levenshtein Distance
# ==============================
def levenshtein_distance(s1: str, s2: str) -> int:
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

# ==============================
# Brand detection from URL
# ==============================
def detect_brand_from_url(url: str) -> tuple:
    """
    Detect impersonated brand from URL.
    Returns (brand_name or None, confidence_score)
    """
    ext = tldextract.extract(url)
    domain = ext.domain.lower().replace("-", "").replace("_", "")

    best_brand = None
    best_score = 0.0

    for brand in KNOWN_BRANDS:
        # Direct substring match
        if brand in domain:
            return brand, 0.9

        # Similarity via edit distance
        distance = levenshtein_distance(domain, brand)
        max_len = max(len(domain), len(brand))
        similarity = 1 - (distance / max_len)

        if similarity > best_score and similarity > 0.75:
            best_score = similarity
            best_brand = brand

    if best_brand:
        return best_brand, best_score

    return None, 0.0

# ==============================
# Typosquatting detection
# ==============================
def detect_typosquatting(domain: str) -> tuple:
    """
    Returns:
    (is_typosquatting, closest_brand, similarity_score)
    """
    domain_clean = domain.lower().replace("-", "").replace("_", "")

    for brand in KNOWN_BRANDS:
        if domain_clean == brand:
            return False, brand, 1.0

    best_match = None
    min_distance = float("inf")

    for brand in KNOWN_BRANDS:
        if brand in domain_clean and domain_clean != brand:
            return True, brand, 0.8

        distance = levenshtein_distance(domain_clean, brand)
        max_len = max(len(domain_clean), len(brand))
        threshold = 3 if max_len > 6 else 2

        if 0 < distance <= threshold:
            similarity = 1 - (distance / max_len)
            if distance < min_distance:
                min_distance = distance
                best_match = (brand, similarity)

    if best_match:
        return True, best_match[0], best_match[1]

    return False, None, 0.0

# ==============================
# Model initialization
# ==============================
def initialize_model(models_dir: str):
    global MODEL_DIR, model, tokenizer, scaler

    MODEL_DIR = os.path.join(models_dir, "url_model")

    model_path = os.path.join(MODEL_DIR, "hybrid_best_model.keras")
    tokenizer_path = os.path.join(MODEL_DIR, "tokenizer.pkl")
    scaler_path = os.path.join(MODEL_DIR, "url_feature_scaler.pkl")

    if not os.path.exists(model_path):
        raise FileNotFoundError("URL model not found")

    model = tf.keras.models.load_model(model_path)

    with open(tokenizer_path, "rb") as f:
        tokenizer = pickle.load(f)

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    print("✓ URL phishing model initialized")

# ==============================
# URL Feature Extraction
# ==============================
def extract_features(url: str) -> dict:
    url = url.lower()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    ext = tldextract.extract(url)
    domain = ext.domain
    suffix = ext.suffix
    hostname = f"{domain}.{suffix}" if suffix else domain

    return {
        "url_length": len(url),
        "count_digits": sum(c.isdigit() for c in url),
        "count_special": sum(c in "-@_./=:" for c in url),
        "has_login": int("login" in url),
        "has_secure": int("secure" in url),
        "has_bank": int("bank" in url),
        "tld_is_suspicious": int(suffix in {"xyz", "top", "help", "club"}),
        "is_ip": int(bool(re.fullmatch(r"\d+\.\d+\.\d+\.\d+", hostname))),
        "subdomain_count": ext.subdomain.count(".") + (1 if ext.subdomain else 0)
    }

# ==============================
# Main prediction function
# ==============================
def get_url_score(url: str) -> dict:
    """
    Returns:
    {
        url_score: phishing probability (0–1),
        detected_brand: brand name or None,
        brand_confidence: confidence score
    }
    """
    if model is None or tokenizer is None or scaler is None:
        raise RuntimeError("URL model not initialized")

    # Text sequence
    seq = tokenizer.texts_to_sequences([url])
    padded = tf.keras.preprocessing.sequence.pad_sequences(
        seq, maxlen=200, padding="post"
    )

    # Numerical features
    features = extract_features(url)
    feature_array = scaler.transform([list(features.values())])

    # Prediction
    ml_score = float(model.predict([padded, feature_array], verbose=0)[0][0])

    # Brand impersonation boost
    detected_brand, confidence = detect_brand_from_url(url)
    if detected_brand:
        ml_score = max(ml_score, 0.85)

    return {
        "url_score": round(ml_score, 4),
        "detected_brand": detected_brand,
        "brand_confidence": round(confidence, 3)
    }
