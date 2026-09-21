import csv
import io
import os

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from database import db
from models import Portfolio, Holding
from services.crypto_csv_parser import parse_crypto_csv

bp = Blueprint('upload', __name__, url_prefix='/api/upload')


@bp.route('/portfolio-csv', methods=['POST'])
def upload_portfolio_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'Only CSV files are allowed'}), 400

    portfolio_id = request.form.get('portfolio_id', type=int)
    portfolio_name = request.form.get('portfolio_name') or os.path.splitext(file.filename)[0]

    if portfolio_id:
        portfolio = Portfolio.query.get_or_404(portfolio_id)
    else:
        portfolio = Portfolio.query.order_by(Portfolio.created_at.desc()).first()
        if not portfolio:
            portfolio = Portfolio(name=portfolio_name or 'Imported crypto portfolio', base_currency='USD')
            db.session.add(portfolio)
            db.session.flush()
        else:
            portfolio.name = portfolio_name or portfolio.name

    try:
        rows = parse_crypto_csv(file)
    except Exception as exc:
        return jsonify({'error': f'Unable to parse CSV: {exc}'}), 400

    if not rows:
        return jsonify({'error': 'CSV contains no valid crypto positions'}), 400

    for row in rows:
        row = {**row, 'symbol': str(row['symbol']).upper()}
        existing = Holding.query.filter_by(portfolio_id=portfolio.id, symbol=row['symbol']).first()
        if existing:
            existing.name = row['name']
            existing.quantity = float(row['quantity'])
            existing.average_cost = float(row['average_cost'])
            existing.current_price = float(row.get('current_price') or 0)
            existing.current_value = float(row['quantity']) * float(row.get('current_price') or 0)
            existing.cost_basis = float(row['quantity']) * float(row.get('average_cost') or 0)
            existing.unrealized_pnl = existing.current_value - existing.cost_basis
            existing.category = row.get('category') or existing.category or 'Unknown'
            existing.market_cap_tier = row.get('market_cap_tier') or existing.market_cap_tier or 'Unknown'
            existing.notes = row.get('notes') or existing.notes or ''
        else:
            current_price = float(row.get('current_price') or 0)
            quantity = float(row['quantity'])
            average_cost = float(row['average_cost'])
            holding = Holding(
                portfolio_id=portfolio.id,
                symbol=row['symbol'],
                name=row['name'],
                category=row.get('category') or 'Unknown',
                market_cap_tier=row.get('market_cap_tier') or 'Unknown',
                quantity=quantity,
                average_cost=average_cost,
                current_price=current_price,
                current_value=quantity * current_price,
                cost_basis=quantity * average_cost,
                unrealized_pnl=(quantity * current_price) - (quantity * average_cost),
                realized_pnl=0,
                notes=row.get('notes') or '',
            )
            db.session.add(holding)

    db.session.commit()
    return jsonify({'status': 'success', 'portfolio': portfolio.to_dict(), 'rows_imported': len(rows)})
