# Models

This directory contains trained machine learning models and related files.

## Structure

```
models/
├── url_model/           # URL-based phishing detection model
│   ├── hybrid_best_model.keras   # Trained Keras model
│   ├── tokenizer.pkl    # URL tokenizer
│   └── url_feature_scaler.pkl    # Feature scaler
└── fusion/              # Fusion scoring components
    ├── fusion.py        # Fusion score calculator
    ├── sample_data.json # Test data
    └── thresholds.json  # Scoring thresholds
```

## URL Model

A hybrid deep learning model that analyzes URL characteristics:
- URL length and structure
- Special character patterns
- Suspicious keyword detection
- TLD analysis

## Usage

Models are loaded by the backend service during startup. See `backend/app/ml/url_predictor.py`.
