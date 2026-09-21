import os
from typing import Dict, List, Optional

import requests


DEFAULT_PRICES = {
    'BTC': 62000,
    'ETH': 3200,
    'SOL': 155,
    'BNB': 570,
    'XRP': 0.63,
    'ADA': 0.72,
    'DOGE': 0.17,
    'AVAX': 34,
    'LINK': 17,
    'MATIC': 0.82,
    'DOT': 7.2,
    'ATOM': 8.8,
    'OP': 2.1,
    'ARB': 1.1,
    'UNI': 8.3,
}


def normalize_symbol(symbol: Optional[str]) -> str:
    if not symbol:
        return ''
    value = str(symbol).strip().upper().replace(' ', '')
    return value.replace(':', '')


class CryptoMarketDataService:
    def __init__(self):
        self.base_currency = (os.getenv('BASE_CURRENCY') or 'USD').upper()

    def _fetch_coingecko(self, ids: List[str]) -> Dict[str, Dict]:
        if not ids:
            return {}
        try:
            url = 'https://api.coingecko.com/api/v3/coins/markets'
            params = {
                'vs_currency': self.base_currency.lower(),
                'ids': ','.join(ids),
                'price_change_percentage': '1h,24h,7d,30d,1y',
                'sparkline': 'false',
                'per_page': 250,
                'page': 1,
            }
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            items = response.json()
            return {str(item.get('symbol', '')).upper(): item for item in items if item}
        except Exception:
            return {}

    def get_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        normalized = [normalize_symbol(symbol) for symbol in symbols if normalize_symbol(symbol)]
        if not normalized:
            return {}
        ids = [self._symbol_to_id(symbol) for symbol in normalized]
        live = self._fetch_coingecko([item for item in ids if item])
        out = {}
        for symbol in normalized:
            id_key = self._symbol_to_id(symbol)
            data = live.get(symbol)
            if not data:
                data = {
                    'symbol': symbol,
                    'current_price': DEFAULT_PRICES.get(symbol, 1.0),
                    'market_cap': 0,
                    'total_volume': 0,
                    'category': 'Unknown',
                    'market_cap_rank': 0,
                    'price_change_percentage_24h': 0,
                    'price_change_percentage_7d': 0,
                    'price_change_percentage_30d': 0,
                    'price_change_percentage_1y': 0,
                }
            out[symbol] = data
        return out

    @staticmethod
    def _symbol_to_id(symbol: str) -> str:
        mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'AVAX': 'avalanche-2',
            'LINK': 'chainlink',
            'MATIC': 'matic-network',
            'DOT': 'polkadot',
            'ATOM': 'cosmos',
            'OP': 'optimism',
            'ARB': 'arbitrum',
            'UNI': 'uniswap',
        }
        return mapping.get(symbol, symbol.lower())

    def enrich_holding(self, holding: Dict) -> Dict:
        symbol = normalize_symbol(holding.get('symbol'))
        if not symbol:
            return holding
        market = self.get_market_data([symbol]).get(symbol, {})
        current_price = float(holding.get('current_price') or market.get('current_price') or DEFAULT_PRICES.get(symbol, 0.0) or 0.0)
        quantity = float(holding.get('quantity') or 0.0)
        current_value = quantity * current_price
        average_cost = float(holding.get('average_cost') or 0.0)
        cost_basis = quantity * average_cost if quantity else 0.0
        holding['current_price'] = current_price
        holding['current_value'] = current_value
        holding['cost_basis'] = cost_basis
        holding['unrealized_pnl'] = current_value - cost_basis
        holding['category'] = holding.get('category') or str(market.get('category') or 'Unknown')
        holding['market_cap_tier'] = holding.get('market_cap_tier') or (
            'Large Cap' if float(market.get('market_cap') or 0) > 100_000_000 else 'Mid Cap'
        )
        holding['perf_1d'] = float(market.get('price_change_percentage_24h') or 0) if market else 0.0
        holding['perf_7d'] = float(market.get('price_change_percentage_7d') or 0) if market else 0.0
        holding['perf_30d'] = float(market.get('price_change_percentage_30d') or 0) if market else 0.0
        holding['perf_1y'] = float(market.get('price_change_percentage_1y') or 0) if market else 0.0
        holding['market_cap'] = float(market.get('market_cap') or 0) if market else 0.0
        holding['circulating_supply'] = float(market.get('circulating_supply') or 0) if market else 0.0
        return holding


def enrich_holdings(holdings: Iterable[Dict]) -> List[Dict]:
    service = CryptoMarketDataService()
    return [service.enrich_holding(h) for h in holdings]
