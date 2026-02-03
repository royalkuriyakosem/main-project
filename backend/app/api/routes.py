"""
API Routes Module

Contains all FastAPI endpoint definitions for the phishing detection API.
"""

import os
import json
import subprocess
from urllib.parse import urlparse

from fastapi import APIRouter
from pydantic import BaseModel

from app.ml.url_predictor import get_url_score
from app.core.dom_analysis import dom_score
from app.core.visual_analysis import calculate_visual_score

router = APIRouter()

# Paths - will be set from main.py
STATIC_DIR = None
SCRIPTS_DIR = None


class URLRequest(BaseModel):
    url: str
    brand: str = ""


def set_paths(static_dir: str, scripts_dir: str):
    """Set the paths for static files and scripts."""
    global STATIC_DIR, SCRIPTS_DIR
    STATIC_DIR = static_dir
    SCRIPTS_DIR = scripts_dir


def extract_dom_via_puppeteer(url: str, output_path: str):
    """Extract DOM tree from a URL using Puppeteer."""
    puppeteer_path = os.path.join(SCRIPTS_DIR, "puppeteer_script.js")
    
    try:
        print(f"Running subprocess for URL: {url}")
        result = subprocess.run(
            ["node", puppeteer_path, url, output_path],
            check=True, timeout=60,
            capture_output=True, text=True
        )
        print(f"Subprocess stdout: {result.stdout[:500] if result.stdout else 'None'}...")
        
        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                dom_tree = json.load(f)
            print(f"Tree loaded! Size: {len(json.dumps(dom_tree)) / 1000:.1f} KB")
            return dom_tree
        else:
            print("Temp file not created!")
            return None
    except subprocess.TimeoutExpired:
        print("Subprocess timeout!")
        return None
    except Exception as e:
        print(f"Subprocess error: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None


def get_dom_and_visual_score(url: str, brand: str):
    """
    Get DOM similarity and visual similarity scores.
    
    Returns:
        tuple: (dom_score, visual_score, detected_brand)
    """
    debug_dir = os.path.join(STATIC_DIR, "debug_visuals")
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)
    
    temp_test_path = "temp_test_dom.json"
    temp_brand_path = "temp_brand_dom.json"
    temp_test_img = os.path.join(debug_dir, "temp_test_dom.png")
    temp_brand_img = os.path.join(debug_dir, "temp_brand_dom.png")
    
    # Fetch test tree & screenshot
    dom_tree = extract_dom_via_puppeteer(url, temp_test_path)
    if not dom_tree:
        return None, None, brand
    
    # Move screenshot if created in root
    root_test_img = temp_test_path.replace('.json', '.png')
    if os.path.exists(root_test_img):
        os.rename(root_test_img, temp_test_img)
    
    # Auto-detect brand if not provided
    if not brand:
        print("DEBUG: Auto-detecting brand...")
        if isinstance(dom_tree, dict):
            page_title = dom_tree.get("title", "").lower()
            print(f"DEBUG: Page Title: '{page_title}'")
            
            brand_keywords = ["facebook", "paypal", "google", "amazon", "instagram", "netflix"]
            for keyword in brand_keywords:
                if keyword in page_title:
                    brand = keyword
                    break
            
            if not brand:
                print("DEBUG: Brand not detected.")
                return None, None, None
            
            print(f"DEBUG: Detected Brand: {brand}")
    
    # Fetch brand tree & screenshot
    brand_url = f"https://www.{brand}.com"
    brand_tree = extract_dom_via_puppeteer(brand_url, temp_brand_path)
    
    # Move brand screenshot
    root_brand_img = temp_brand_path.replace('.json', '.png')
    if os.path.exists(root_brand_img):
        os.rename(root_brand_img, temp_brand_img)
    
    if not brand_tree:
        if os.path.exists(temp_test_path):
            os.remove(temp_test_path)
        return None, None, brand
    
    # Compute scores
    d_score = dom_score(temp_test_path, temp_brand_path)
    v_score = calculate_visual_score(temp_test_img, temp_brand_img)
    print(f"Visual Score: {v_score:.4f}")
    
    # Cleanup JSONs but KEEP images for debug
    for f in [temp_test_path, temp_brand_path]:
        if os.path.exists(f):
            os.remove(f)
    
    return d_score, v_score, brand


@router.post("/predict")
def predict(data: URLRequest):
    """
    Analyze a URL for phishing indicators.
    
    Combines URL-based ML prediction with DOM and visual similarity analysis.
    """
    try:
        url = data.url
        brand = data.brand.lower() if data.brand else ""
        
        # Phase 1: URL Score
        url_score = get_url_score(url)
        
        # Phase 2: DOM & Visual Score
        d_score, v_score, detected_brand = get_dom_and_visual_score(url, brand)
        
        # Update brand if auto-detected
        if not brand and detected_brand:
            brand = detected_brand
        
        # Domain validation
        domain = urlparse(url).netloc.lower()
        if brand:
            expected_domain = f"{brand}.com"
            is_domain_match = expected_domain in domain
        else:
            is_domain_match = False
        
        # Fusion Logic
        if d_score is None:
            # Site Unreachable -> Rely 100% on URL Model
            print("DEBUG: Site Unreachable. Fallback to URL Model.")
            d_score = 0.0
            v_score = 0.0
            similarity_score = 0.0
            phishing_prob = url_score
        else:
            # Site Reachable -> Hybrid Logic
            if v_score and v_score > 0:
                similarity_score = (d_score * 0.5) + (v_score * 0.5)
            else:
                similarity_score = d_score
                v_score = 0.0
            
            if is_domain_match:
                phishing_prob = url_score * 0.1
            else:
                phishing_prob = (url_score * 0.2) + (similarity_score * 0.8)
        
        print(f"DEBUG: URL={url}, Brand={brand}")
        print(f"DEBUG: Domain Match={is_domain_match}")
        print(f"DEBUG: URL Score={url_score}")
        print(f"DEBUG: DOM Score={d_score}")
        print(f"DEBUG: Visual Score={v_score}")
        print(f"DEBUG: Similarity Score={similarity_score}")
        print(f"DEBUG: Phishing Prob (Hybrid)={phishing_prob}")
        
        threshold = 0.5
        label = "Phishing" if phishing_prob > threshold else "Legitimate"
        
        return {
            "url": url,
            "brand": brand,
            "domain_match": is_domain_match,
            "url_score": url_score,
            "dom_score": d_score,
            "visual_score": v_score,
            "similarity_score": round(similarity_score, 4),
            "hybrid_score": round(phishing_prob, 4),
            "threshold": threshold,
            "final_label": label
        }
    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}
