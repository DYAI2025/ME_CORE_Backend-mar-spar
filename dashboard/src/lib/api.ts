// Minimal API client for dashboard
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = {
  getStatus: async () => {
    const response = await fetch(`${API_BASE_URL}/status`);
    return response.json();
  },
  getMarkers: async () => {
    const response = await fetch(`${API_BASE_URL}/markers`);
    return response.json();
  },
};

// Additional API functions
export const fetchMarkers = () => api.getMarkers();
export const fetchDetectRegistry = async () => ({ data: [] });
export const fetchSchemas = async (): Promise<any[]> => ([]);
export const fetchDashboardData = async () => ({ 
  status: 'ok', 
  health: { status: 'ok' }, 
  markers: { count: 0 }, 
  jenkins: { status: 'unknown' } 
});
export const fetchJenkinsStatus = async () => ({ status: 'unknown' });
export const triggerDeployment = async () => ({ success: true });
export const triggerE2ETests = async () => ({ success: true });
export const validateRegistry = async () => ({ valid: true });
export const updateDetectRegistry = async () => ({ success: true });