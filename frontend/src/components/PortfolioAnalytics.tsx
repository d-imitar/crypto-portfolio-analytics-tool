import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { getPortfolioAnalytics, getPortfolioResearch } from '../services/api';
import './PortfolioAnalytics.css';

interface Portfolio {
  id: number;
  name: string;
}

const PortfolioAnalytics: React.FC<{ portfolio: Portfolio }> = ({ portfolio }) => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [research, setResearch] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const load = async () => {
      try {
        const [analyticsRes, researchRes] = await Promise.all([
          getPortfolioAnalytics(portfolio.id),
          getPortfolioResearch(portfolio.id),
        ]);
        setAnalytics(analyticsRes.data.analytics);
        setResearch(researchRes.data.research);
        setError('');
      } catch (error) {
        console.error('Failed to load analytics', error);
        setError('Unable to load analytics right now.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [portfolio.id]);

  if (loading) return <div className="panel">Loading analytics...</div>;
  if (error) return <div className="panel">{error}</div>;
  if (!analytics) return <div className="panel">No analytics available</div>;

  const categoryExposure = analytics.exposure_data?.category || {};
  const marketExposure = analytics.exposure_data?.market_cap || {};
  const categoryEntries = Object.entries(categoryExposure.breakdown || {}).sort(([, a], [, b]) => Number(b) - Number(a));
  const marketEntries = Object.entries(marketExposure.breakdown || {}).sort(([, a], [, b]) => Number(b) - Number(a));

  const hasBeta = analytics.beta !== null && analytics.beta !== undefined && analytics.beta !== '';
  const hasSharpe = analytics.sharpe_ratio !== null && analytics.sharpe_ratio !== undefined && analytics.sharpe_ratio !== '';

  return (
    <div className="panel analytics-panel">
      <h2>Portfolio Analytics</h2>
      <div className="metrics-grid">
        <div className="metric"><label>Portfolio Value</label><strong>{Number(analytics.total_value || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })}</strong></div>
        <div className="metric"><label>Long Value</label><strong>{Number(analytics.long_value || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })}</strong></div>
        <div className="metric"><label>Short Value</label><strong>{Number(analytics.short_value || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })}</strong></div>
        <div className="metric"><label>Volatility</label><strong>{Number(analytics.volatility || 0).toFixed(2)}</strong></div>
        {hasBeta && <div className="metric"><label>Beta</label><strong>{Number(analytics.beta || 0).toFixed(2)}</strong></div>}
        {hasSharpe && <div className="metric"><label>Sharpe</label><strong>{Number(analytics.sharpe_ratio || 0).toFixed(2)}</strong></div>}
      </div>

      <div className="charts-grid">
        {categoryEntries.length > 0 && (
          <div className="chart-card">
            <h3>Category Allocation</h3>
            <Plot
              data={[{ type: 'pie', labels: categoryEntries.map(([key]) => key), values: categoryEntries.map(([, value]) => Number(value)), textinfo: 'label+percent', marker: { line: { color: '#0f172a', width: 1 } } }]}
              layout={{ paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', font: { color: '#e2e8f0' }, margin: { t: 10, b: 10, l: 10, r: 10 } }}
              config={{ displayModeBar: false }}
              style={{ width: '100%', height: '320px' }}
              useResizeHandler
            />
          </div>
        )}

        {marketEntries.length > 0 && (
          <div className="chart-card">
            <h3>Market Cap Tier</h3>
            <Plot
              data={[{ type: 'bar', y: marketEntries.map(([key]) => key), x: marketEntries.map(([, value]) => Number(value)), orientation: 'h', marker: { color: '#38bdf8' } }]}
              layout={{ paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', font: { color: '#e2e8f0' }, margin: { t: 10, b: 10, l: 110, r: 10 }, xaxis: { title: { text: 'USD' } } }}
              config={{ displayModeBar: false }}
              style={{ width: '100%', height: '320px' }}
              useResizeHandler
            />
          </div>
        )}
      </div>

      {research?.ranked_positions?.length > 0 && (
        <div className="research-block">
          <h3>Research</h3>
          <table>
            <thead><tr><th>Coin</th><th>Target</th><th>Upside</th><th>Rating</th></tr></thead>
            <tbody>
              {research.ranked_positions.slice(0, 5).map((item: any, index: number) => (
                <tr key={`${item.symbol}-${index}`}>
                  <td>{item.symbol}</td>
                  <td>{Number(item.target_price || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })}</td>
                  <td>{Number(item.upside_pct || 0).toFixed(2)}%</td>
                  <td>{item.recommendation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PortfolioAnalytics;
