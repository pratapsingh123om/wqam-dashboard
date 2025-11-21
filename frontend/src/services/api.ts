import axios from 'axios';
import type { UploadReport, DashboardData } from '../types/dashboard';

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
});

// Function to set the auth token
export const setAuthToken = (token: string | null) => {
  if (token) {
    axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete axiosInstance.defaults.headers.common['Authorization'];
  }
};

export async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const method = options?.method || 'GET';
  
  // Start with default headers
  let headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Merge provided headers, converting Headers object to plain object if necessary
  if (options?.headers) {
    if (options.headers instanceof Headers) {
      headers = { ...headers, ...Object.fromEntries(options.headers.entries()) };
    } else {
      headers = { ...headers, ...options.headers as Record<string, string> };
    }
  }

  let data: any;
  if (options?.body) {
    // If body is FormData, don't set Content-Type header manually, let Axios handle it
    if (options.body instanceof FormData) {
      delete headers['Content-Type'];
      data = options.body;
    } else if (typeof options.body === 'string') {
      try {
        data = JSON.parse(options.body);
      } catch (e) {
        data = options.body; // Not JSON, send as is
      }
    } else {
      data = options.body;
    }
  }

  try {
    const response = await axiosInstance({
      url,
      method,
      headers,
      data,
    });
    return response.data as T;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'API error');
    }
    throw error;
  }
}


export async function fetchDemo(): Promise<DashboardData> {
  return apiFetch<DashboardData>('/demo');
}

export async function fetchReports(): Promise<UploadReport[]> {
  return apiFetch<UploadReport[]>('/reports');
}

export async function downloadLatestReportPdf(): Promise<Blob> {
  const response = await axiosInstance.get('/reports/latest/pdf', { responseType: 'blob' });
  return response.data;
}

export async function uploadWaterData(formData: FormData): Promise<UploadReport> {
  const response = await axiosInstance.post('/uploads/analyze', formData);
  return response.data;
}

// Re-export axiosInstance just in case other files still need it directly,
// but the intention is to use apiFetch for most API interactions.
export { axiosInstance as api };