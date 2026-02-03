# PhishDetect

A Hybrid URL-DOM Based Phishing Detection Framework with machine learning, DOM analysis, and visual similarity detection.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

## Overview

PhishDetect uses a multi-layered approach to detect phishing websites:

1. **URL Analysis** - ML model analyzes URL patterns and characteristics
2. **DOM Analysis** - Compares page structure with legitimate brand templates
3. **Visual Analysis** - Uses SSIM to detect visual clones
4. **Fusion Scoring** - Combines all signals for final prediction

## Project Structure

```
main-project/
├── backend/          # FastAPI Python backend
│   ├── app/          # Application code
│   │   ├── api/      # API routes
│   │   ├── core/     # Analysis modules
│   │   └── ml/       # ML prediction
│   ├── scripts/      # Puppeteer scripts
│   └── Dockerfile
├── frontend/         # Web interface
│   └── src/          # HTML, CSS, JS
├── models/           # ML models
│   ├── url_model/    # URL prediction model
│   └── fusion/       # Fusion scoring
├── docs/             # Documentation
└── docker-compose.yml
```

## Quick Start

### Using Docker (Recommended)

```bash
# Build and run
docker-compose up --build

# Access the app
open http://localhost:8000
```

### Local Development

```bash
# Backend setup
cd backend
pip install -r requirements.txt
npm install

# Run server
uvicorn app.main:app --reload --port 8000
```

## API Usage

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "brand": "paypal"}'
```

## Documentation

- [Architecture & Flow](docs/architecture_and_flow.md)
- [Project Overview](docs/project_overview.md)
- [Run Instructions](docs/run_instructions.md)
- [Innovation Roadmap](docs/innovation_roadmap.md)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI, Python 3.12 |
| ML | TensorFlow, scikit-learn |
| DOM Extraction | Puppeteer, Node.js |
| Visual Analysis | OpenCV, scikit-image |
| Frontend | HTML, CSS, JavaScript |
| Containerization | Docker |

## License

MIT# main-project
