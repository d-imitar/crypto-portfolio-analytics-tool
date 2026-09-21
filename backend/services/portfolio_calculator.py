from collections import defaultdict
from typing import Dict, List

import numpy as np


class PortfolioCalculator:
    @staticmethod
    def _normalize_exposure_map(exposure: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        cleaned = {str(label): float(value) for label, value in exposure.items() if value is not None}
        if not cleaned:
            return {'breakdown': {}, 'total': 0.0, 'percentages': {}}
        total = sum(cleaned.values())
        sorted_exposure = dict(sorted(cleaned.items(), key=lambda item: item[1], reverse=True))
        if total <= 0:
            return {'breakdown': sorted_exposure, 'total': 0.0, 'percentages': {label: 0.0 for label in sorted_exposure}}
        return {
            'breakdown': sorted_exposure,
            'total': total,
            'percentages': {label: (value / total) * 100.0 for label, value in sorted_exposure.items()},
        }

    def __init__(self, holdings: List[Dict], base_currency: str = 'USD'):
        self.holdings = holdings
        self.base_currency = base_currency
        self.total_value = sum(float(h.get('current_value', 0) or 0) for h in holdings)
        self.absolute_exposure = sum(abs(float(h.get('current_value', 0) or 0)) for h in holdings)

    def calculate_position_weights(self):
        weights = []
        exposure_total = self.absolute_exposure if self.absolute_exposure > 0 else max(self.total_value, 0)
        for holding in self.holdings:
            value = float(holding.get('current_value', 0) or 0)
            weight = (abs(value) / exposure_total * 100) if exposure_total > 0 else 0
            weights.append({'symbol': holding.get('symbol', 'N/A'), 'weight': weight, 'value': value})
        return sorted(weights, key=lambda item: abs(item['value']), reverse=True)

    def calculate_category_exposure(self) -> Dict[str, float]:
        exposure = defaultdict(float)
        for holding in self.holdings:
            category = str(holding.get('category') or 'Cryptocurrency').strip() or 'Cryptocurrency'
            if category.lower() == 'unknown':
                category = 'Cryptocurrency'
            exposure[category] += abs(float(holding.get('current_value', 0) or 0))
        return self._normalize_exposure_map(exposure)

    def calculate_market_cap_exposure(self) -> Dict[str, float]:
        exposure = defaultdict(float)
        for holding in self.holdings:
            tier = str(holding.get('market_cap_tier') or 'Unspecified').strip() or 'Unspecified'
            if tier.lower() == 'unknown':
                tier = 'Unspecified'
            if tier == 'Unspecified' and float(holding.get('market_cap') or 0) > 0:
                tier = 'Large Cap' if float(holding.get('market_cap') or 0) >= 100_000_000 else 'Mid Cap' if float(holding.get('market_cap') or 0) >= 10_000_000 else 'Small Cap'
            exposure[tier] += abs(float(holding.get('current_value', 0) or 0))
        return self._normalize_exposure_map(exposure)

    def calculate_ytd_performance(self):
        total_unrealized = sum(float(h.get('unrealized_pnl', 0) or 0) for h in self.holdings)
        total_realized = sum(float(h.get('realized_pnl', 0) or 0) for h in self.holdings)
        total_pnl = total_unrealized + total_realized
        cost_basis = sum(float(h.get('cost_basis', 0) or 0) for h in self.holdings)
        ytd_return = (total_pnl / cost_basis * 100) if cost_basis > 0 else 0.0
        return {
            'total_unrealized': total_unrealized,
            'total_realized': total_realized,
            'total_pnl': total_pnl,
            'ytd_return_pct': ytd_return,
            'cost_basis': cost_basis,
        }

    def calculate_volatility(self):
        if not self.holdings:
            return {'std_dev': 0.0, 'volatility': 0.0}
        pnl_values = [float(h.get('unrealized_pnl', 0) or 0) for h in self.holdings if h.get('unrealized_pnl') is not None]
        if len(pnl_values) < 2:
            return {'std_dev': 0.0, 'volatility': 0.0}
        std_dev = float(np.std(pnl_values))
        return {'std_dev': std_dev, 'volatility': (std_dev / self.total_value * 100) if self.total_value > 0 else 0.0}

    def calculate_portfolio_summary(self):
        weights = self.calculate_position_weights()
        category_exp = self.calculate_category_exposure()
        market_cap_exp = self.calculate_market_cap_exposure()
        volatility = self.calculate_volatility()
        performance = self.calculate_ytd_performance()
        long_value = sum(float(h.get('current_value', 0) or 0) for h in self.holdings if float(h.get('current_value', 0) or 0) > 0)
        short_value = sum(float(h.get('current_value', 0) or 0) for h in self.holdings if float(h.get('current_value', 0) or 0) < 0)
        return {
            'total_value': self.total_value,
            'long_value': long_value,
            'short_value': short_value,
            'num_holdings': len(self.holdings),
            'position_weights': weights[:10],
            'category_exposure': category_exp,
            'market_cap_exposure': market_cap_exp,
            'volatility': volatility,
            'performance': performance,
            'base_currency': self.base_currency,
        }
