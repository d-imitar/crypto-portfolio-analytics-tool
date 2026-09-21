import io
import os

import pytest

# Ensure backend services can be imported when running from the repo root.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BACKEND_DIR not in os.sys.path:
    os.sys.path.insert(0, BACKEND_DIR)

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
