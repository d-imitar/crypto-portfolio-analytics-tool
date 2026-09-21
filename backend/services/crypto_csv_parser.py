import csv
import io


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
    required = {'symbol', 'quantity', 'average_cost'}
    missing = sorted(required - normalized_headers)
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")

    rows = []
    for row_index, row in enumerate(reader, start=2):
        if not row or not any((value or '').strip() for value in row.values()):
            continue

        symbol = str(row.get('symbol') or row.get('Symbol') or '').strip()
        if not symbol:
            continue

        quantity = _coerce_float(row.get('quantity') or 0, 'quantity')
        average_cost = _coerce_float(row.get('average_cost') or 0, 'average_cost')
        current_price = _coerce_float(row.get('current_price') or 0, 'current_price')

        if quantity <= 0:
            raise ValueError(f"Row {row_index}: quantity must be greater than zero.")
        if average_cost < 0:
            raise ValueError(f"Row {row_index}: average_cost cannot be negative.")
        if current_price < 0:
            raise ValueError(f"Row {row_index}: current_price cannot be negative.")

        rows.append({
            'symbol': symbol.upper(),
            'name': (row.get('name') or row.get('Name') or symbol or '').strip(),
            'quantity': quantity,
            'average_cost': average_cost,
            'current_price': current_price,
            'category': (row.get('category') or row.get('Category') or 'Unknown').strip() or 'Unknown',
            'market_cap_tier': (row.get('market_cap_tier') or row.get('market_cap') or 'Unknown').strip() or 'Unknown',
            'notes': (row.get('notes') or row.get('Notes') or '').strip(),
        })

    if not rows:
        raise ValueError('CSV contains no valid crypto positions.')

    return rows
