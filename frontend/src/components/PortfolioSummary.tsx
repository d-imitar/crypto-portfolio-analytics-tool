import React, { useEffect, useState } from 'react';
import { getPortfolioHoldings, getPortfolioResearch, getPortfolioSummary } from '../services/api';
import './PortfolioSummary.css';

interface Portfolio {
  id: number;
  name: string;
}

const PortfolioSummary: React.FC<{ portfolio: Portfolio }> = ({ portfolio }) => {
  const [summary, setSummary] = useState<any>(null);
  const [holdings, setHoldings] = useState<any[]>([]);
  const [research, setResearch] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const load = async () => {
      try {
        const [summaryRes, holdingsRes, researchRes] = await Promise.all([
          getPortfolioSummary(portfolio.id),
          getPortfolioHoldings(portfolio.id),
          getPortfolioResearch(portfolio.id),
        ]);
        setSummary(summaryRes.data.summary);
        setHoldings(holdingsRes.data.holdings || []);
        setResearch(researchRes.data.research || null);
        setError('');
      } catch (error) {
        console.error('Failed to load summary', error);
        setError('Unable to load summary data.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [portfolio.id]);

  if (loading) return <div className="panel">Loading summary...</div>;
  if (error) return <div className="panel">{error}</div>;
  if (!summary) return <div className="panel">No summary available</div>;

  const totalPnl = Number(summary.performance?.total_pnl || 0);
  const costBasis = Number(summary.performance?.cost_basis || 0);
  const pnlPct = costBasis > 0 ? (totalPnl / costBasis) * 100 : 0;
  const topHoldings = [...holdings].sort((a, b) => Number(b.current_value || 0) - Number(a.current_value || 0));

  return (
    <div className="panel summary-panel">
      <h2>{portfolio.name}</h2>
      <div className="summary-grid">
        <div className="card"><label>Total Value</label><strong>{Number(summary.total_value || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })}</strong></div>
        <div className="card"><label>Holdings</label><strong>{holdings.length}</strong></div>
        <div className="card"><label>Total P&L</label><strong className={totalPnl >= 0 ? 'positive' : 'negative'}>{Number(totalPnl).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })}</strong></div>
        <div className="card"><label>YTD Return</label><strong className={Number(summary.performance?.ytd_return_pct || 0) >= 0 ? 'positive' : 'negative'}>{Number(summary.performance?.ytd_return_pct || 0).toFixed(2)}%</strong></div>
      </div>

      {research?.worst_position && (
        <div className="research-card">
          <h3>Worst position</h3>
          <p><strong>{research.worst_position.symbol}</strong> — {research.worst_position.recommendation}</p>
          <p>{research.research_note}</p>
          <p>{research.worst_position.research_summary}</p>
        </div>
      )}

      <div className="holdings-table-wrap">
        <h3>Holdings</h3>
        <table>
          <thead>
            <tr><th>Symbol</th><th>Qty</th><th>Price</th><th>Value</th><th>P&L</th></tr>
          </thead>
          <tbody>
            {topHoldings.map((holding) => (
              <tr key={holding.id}>
                <td>{holding.symbol}</td>
                <td>{Number(holding.quantity || 0).toFixed(4)}</td>
                <td>{Number(holding.current_price || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })}</td>
                <td>{Number(holding.current_value || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })}</td>
                <td className={Number(holding.unrealized_pnl || 0) >= 0 ? 'positive' : 'negative'}>{Number(holding.unrealized_pnl || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="performance-note">Portfolio return: {pnlPct.toFixed(2)}%</p>
    </div>
  );
};

export default PortfolioSummary;
