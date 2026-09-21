import React, { useEffect, useState } from 'react';
import './App.css';
import PortfolioSummary from './components/PortfolioSummary';
import PortfolioAnalytics from './components/PortfolioAnalytics';
import { addCryptoPosition, getPortfolios, uploadPortfolioCsv } from './services/api';

interface Portfolio {
  id: number;
  name: string;
  base_currency: string;
}

const initialForm = {
  symbol: 'BTC',
  name: 'Bitcoin',
  quantity: '1',
  average_cost: '55000',
  current_price: '62000',
  category: 'Layer 1',
  market_cap_tier: 'Large Cap',
  notes: 'Core position',
};

function App() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(initialForm);
  const [message, setMessage] = useState<string>('');

  const loadPortfolios = async () => {
    try {
      const response = await getPortfolios();
      const items = response.data.portfolios || [];
      setPortfolios(items);

      if (items.length === 0) {
        setSelectedPortfolio(null);
        return;
      }

      const stillExists = items.some((portfolio) => portfolio.id === selectedPortfolio?.id);
      if (!selectedPortfolio || !stillExists) {
        setSelectedPortfolio(items[0]);
      }
    } catch (error) {
      console.error('Failed to load portfolios', error);
      setMessage('Unable to load portfolios right now.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPortfolios();
  }, []);

  const handleFieldChange = (field: string, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleManualAdd = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedPortfolio) return;
    try {
      await addCryptoPosition(selectedPortfolio.id, {
        symbol: form.symbol,
        name: form.name,
        quantity: Number(form.quantity),
        average_cost: Number(form.average_cost),
        current_price: Number(form.current_price),
        category: form.category,
        market_cap_tier: form.market_cap_tier,
        notes: form.notes,
      });
      setMessage('Position added successfully');
      await loadPortfolios();
      setForm(initialForm);
    } catch (error: any) {
      setMessage(error.response?.data?.error || 'Unable to add position');
    }
  };

  const handleCsvUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      await uploadPortfolioCsv(file, selectedPortfolio?.id);
      setMessage('CSV imported successfully');
      await loadPortfolios();
    } catch (error: any) {
      setMessage(error.response?.data?.error || 'Upload failed');
    } finally {
      event.target.value = '';
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Crypto Portfolio Dashboard</p>
          <h1>Portfolio Analytics</h1>
        </div>
      </header>

      <main className="layout">
        <aside className="sidebar">
          <div className="panel">
            <h3>Add Crypto Position</h3>
            <form onSubmit={handleManualAdd} className="manual-form">
              <input value={form.symbol} onChange={(e) => handleFieldChange('symbol', e.target.value)} placeholder="BTC" />
              <input value={form.name} onChange={(e) => handleFieldChange('name', e.target.value)} placeholder="Bitcoin" />
              <input type="number" value={form.quantity} onChange={(e) => handleFieldChange('quantity', e.target.value)} placeholder="Quantity" step="any" />
              <input type="number" value={form.average_cost} onChange={(e) => handleFieldChange('average_cost', e.target.value)} placeholder="Avg cost" step="any" />
              <input type="number" value={form.current_price} onChange={(e) => handleFieldChange('current_price', e.target.value)} placeholder="Current price" step="any" />
              <input value={form.category} onChange={(e) => handleFieldChange('category', e.target.value)} placeholder="Category" />
              <input value={form.market_cap_tier} onChange={(e) => handleFieldChange('market_cap_tier', e.target.value)} placeholder="Market cap tier" />
              <textarea value={form.notes} onChange={(e) => handleFieldChange('notes', e.target.value)} placeholder="Notes" />
              <button type="submit">Add position</button>
            </form>
          </div>

          <div className="panel">
            <h3>Import Portfolio CSV</h3>
            <label className="file-upload">
              <input type="file" accept=".csv" onChange={handleCsvUpload} />
              <span>Select CSV file</span>
            </label>
          </div>

          <div className="panel portfolios-panel">
            <h3>Portfolios</h3>
            {portfolios.length === 0 ? <p>No portfolios yet</p> : portfolios.map((portfolio) => (
              <button key={portfolio.id} className={`portfolio-button ${selectedPortfolio?.id === portfolio.id ? 'active' : ''}`} onClick={() => setSelectedPortfolio(portfolio)}>
                {portfolio.name}
              </button>
            ))}
          </div>
        </aside>

        <section className="content">
          {message && <div className="flash-message">{message}</div>}
          {loading ? <div className="loading">Loading portfolio...</div> : selectedPortfolio ? (
            <>
              <PortfolioSummary portfolio={selectedPortfolio} />
              <PortfolioAnalytics portfolio={selectedPortfolio} />
            </>
          ) : (
            <div className="empty-state">No portfolio selected</div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
