"""
API Routes Module
Frontend-safe, non-blocking, deterministic outputs
"""

import os
import json
import subprocess
from urllib.parse import urlparse
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.ml.url_predictor import get_url_score
from app.core.dom_analysis import dom_score
from app.core.visual_analysis import calculate_visual_score

router = APIRouter()

STATIC_DIR = None
SCRIPTS_DIR = None


class URLRequest(BaseModel):
    url: str
    brand: Optional[str] = ""


def set_paths(static_dir: str, scripts_dir: str):
    global STATIC_DIR, SCRIPTS_DIR
    STATIC_DIR = static_dir
    SCRIPTS_DIR = scripts_dir


# -----------------------------
# Puppeteer DOM Extraction
# -----------------------------
def extract_dom_via_puppeteer(url: str, output_path: str, timeout=25):
    puppeteer_path = os.path.join(SCRIPTS_DIR, "puppeteer_script.js")

    try:
        subprocess.run(
            ["node", puppeteer_path, url, output_path],
            timeout=timeout,
            capture_output=True,
            text=True
        )

        if not os.path.exists(output_path):
            return None

        with open(output_path, "r") as f:
            return json.load(f)

    except Exception:
        return None


# -----------------------------
# DOM + Visual Scoring
# -----------------------------
def get_dom_and_visual_score(url: str, brand: str):
    debug_dir = os.path.join(STATIC_DIR, "debug_visuals")
    os.makedirs(debug_dir, exist_ok=True)

    test_dom = "temp_test_dom.json"
    brand_dom = "temp_brand_dom.json"

    test_img = os.path.join(debug_dir, "temp_test_dom.png")
    brand_img = os.path.join(debug_dir, "temp_brand_dom.png")

    dom_tree = extract_dom_via_puppeteer(url, test_dom)
    if not dom_tree:
        return None, None, brand

    # Auto brand detection from title
    if not brand and isinstance(dom_tree, dict):
        title = dom_tree.get("title", "").lower()
        for b in ["google", "paypal", "amazon", "facebook", "instagram", "netflix"]:
            if b in title:
                brand = b
                break

    if not brand:
        return None, None, None

    brand_tree = extract_dom_via_puppeteer(f"https://www.{brand}.com", brand_dom)
    if not brand_tree:
        return None, None, brand

    d_score = float(dom_score(test_dom, brand_dom))

    try:
        v_score = float(calculate_visual_score(test_img, brand_img))
    except Exception:
        v_score = 0.0

    return d_score, v_score, brand


# -----------------------------
# PREDICT ROUTE (FIXED)
# -----------------------------
@router.post("/predict")
def predict(data: URLRequest):
    url = data.url
    brand = data.brand.lower() if data.brand else ""

    # ---------- SAFE DEFAULTS ----------
    url_score = 0.0
    d_score = 0.0
    v_score = 0.0
    similarity_score = 0.0
    phishing_prob = 0.0
    detected_brand = brand

    # ---------- PHASE 1: URL ----------
    url_result = get_url_score(url)

    url_score = float(url_result["url_score"])
    if url_result["detected_brand"]:
        detected_brand = url_result["detected_brand"]

    # ---------- PHASE 2: DOM + VISUAL ----------
    d, v, detected = get_dom_and_visual_score(url, detected_brand)

    if detected:
        detected_brand = detected

    if d is not None:
        d_score = float(d)
        v_score = float(v)
        similarity_score = 0.5 * d_score + 0.5 * v_score

    # ---------- DOMAIN CHECK ----------
# Allow brand anywhere in the domain (safer than strict .com)
    domain = urlparse(url).netloc.lower()

    parts = domain.split(".")   # ✅ ALWAYS defined

    if detected_brand:
        is_domain_match = any(detected_brand in part for part in parts)
    else:
        is_domain_match = False



    # ---------- FUSION (XGBoost-style math, no model) ----------
    if d is None:
        phishing_prob = max(url_score, 0.6)
        if detected_brand and not is_domain_match:
            phishing_prob = max(phishing_prob, 0.9)
    else:
        if is_domain_match:
            phishing_prob = url_score * 0.1
        else:
            phishing_prob = (0.2 * url_score) + (0.8 * similarity_score)

    phishing_prob = min(max(phishing_prob, 0.0), 1.0)
    label = "Phishing" if phishing_prob > 0.5 else "Legitimate"

    return {
        "url": url,
        "brand": detected_brand or "",
        "domain_match": is_domain_match,
        "url_score": round(url_score, 4),
        "dom_score": round(d_score, 4),
        "visual_score": round(v_score, 4),
        "similarity_score": round(similarity_score, 4),
        "hybrid_score": round(phishing_prob, 4),
        "threshold": 0.5,
        "final_label": label
    }
