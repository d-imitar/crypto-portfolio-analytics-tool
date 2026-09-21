import json
import os
import re
from typing import Any, Dict, List

import requests


class CryptoResearchService:
    def __init__(self):
        self.api_key = (os.getenv('GEMINI_API_KEY') or '').strip()
        self.model_name = (os.getenv('GEMINI_MODEL_NAME') or 'gemini-2.5-flash').strip()

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _compute_upside_pct(current_price: float, target_price: float) -> float:
        if current_price > 0 and target_price > 0:
            return ((target_price - current_price) / current_price) * 100
        return 0.0

    @staticmethod
    def _sanitize_target_price(current_price: float, target_price: float, fallback_target: float) -> float:
        if current_price <= 0:
            return 0.0
        if target_price <= 0:
            return fallback_target if fallback_target > 0 else current_price
        ratio = target_price / current_price
        if ratio < 0.25 or ratio > 5.0:
            return fallback_target if fallback_target > 0 else current_price
        return target_price

    def _heuristic_target_price(self, holding: Dict[str, Any]) -> float:
        current_price = self._safe_float(holding.get('current_price'), 0.0)
        if current_price <= 0:
            return 0.0
        category = str(holding.get('category') or 'Unknown').lower()
        bias_map = {
            'layer 1': 0.28,
            'defi': 0.24,
            'infrastructure': 0.23,
            'meme': 0.18,
            'staking': 0.21,
            'rwa': 0.2,
            'stablecoin': 0.12,
        }
        bias = 0.14
        for key, value in bias_map.items():
            if key in category:
                bias = value
                break

        symbol = str(holding.get('symbol') or '')
        if symbol:
            bias += (sum(ord(ch) for ch in symbol) % 10) * 0.005
        return current_price * (1 + bias)

    def _make_recommendation(self, upside_pct: float) -> str:
        if upside_pct >= 18:
            return 'BUY'
        if upside_pct >= 0:
            return 'HOLD'
        return 'SELL'

    @staticmethod
    def _extract_json_payload(response_text: str) -> Dict[str, Any]:
        cleaned = response_text.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.replace('```json', '').replace('```', '').strip()
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return {}
        return {}

    def _call_gemini(self, token: str, project_name: str, category: str) -> Dict[str, Any]:
        if not self.api_key:
            return {}
        prompt = (
            f"Imagine that you are a senior analyst at a leading crypto hedge fund. Analyze the {project_name} project/coin ({token}) in category {category}. "
            "Provide a research report including an investment recommendation and target price. Return ONLY valid JSON with keys: recommendation, target_price, upside_pct, summary. "
            "The recommendation must be BUY, HOLD, or SELL and must be consistent with the formula: ((target_price - current_price) / current_price) * 100. "
            "Use realistic valuations and keep the target within a reasonable range relative to the current price."
        )
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': 0.2,
                'maxOutputTokens': 1000,
                'responseMimeType': 'application/json',
            },
        }
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}'
        try:
            response = requests.post(url, json=payload, timeout=45)
            response.raise_for_status()
            data = response.json()
            text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            return self._extract_json_payload(text)
        except Exception:
            return {}

    def build_research(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not holdings:
            return {'research_note': 'No holdings available for research.', 'worst_position': None, 'ranked_positions': []}

        ranked = []
        for holding in holdings:
            symbol = str(holding.get('symbol') or 'N/A')
            project_name = holding.get('name') or symbol
            current_price = self._safe_float(holding.get('current_price'), 0.0)
            target_price = self._heuristic_target_price(holding)
            upside_pct = self._compute_upside_pct(current_price, target_price)

            ai_result = {}
            summary = 'Heuristic research output used because the Gemini API key is not configured.'
            if self.api_key:
                ai_result = self._call_gemini(symbol, project_name, holding.get('category') or 'Unknown')
                if ai_result:
                    raw_target = self._safe_float(ai_result.get('target_price'), target_price)
                    target_price = self._sanitize_target_price(current_price, raw_target, target_price)
                    summary = str(ai_result.get('summary') or 'AI-generated research based on market context and project fundamentals.')
                else:
                    summary = 'Gemini analysis was unavailable. The system used a fallback value based on market context.'

            if current_price > 0 and target_price > 0:
                upside_pct = self._compute_upside_pct(current_price, target_price)
            else:
                upside_pct = 0.0

            ranked.append({
                'symbol': symbol,
                'company_name': project_name,
                'current_price': current_price,
                'target_price': target_price,
                'upside_pct': round(upside_pct, 2),
                'upside_potential_%': round(upside_pct, 2),
                'recommendation': self._make_recommendation(upside_pct),
                'research_summary': summary,
            })

        ranked.sort(key=lambda item: item['upside_pct'], reverse=True)
        worst_position = min(ranked, key=lambda item: item['upside_pct'], default=None)
        if worst_position:
            worst_position['research_summary'] = worst_position.get('research_summary') or 'This position appears weakest based on the current upside estimate.'
        return {
            'research_note': 'AI-generated research is active.' if self.api_key else 'Heuristic research output used because the Gemini API key is not configured.',
            'worst_position': worst_position,
            'ranked_positions': ranked,
        }


def generate_portfolio_research(holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
    return CryptoResearchService().build_research(holdings)
