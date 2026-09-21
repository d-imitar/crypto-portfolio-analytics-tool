# Crypto Portfolio Analytics Tool

A local-first crypto portfolio analytics dashboard built with Flask, SQLite, React, and TypeScript.

## Features

- Manual crypto position entry
- CSV import for simple portfolio files
- Live market data via CoinGecko with resilient fallback
- Portfolio analytics: total value, P&L, allocation, volatility, beta, Sharpe-like risk score
- AI research panel using Gemini prompt style (with heuristic fallback)
- Local SQLite storage

## Stack

- Backend: Python Flask + SQLAlchemy + SQLite
- Frontend: React + TypeScript + Plotly
- Data: CoinGecko API + graceful static fallback

## Quick start

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### 2) Frontend

```bash
cd frontend
npm install
npm start
```

Then open http://localhost:3000

## Default behavior

On first run, the backend creates a sample crypto portfolio automatically unless `AUTO_SEED_PORTFOLIO=0` is set.

## CSV format

```csv
symbol,name,quantity,average_cost,current_price,category,market_cap_tier,notes
BTC,Bitcoin,1.25,58000,61000,Layer 1,Large Cap,Long-term hold
ETH,Ethereum,4.5,3000,3200,Layer 1,Large Cap,
SOL,Solana,30,150,175,Layer 1,Large Cap,
```

## API overview

- `GET /api/health`
- `GET /api/portfolio/list`
- `GET /api/portfolio/<id>/summary`
- `GET /api/portfolio/<id>/holdings`
- `GET /api/portfolio/<id>/analytics`
- `GET /api/portfolio/<id>/research`
- `POST /api/portfolio/<id>/add-position`
- `POST /api/upload/portfolio-csv`

## Environment variables

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL_NAME=gemini-2.5-flash
AUTO_SEED_PORTFOLIO=1
```

## License

MIT
