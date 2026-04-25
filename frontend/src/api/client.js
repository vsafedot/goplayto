import axios from 'axios';

const client = axios.create({
  baseURL: '/api/v1',
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
