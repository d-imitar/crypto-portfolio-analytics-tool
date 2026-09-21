from datetime import datetime
from database import db


class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, default='Default portfolio')
    base_currency = db.Column(db.String(10), default='USD')
    description = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    holdings = db.relationship('Holding', backref='portfolio', lazy=True, cascade='all, delete-orphan')
    performance = db.relationship('Performance', backref='portfolio', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'base_currency': self.base_currency,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Holding(db.Model):
    __tablename__ = 'holding'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)

    symbol = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), default='')
    category = db.Column(db.String(100), default='Unknown')
    market_cap_tier = db.Column(db.String(50), default='Unknown')
    quantity = db.Column(db.Float, default=0.0)
    average_cost = db.Column(db.Float, default=0.0)
    current_price = db.Column(db.Float, default=0.0)
    current_value = db.Column(db.Float, default=0.0)
    cost_basis = db.Column(db.Float, default=0.0)
    unrealized_pnl = db.Column(db.Float, default=0.0)
    realized_pnl = db.Column(db.Float, default=0.0)
    perf_1d = db.Column(db.Float, default=0.0)
    perf_7d = db.Column(db.Float, default=0.0)
    perf_30d = db.Column(db.Float, default=0.0)
    perf_1y = db.Column(db.Float, default=0.0)
    market_cap = db.Column(db.Float, default=0.0)
    circulating_supply = db.Column(db.Float, default=0.0)
    notes = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'symbol': self.symbol,
            'name': self.name,
            'category': self.category,
            'market_cap_tier': self.market_cap_tier,
            'quantity': self.quantity,
            'average_cost': self.average_cost,
            'current_price': self.current_price,
            'current_value': self.current_value,
            'cost_basis': self.cost_basis,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'perf_1d': self.perf_1d,
            'perf_7d': self.perf_7d,
            'perf_30d': self.perf_30d,
            'perf_1y': self.perf_1y,
            'market_cap': self.market_cap,
            'circulating_supply': self.circulating_supply,
            'notes': self.notes,
        }


class Performance(db.Model):
    __tablename__ = 'performance'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
    total_value = db.Column(db.Float, default=0.0)
    long_value = db.Column(db.Float, default=0.0)
    short_value = db.Column(db.Float, default=0.0)
    unrealized_total = db.Column(db.Float, default=0.0)
    realized_total = db.Column(db.Float, default=0.0)
    ytd_performance = db.Column(db.Float, default=0.0)
    beta = db.Column(db.Float, default=0.0)
    std_dev = db.Column(db.Float, default=0.0)
    sharpe_ratio = db.Column(db.Float, default=0.0)
    exposure_data = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'total_value': self.total_value,
            'long_value': self.long_value,
            'short_value': self.short_value,
            'unrealized_total': self.unrealized_total,
            'realized_total': self.realized_total,
            'ytd_performance': self.ytd_performance,
            'beta': self.beta,
            'std_dev': self.std_dev,
            'sharpe_ratio': self.sharpe_ratio,
            'exposure_data': self.exposure_data,
        }
