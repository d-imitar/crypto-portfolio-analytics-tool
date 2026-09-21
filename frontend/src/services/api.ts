import axios from 'axios';

const API_BASE_URL = (process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api').replace(/\/$/, '');
const apiClient = axios.create({ baseURL: API_BASE_URL });

const joinApiPath = (path: string) => path.replace(/^\//, '');

export const getPortfolios = () => apiClient.get(joinApiPath('/portfolio/list'));
export const getPortfolioSummary = (portfolioId: number) => apiClient.get(joinApiPath(`/portfolio/${portfolioId}/summary`));
export const getPortfolioHoldings = (portfolioId: number) => apiClient.get(joinApiPath(`/portfolio/${portfolioId}/holdings`));
export const getPortfolioAnalytics = (portfolioId: number) => apiClient.get(joinApiPath(`/portfolio/${portfolioId}/analytics`));
export const getPortfolioResearch = (portfolioId: number) => apiClient.get(joinApiPath(`/portfolio/${portfolioId}/research`));

export const addCryptoPosition = (portfolioId: number, payload: Record<string, any>) =>
  apiClient.post(joinApiPath(`/portfolio/${portfolioId}/add-position`), payload);

export const uploadPortfolioCsv = (file: File, portfolioId?: number) => {
  const formData = new FormData();
  formData.append('file', file);
  if (portfolioId) formData.append('portfolio_id', String(portfolioId));
  return apiClient.post(joinApiPath('/upload/portfolio-csv'), formData, { headers: { 'Content-Type': 'multipart/form-data' } });
};
