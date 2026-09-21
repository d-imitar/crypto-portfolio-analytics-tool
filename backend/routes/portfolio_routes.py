from flask import Blueprint, jsonify, request
from database import db
from models import Portfolio, Holding, Performance
from services.crypto_csv_parser import parse_crypto_csv
from services.crypto_market_data import CryptoMarketDataService
from services.portfolio_calculator import PortfolioCalculator
from services.crypto_research import generate_portfolio_research

bp = Blueprint('portfolio', __name__, url_prefix='/api/portfolio')


def _empty_summary(portfolio):
    return {
        'total_value': 0,
        'long_value': 0,
        'short_value': 0,
        'num_holdings': 0,
        'position_weights': [],
        'category_exposure': {'breakdown': {}, 'total': 0, 'percentages': {}},
        'market_cap_exposure': {'breakdown': {}, 'total': 0, 'percentages': {}},
        'volatility': {'std_dev': 0.0, 'volatility': 0.0},
        'performance': {
            'total_unrealized': 0,
            'total_realized': 0,
            'total_pnl': 0,
            'ytd_return_pct': 0,
            'cost_basis': 0,
        },
        'base_currency': portfolio.base_currency if portfolio else 'USD',
    }


def ensure_default_portfolio():
    portfolio = Portfolio.query.filter_by(name='Default crypto portfolio').first()
    if portfolio:
        return portfolio

    portfolio = Portfolio(name='Default crypto portfolio', base_currency='USD', description='Seed portfolio')
    db.session.add(portfolio)
    db.session.flush()

    sample_holdings = [
        {'symbol': 'BTC', 'name': 'Bitcoin', 'quantity': 0.8, 'average_cost': 52000, 'current_price': 62000, 'category': 'Layer 1', 'market_cap_tier': 'Large Cap', 'notes': 'Core BTC position'},
        {'symbol': 'ETH', 'name': 'Ethereum', 'quantity': 4.2, 'average_cost': 2800, 'current_price': 3200, 'category': 'Layer 1', 'market_cap_tier': 'Large Cap', 'notes': 'Execution layer'},
        {'symbol': 'SOL', 'name': 'Solana', 'quantity': 32, 'average_cost': 120, 'current_price': 155, 'category': 'Layer 1', 'market_cap_tier': 'Large Cap', 'notes': 'High throughput'},
    ]
    for row in sample_holdings:
        current_price = float(row['current_price'])
        quantity = float(row['quantity'])
        average_cost = float(row['average_cost'])
        current_value = quantity * current_price
        holding = Holding(
            portfolio_id=portfolio.id,
            symbol=row['symbol'],
            name=row['name'],
            category=row['category'],
            market_cap_tier=row['market_cap_tier'],
            quantity=quantity,
            average_cost=average_cost,
            current_price=current_price,
            current_value=current_value,
            cost_basis=quantity * average_cost,
            unrealized_pnl=current_value - (quantity * average_cost),
            realized_pnl=0,
            notes=row.get('notes', ''),
        )
        db.session.add(holding)

    db.session.commit()
    return portfolio


@bp.route('/list', methods=['GET'])
def list_portfolios():
    portfolios = Portfolio.query.order_by(Portfolio.created_at.desc()).all()
    return jsonify({'portfolios': [portfolio.to_dict() for portfolio in portfolios]})


@bp.route('/<int:portfolio_id>/summary', methods=['GET'])
def get_summary(portfolio_id):
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    holdings = Holding.query.filter_by(portfolio_id=portfolio_id).all()

    if holdings:
        enriched = [CryptoMarketDataService().enrich_holding(h.to_dict()) for h in holdings]
        summary = PortfolioCalculator(enriched, portfolio.base_currency).calculate_portfolio_summary()
    else:
        summary = _empty_summary(portfolio)

    performance_record = Performance.query.filter_by(portfolio_id=portfolio_id).order_by(Performance.created_at.desc()).first()
    if performance_record:
        record = performance_record.to_dict()
        summary['total_value'] = record.get('total_value', summary.get('total_value', 0))
        summary['performance'] = {
            **summary.get('performance', {}),
            'total_unrealized': record.get('unrealized_total', 0),
            'total_realized': record.get('realized_total', 0),
            'total_pnl': record.get('unrealized_total', 0) + record.get('realized_total', 0),
            'ytd_return_pct': record.get('ytd_performance', 0),
            'cost_basis': record.get('total_value', 0),
        }

    return jsonify({'portfolio': portfolio.to_dict(), 'summary': summary})


@bp.route('/<int:portfolio_id>/holdings', methods=['GET'])
def get_holdings(portfolio_id):
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    holdings = Holding.query.filter_by(portfolio_id=portfolio_id).all()
    return jsonify({'portfolio': portfolio.to_dict(), 'holdings': [holding.to_dict() for holding in holdings]})


@bp.route('/<int:portfolio_id>/analytics', methods=['GET'])
def get_analytics(portfolio_id):
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    holdings = Holding.query.filter_by(portfolio_id=portfolio_id).all()
    if holdings:
        enriched = [CryptoMarketDataService().enrich_holding(h.to_dict()) for h in holdings]
        summary = PortfolioCalculator(enriched, portfolio.base_currency).calculate_portfolio_summary()
    else:
        summary = _empty_summary(portfolio)

    analytics = {
        'portfolio_id': portfolio_id,
        'total_value': summary.get('total_value', 0),
        'long_value': summary.get('long_value', 0),
        'short_value': summary.get('short_value', 0),
        'std_dev': summary.get('volatility', {}).get('std_dev', 0),
        'volatility': summary.get('volatility', {}).get('volatility', 0),
        'beta': 0.0,
        'sharpe_ratio': 0.0,
        'performance': summary.get('performance', {}),
        'exposure_data': {
            'category': summary.get('category_exposure', {}),
            'market_cap': summary.get('market_cap_exposure', {}),
        },
    }
    return jsonify({'portfolio': portfolio.to_dict(), 'analytics': analytics})


@bp.route('/<int:portfolio_id>/research', methods=['GET'])
def get_research(portfolio_id):
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    holdings = Holding.query.filter_by(portfolio_id=portfolio_id).all()
    research = generate_portfolio_research([CryptoMarketDataService().enrich_holding(h.to_dict()) for h in holdings])
    return jsonify({'portfolio': portfolio.to_dict(), 'research': research})


@bp.route('/<int:portfolio_id>/add-position', methods=['POST'])
def add_position(portfolio_id):
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    payload = request.get_json(silent=True) or {}
    symbol = str(payload.get('symbol') or '').strip().upper()
    if not symbol:
        return jsonify({'error': 'symbol is required'}), 400

    quantity = float(payload.get('quantity') or 0)
    average_cost = float(payload.get('average_cost') or 0)
    current_price = float(payload.get('current_price') or 0)
    category = str(payload.get('category') or 'Unknown')
    market_cap_tier = str(payload.get('market_cap_tier') or 'Unknown')
    name = str(payload.get('name') or symbol)
    notes = str(payload.get('notes') or '')

    if quantity <= 0:
        return jsonify({'error': 'quantity must be greater than zero'}), 400

    existing = Holding.query.filter_by(portfolio_id=portfolio_id, symbol=symbol).first()
    if existing:
        existing.quantity = quantity
        existing.average_cost = average_cost
        existing.current_price = current_price
        existing.current_value = quantity * current_price
        existing.cost_basis = quantity * average_cost
        existing.unrealized_pnl = existing.current_value - existing.cost_basis
        existing.category = category
        existing.market_cap_tier = market_cap_tier
        existing.name = name
        existing.notes = notes
        db.session.commit()
        return jsonify({'portfolio': portfolio.to_dict(), 'holding': existing.to_dict()})

    holding = Holding(
        portfolio_id=portfolio.id,
        symbol=symbol,
        name=name,
        category=category,
        market_cap_tier=market_cap_tier,
        quantity=quantity,
        average_cost=average_cost,
        current_price=current_price,
        current_value=quantity * current_price,
        cost_basis=quantity * average_cost,
        unrealized_pnl=(quantity * current_price) - (quantity * average_cost),
        realized_pnl=0,
        notes=notes,
    )
    db.session.add(holding)
    db.session.commit()
    return jsonify({'portfolio': portfolio.to_dict(), 'holding': holding.to_dict()})
