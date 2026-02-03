"""
URL Feature Extraction and ML Prediction Module

This module handles:
- URL feature extraction (length, digits, special chars, etc.)
- Loading the trained Keras model
- Making phishing predictions on URLs
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
    
    Returns:
        float: Score between 0.0 (safe) and 1.0 (likely phishing)
    """
    if model is None:
        raise RuntimeError("Model not initialized. Call initialize_model() first.")
    
    seq = tokenizer.texts_to_sequences([url])
    padded = tf.keras.preprocessing.sequence.pad_sequences(seq, maxlen=200)
    feat = np.array([list(extract_features(url).values())])
    feat = scaler.transform(feat)
    pred = model.predict([padded, feat])[0][0]
    
    return float(pred)
