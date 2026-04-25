import axios from 'axios';

// In production, set VITE_API_URL to your backend (e.g. https://playto-api.onrender.com/api/v1)
// In local dev, the Vite proxy forwards /api to localhost:8000
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getMerchants = () => client.get('/merchants/');
export const getMerchant = (id) => client.get(`/merchants/${id}/`);
export const getLedger = (id) => client.get(`/merchants/${id}/ledger/`);
export const getPayouts = (id) => client.get(`/merchants/${id}/payouts/`);
export const createPayout = (idempotencyKey, data) => 
  client.post('/payouts/', data, {
    headers: {
      'Idempotency-Key': idempotencyKey,
    },
  });

export default client;
