# PhishDetect Backend

FastAPI-based phishing detection backend service.

## Features

- **URL Analysis**: ML-based URL feature extraction and prediction
- **DOM Analysis**: Puppeteer-powered DOM tree extraction and comparison
- **Visual Analysis**: SSIM-based screenshot similarity detection
- **Fusion Scoring**: Hybrid scoring combining all analysis methods

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py     # API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── dom_analysis.py
│   │   ├── visual_analysis.py
│   │   └── tree_edit_distance.py
│   ├── ml/
│   │   ├── __init__.py
│   │   └── url_predictor.py
│   └── utils/
│       └── __init__.py
├── scripts/
│   └── puppeteer_script.js
├── Dockerfile
├── requirements.txt
└── package.json
```

## Setup

### Local Development

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for Puppeteer)
npm install

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Docker

```bash
docker build -t phishdetect-backend .
docker run -p 8000:8000 phishdetect-backend
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve frontend |
| GET | `/health` | Health check |
| POST | `/predict` | Analyze URL for phishing |

### POST /predict

Request:
```json
{
  "url": "https://example.com",
  "brand": "paypal"  // Optional, auto-detect if empty
}
```

Response:
```json
{
  "url": "https://example.com",
  "brand": "paypal",
  "domain_match": false,
  "url_score": 0.85,
  "dom_score": 0.72,
  "visual_score": 0.68,
  "similarity_score": 0.70,
  "hybrid_score": 0.73,
  "threshold": 0.5,
  "final_label": "Phishing"
}
```
