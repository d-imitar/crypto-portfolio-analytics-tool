import csv
import io


def parse_crypto_csv(file_obj) -> list:
    text = file_obj.read().decode('utf-8-sig')
    stream = io.StringIO(text)
    reader = csv.DictReader(stream)
    rows = []
    for row in reader:
        if not row:
            continue
        if not row.get('symbol'):
            continue
        rows.append({
            'symbol': str(row.get('symbol', '')).strip().upper(),
            'name': (row.get('name') or row.get('symbol') or '').strip(),
            'quantity': float(row.get('quantity') or 0),
            'average_cost': float(row.get('average_cost') or 0),
            'current_price': float(row.get('current_price') or 0),
            'category': (row.get('category') or 'Unknown').strip(),
            'market_cap_tier': (row.get('market_cap_tier') or 'Unknown').strip(),
            'notes': (row.get('notes') or '').strip(),
        })
    return rows
