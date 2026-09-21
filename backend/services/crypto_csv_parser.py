import csv
import io


KNOWN_SYMBOLS = {
    'bitcoin': 'BTC',
    'btc': 'BTC',
    'ethereum': 'ETH',
    'eth': 'ETH',
    'solana': 'SOL',
    'sol': 'SOL',
    'binance coin': 'BNB',
    'bnb': 'BNB',
    'xrp': 'XRP',
    'ripple': 'XRP',
    'cardano': 'ADA',
    'ada': 'ADA',
    'dogecoin': 'DOGE',
    'doge': 'DOGE',
    'avalanche': 'AVAX',
    'avax': 'AVAX',
    'chainlink': 'LINK',
    'link': 'LINK',
    'matic': 'MATIC',
    'polygon': 'MATIC',
    'polkadot': 'DOT',
    'dot': 'DOT',
    'cosmos': 'ATOM',
    'atom': 'ATOM',
    'optimism': 'OP',
    'op': 'OP',
    'arbitrum': 'ARB',
    'arb': 'ARB',
    'uniswap': 'UNI',
    'uni': 'UNI',
    'ethena': 'ENA',
    'ena': 'ENA',
    'jito': 'JTO',
    'jito governance token': 'JTO',
    'lido': 'LDO',
    'lido dao': 'LDO',
    'lido-dao': 'LDO',
}


def _coerce_float(value, field_name: str):
    if value is None or str(value).strip() == '':
        return 0.0
    try:
        number = float(str(value).replace(',', ''))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc
    if number != number:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}")
    return number


def _row_value(row, *candidates):
    for candidate in candidates:
        if candidate in row and row.get(candidate) is not None:
            return row.get(candidate)
    normalized = {str(key).strip().lower(): value for key, value in row.items() if key is not None}
    for candidate in candidates:
        match = normalized.get(str(candidate).strip().lower())
        if match is not None:
            return match
    return None


def _normalize_name_key(value):
    return str(value or '').strip().lower().replace('-', ' ').replace('_', ' ')


def _infer_symbol_from_name(name_value):
    if name_value is None:
        return ''
    raw_name = str(name_value).strip()
    if not raw_name:
        return ''
    uppercase = raw_name.upper()
    if uppercase and all(ch.isalpha() or ch in {'-', '_'} for ch in uppercase.replace(' ', '')) and len(raw_name) <= 8:
        if uppercase in {'BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX', 'LINK', 'MATIC', 'DOT', 'ATOM', 'OP', 'ARB', 'UNI', 'ENA', 'JTO', 'LDO'}:
            return uppercase

    normalized = _normalize_name_key(raw_name)
    if normalized in KNOWN_SYMBOLS:
        return KNOWN_SYMBOLS[normalized]

    for key, symbol in KNOWN_SYMBOLS.items():
        if key in normalized:
            return symbol

    return ''


def parse_crypto_csv(file_obj) -> list:
    if file_obj is None:
        raise ValueError('CSV file is required.')

    text = file_obj.read()
    if isinstance(text, bytes):
        text = text.decode('utf-8-sig')
    elif not isinstance(text, str):
        text = str(text)

    if not text.strip():
        raise ValueError('CSV file is empty.')

    stream = io.StringIO(text)
    reader = csv.DictReader(stream)
    if not reader.fieldnames:
        raise ValueError('CSV file is missing a header row.')

    normalized_headers = {str(header).strip().lower() for header in reader.fieldnames if header}
    required = {'symbol', 'quantity'}
    if not required.issubset(normalized_headers):
        if 'coin' in normalized_headers and 'symbol' not in normalized_headers:
            normalized_headers.add('symbol')
        if 'qty' in normalized_headers and 'quantity' not in normalized_headers:
            normalized_headers.add('quantity')
    missing = sorted(required - normalized_headers)
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")

    rows = []
    for row_index, row in enumerate(reader, start=2):
        if not row or not any((value or '').strip() for value in row.values()):
            continue

        symbol = str(_row_value(row, 'symbol', 'Symbol', 'ticker', 'Ticker') or '').strip()
        if not symbol:
            name_candidate = str(_row_value(row, 'name', 'Name', 'coin', 'Coin', 'asset', 'Asset') or '').strip()
            symbol = _infer_symbol_from_name(name_candidate)
        if not symbol:
            continue

        quantity = _coerce_float(_row_value(row, 'quantity', 'Quantity', 'qty', 'Qty') or 0, 'quantity')
        average_cost = _coerce_float(_row_value(row, 'average_cost', 'Average Cost', 'avg_cost', 'Avg Cost', 'cost_basis', 'Cost Basis') or 0, 'average_cost')
        current_price = _coerce_float(_row_value(row, 'current_price', 'Current Price', 'price', 'Price', 'last_price', 'Last Price') or 0, 'current_price')

        if quantity <= 0:
            raise ValueError(f"Row {row_index}: quantity must be greater than zero.")
        if average_cost < 0:
            raise ValueError(f"Row {row_index}: average_cost cannot be negative.")
        if current_price < 0:
            raise ValueError(f"Row {row_index}: current_price cannot be negative.")

        name = str(_row_value(row, 'name', 'Name', 'coin', 'Coin', 'asset', 'Asset') or symbol).strip()
        category = str(_row_value(row, 'category', 'Category', 'sector', 'Sector') or 'Unknown').strip() or 'Unknown'
        market_cap_tier = str(_row_value(row, 'market_cap_tier', 'Market Cap Tier', 'market_cap', 'Market Cap', 'tier', 'Tier') or 'Unknown').strip() or 'Unknown'
        notes = str(_row_value(row, 'notes', 'Notes', 'note', 'Note') or '').strip()

        rows.append({
            'symbol': symbol.upper(),
            'name': name,
            'quantity': quantity,
            'average_cost': average_cost,
            'current_price': current_price,
            'category': category,
            'market_cap_tier': market_cap_tier,
            'notes': notes,
        })

    if not rows:
        raise ValueError('CSV contains no valid crypto positions.')

    return rows
