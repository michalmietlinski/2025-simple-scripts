# Printables Integration Research

## Current Status (as of March 2024)

According to recent forum discussions:

- No public API is currently available
- Prusa has considered it but hasn't published one
- Bot interactions are likely to be blocked
- Concerns about automated uploads and spam exist

## Implementation Strategy

Given these constraints, we'll focus on a user-friendly scraping approach using Playwright (as suggested in the forum):

```typescript
class PrintablesScraper {
  private browser: Browser; // Playwright browser
  private context: BrowserContext;

  constructor() {
    // Use headed mode for manual intervention if needed
    this.browser = await playwright.chromium.launch({
      headless: false,
    });
    this.context = await this.browser.newContext();
  }

  // Respect rate limits and act like a human
  private async humanLikeDelay(): Promise<void> {
    const delay = 1000 + Math.random() * 2000; // 1-3 seconds
    await new Promise((resolve) => setTimeout(resolve, delay));
  }

  async extractModelData(url: string): Promise<ModelData> {
    const page = await this.context.newPage();
    await page.goto(url);
    await this.humanLikeDelay();

    // Extract data carefully to avoid detection
    const data = await page.evaluate(() => {
      return {
        title: document.querySelector('.model-info h1')?.textContent,
        description: document.querySelector('.model-description')?.textContent,
        files: Array.from(
          document.querySelectorAll('.model-files-list .file-item'),
        ).map((item) => ({
          name: item.querySelector('.file-name')?.textContent,
          size: item.querySelector('.file-size')?.textContent,
        })),
      };
    });

    await page.close();
    return data;
  }
}
```

## Anti-Detection Measures

```typescript
interface ScrapingConfig {
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

const defaultConfig: ScrapingConfig = {
  delays: {
    pageLoad: [2000, 5000],
    interaction: [500, 1500],
    download: [3000, 6000],
  },
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  viewport: {
    width: 1920,
    height: 1080,
    deviceScaleFactor: 1,
  },
  maxParallel: 1, // Sequential operations only
};
```

## Ethical Usage Guidelines

1. Rate Limiting:

```typescript
class RateLimiter {
  private lastRequest: number = 0;
  private readonly minDelay = 5000; // 5 seconds minimum between requests

  async waitForNextRequest(): Promise<void> {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequest;

    if (timeSinceLastRequest < this.minDelay) {
      await new Promise((resolve) =>
        setTimeout(resolve, this.minDelay - timeSinceLastRequest),
      );
    }

    this.lastRequest = Date.now();
  }
}
```

2. Download Management:

```typescript
class DownloadManager {
  private downloadCount = 0;
  private readonly maxDownloadsPerHour = 30;
  private readonly downloadHistory: number[] = [];

  async canDownload(): Promise<boolean> {
    const oneHourAgo = Date.now() - 3600000;
    this.downloadHistory = this.downloadHistory.filter(
      (time) => time > oneHourAgo,
    );

    return this.downloadHistory.length < this.maxDownloadsPerHour;
  }

  async trackDownload(): Promise<void> {
    this.downloadHistory.push(Date.now());
  }
}
```

## Error Recovery

```typescript
interface RetryStrategy {
  maxAttempts: number;
  delays: number[]; // Delays between retries
  shouldRetry: (error: any) => boolean;
}

const defaultRetryStrategy: RetryStrategy = {
  maxAttempts: 3,
  delays: [5000, 15000, 30000],
  shouldRetry: (error: any) => {
    // Retry on network errors or 5xx responses
    return (
      error.name === 'NetworkError' || (error.status && error.status >= 500)
    );
  },
};
```

## Future Considerations

1. Monitor for API availability
2. Implement user authentication for higher limits
3. Consider building browser extension instead
4. Focus on user-initiated actions rather than automation
5. Implement proper error handling and logging

[Source: Prusa Forum Discussion on Printables API](https://forum.prusa3d.com/forum/english-forum-general-discussion-announcements-and-releases/printables-application-programmable-interface-api/)
