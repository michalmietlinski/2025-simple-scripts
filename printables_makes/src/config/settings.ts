import { Settings } from '../types/Settings';
import path from 'path';

export const CONFIG: Settings = {
  dataPath: path.join(process.cwd(), 'data'),
  photoSizes: {
    maxWidth: 2048,
    maxHeight: 2048,
  },
  supportedFileTypes: ['.stl', '.3mf', '.obj'],
  printablesApi: {
    baseUrl: 'https://printables.com',
    timeout: 60000,
  },
  scraping: {
    delays: {
      pageLoad: [3000, 7000],
      interaction: [1000, 2500],
      download: [5000, 10000],
    },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    viewport: {
      width: 1920,
      height: 1080,
      deviceScaleFactor: 1,
    },
    maxParallel: 1,
  },
  retry: {
    maxAttempts: 3,
    delays: [10000, 30000, 60000],
    shouldRetry: (error: any) => {
      return (
        error.name === 'NetworkError' || 
        (error.status && error.status >= 500) ||
        error.message?.includes('timeout') ||
        error.message?.includes('rate limit')
      );
    },
  },
}; 
