// Minimal API client for frontend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = {
  analyze: async (request: any) => {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return response.json();
  },
  getSchemas: async () => {
    const response = await fetch(`${API_BASE_URL}/schemas`);
    return response.json();
  },
};

export const analyzeText = async (request: any) => {
  return api.analyze(request);
};

export const analyzeChat = async (request: any) => {
  return api.analyze(request);
};