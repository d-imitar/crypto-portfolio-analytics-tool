import io
import os

import pytest

# Ensure backend services can be imported when running from the repo root.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BACKEND_DIR not in os.sys.path:
    os.sys.path.insert(0, BACKEND_DIR)

from app import app
from database import db
from models import Portfolio, Holding
from services.crypto_csv_parser import parse_crypto_csv


def test_parse_csv_valid_rows():
    payload = (
        'symbol,name,quantity,average_cost,current_price,category,market_cap_tier,notes\n'
        'BTC,Bitcoin,1.5,50000,60000,Layer 1,Large Cap,long-term\n'
        'ETH,Ethereum,4,3000,3200,Layer 1,Large Cap,\n'
    )

    rows = parse_crypto_csv(io.BytesIO(payload.encode('utf-8')))

    assert len(rows) == 2
    assert rows[0]['symbol'] == 'BTC'
    assert rows[0]['quantity'] == 1.5
    assert rows[1]['name'] == 'Ethereum'


def test_parse_csv_rejects_invalid_numeric_values():
    payload = 'symbol,name,quantity,average_cost,current_price\nBTC,Bitcoin,invalid,50000,60000\n'

    with pytest.raises(ValueError, match='Invalid numeric value'):
        parse_crypto_csv(io.BytesIO(payload.encode('utf-8')))


def test_parse_csv_supports_common_simple_headers():
    payload = 'Symbol,Coin,Quantity\nJTO,Jito,3500\nENA,Ethena,5000\n'
    rows = parse_crypto_csv(io.BytesIO(payload.encode('utf-8')))
    assert len(rows) == 2
    assert rows[0]['symbol'] == 'JTO'
    assert rows[0]['name'] == 'Jito'
    assert rows[0]['quantity'] == 3500
    assert rows[0]['average_cost'] == 0.0
    assert rows[0]['current_price'] == 0.0


def test_parse_csv_infers_symbol_from_coin_name_when_symbol_is_missing():
    payload = 'Coin,Quantity,Average Cost\nLido,1000,1.2\n'
    rows = parse_crypto_csv(io.BytesIO(payload.encode('utf-8')))
    assert len(rows) == 1
    assert rows[0]['symbol'] == 'LDO'
    assert rows[0]['name'] == 'Lido'
    assert rows[0]['quantity'] == 1000.0
    assert rows[0]['average_cost'] == 1.2


def test_csv_import_replaces_existing_holdings_and_enriches_prices():
    with app.app_context():
        Holding.query.delete()
        Portfolio.query.delete()
        db.session.commit()

        portfolio = Portfolio(name='Test portfolio', base_currency='USD')
        db.session.add(portfolio)
        db.session.commit()

        stale_holding = Holding(
            portfolio_id=portfolio.id,
            symbol='BTC',
            name='Bitcoin',
            quantity=1,
            average_cost=50000,
            current_price=62000,
            current_value=62000,
            cost_basis=50000,
            unrealized_pnl=12000,
        )
        db.session.add(stale_holding)
        db.session.commit()

        payload = 'Symbol,Coin,Quantity\nJTO,Jito,3500\nENA,Ethena,5000\n'
        response = app.test_client().post(
            '/api/upload/portfolio-csv',
            data={'portfolio_id': str(portfolio.id), 'file': (io.BytesIO(payload.encode('utf-8')), 'crypto-portfolio.csv')},
            content_type='multipart/form-data',
        )

        assert response.status_code == 200, response.get_data(as_text=True)
        data = response.get_json()
        assert data['rows_imported'] == 2

        holdings = Holding.query.filter_by(portfolio_id=portfolio.id).order_by(Holding.symbol.asc()).all()
        assert [holding.symbol for holding in holdings] == ['ENA', 'JTO']
        assert all(holding.current_value > 0 for holding in holdings)
        assert all(holding.current_price > 0 for holding in holdings)

