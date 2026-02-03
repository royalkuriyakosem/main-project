# PhishDetect Frontend

Web-based user interface for the PhishDetect phishing detection system.

## Project Structure

```
frontend/
├── src/
│   ├── index.html      # Main HTML page
│   ├── css/
│   │   └── style.css   # Cyberpunk-themed styles
│   └── js/
│       └── main.js     # Form handling and API calls
├── public/
│   └── debug_visuals/  # Screenshot storage (auto-generated)
└── README.md
```

## Features

- **Cyberpunk Theme**: Dark glassmorphism design with neon accents
- **URL Analysis Form**: Submit URLs for phishing detection
- **Brand Selection**: Auto-detect or manually select target brand
- **Visual Results**: Progress bars for all score components
- **Responsive Design**: Works on desktop and mobile

## Design Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-dark` | #0a0e17 | Background |
| `--primary-color` | #00f2ff | Cyan accents |
| `--secondary-color` | #7000ff | Purple accents |
| `--danger-color` | #ff0055 | Phishing indicator |
| `--success-color` | #00ff9d | Legitimate indicator |

## Usage

The frontend is served by the FastAPI backend. Access it via:
```
http://localhost:8000
```

## Development

To modify styles:
1. Edit `src/css/style.css`
2. Restart the backend server
