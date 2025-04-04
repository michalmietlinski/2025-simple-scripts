export interface PhotoSizes {
  maxWidth: number;
  maxHeight: number;
}

export interface PrintablesApiConfig {
  baseUrl: string;
  timeout: number;
}

export interface ScrapingConfig {
  delays: {
    pageLoad: [number, number]; // Min-max delay after page load
    interaction: [number, number]; // Min-max delay between interactions
    download: [number, number]; // Min-max delay between downloads
  };
  userAgent: string; // Realistic browser UA
  viewport: {
    width: number;
    height: number;
    deviceScaleFactor: number;
  };
  maxParallel: number; // Max parallel operations
}

export interface RetryStrategy {
  maxAttempts: number;
  delays: number[]; // Delays between retries
  shouldRetry: (error: any) => boolean;
}

export interface Settings {
  dataPath: string;
  photoSizes: PhotoSizes;
  supportedFileTypes: string[];
  printablesApi: PrintablesApiConfig; // Kept for backward compatibility
  scraping: ScrapingConfig;
  retry: RetryStrategy;
} 
