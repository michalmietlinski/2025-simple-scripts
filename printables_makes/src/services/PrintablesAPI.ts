import { chromium, Browser, BrowserContext } from 'playwright';
import fs from 'fs-extra';
import path from 'path';
import { CONFIG } from '../config/settings';
import { ProjectData } from '../types/Project';

export class PrintablesScraper {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private rateLimiter: RateLimiter;
  private downloadManager: DownloadManager;

  constructor() {
    this.rateLimiter = new RateLimiter();
    this.downloadManager = new DownloadManager();
  }

  private async initBrowser(): Promise<void> {
    if (!this.browser) {
      this.browser = await chromium.launch({
        headless: true, // Use headless mode for production
      });
      
      this.context = await this.browser.newContext({
        userAgent: CONFIG.scraping.userAgent,
        viewport: CONFIG.scraping.viewport,
      });
    }
  }

  private async closeBrowser(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      this.context = null;
    }
  }

  private async humanLikeDelay(type: 'pageLoad' | 'interaction' | 'download'): Promise<void> {
    const [min, max] = CONFIG.scraping.delays[type];
    const delay = min + Math.random() * (max - min);
    await new Promise((resolve) => setTimeout(resolve, delay));
  }

  async validateUrl(url: string): Promise<boolean> {
    try {
      // Check if URL is a valid Printables URL
      const printablesRegex = /^https?:\/\/(www\.)?printables\.com\/model\/\d+(-[\w-]+)?/;
      if (!printablesRegex.test(url)) {
        return false;
      }

      // Initialize browser if needed
      await this.initBrowser();
      if (!this.context) throw new Error('Browser context not initialized');

      // Wait for rate limiting
      await this.rateLimiter.waitForNextRequest();

      // Create a new page
      const page = await this.context.newPage();
      
      try {
        // Navigate to the URL
        await page.goto(url, { timeout: CONFIG.printablesApi.timeout });
        await this.humanLikeDelay('pageLoad');
        
        // Check if the page has a title (indicating it loaded successfully)
        const title = await page.title();
        return title.includes('Printables') && !title.includes('404');
      } finally {
        await page.close();
      }
    } catch (error) {
      console.error('Error validating URL:', error);
      return false;
    } finally {
      await this.closeBrowser();
    }
  }

  async getProjectData(url: string): Promise<ProjectData> {
    try {
      // Initialize browser if needed
      await this.initBrowser();
      if (!this.context) throw new Error('Browser context not initialized');

      // Wait for rate limiting
      await this.rateLimiter.waitForNextRequest();

      // Create a new page
      const page = await this.context.newPage();
      
      try {
        // Navigate to the URL
        await page.goto(url, { timeout: CONFIG.printablesApi.timeout });
        await this.humanLikeDelay('pageLoad');
        
        // Extract data using web scraping
        const data = await page.evaluate(() => {
          // Try multiple selectors for title with fallbacks
          const titleSelectors = [
            'h1.model-name',
            '.model-info h1',
            '.model-header h1',
            '.print-detail-title',
            'h1',
            'title'
          ];
          
          let title = 'Unknown Model';
          for (const selector of titleSelectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent && element.textContent.trim()) {
              title = element.textContent.trim();
              // If we found the title in the page title, clean it up
              if (selector === 'title') {
                // Remove "by User" and "| Printables" parts
                title = title.replace(/ by .*$/, '').replace(/ \| Printables$/, '');
              }
              break;
            }
          }
          
          // Try multiple selectors for description with fallbacks
          const descriptionSelectors = [
            '.model-description',
            '.description-content',
            '.print-detail-description',
            '.model-info .description',
            '[itemprop="description"]'
          ];
          
          let description = '';
          for (const selector of descriptionSelectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent && element.textContent.trim()) {
              description = element.textContent.trim();
              break;
            }
          }
          
          // Try multiple selectors for file list with fallbacks
          const fileListSelectors = [
            '.model-files-list .file-item',
            '.files-list .file-item',
            '.files-table tr',
            '.print-files-table tr',
            '.file-row'
          ];
          
          let fileElements: Element[] = [];
          for (const selector of fileListSelectors) {
            const elements = document.querySelectorAll(selector);
            if (elements && elements.length > 0) {
              fileElements = Array.from(elements);
              break;
            }
          }
          
          // If we still don't have file elements, try to find any links that might be files
          if (fileElements.length === 0) {
            const fileLinks = document.querySelectorAll('a[href*=".stl"], a[href*=".3mf"], a[href*=".obj"]');
            if (fileLinks && fileLinks.length > 0) {
              fileElements = Array.from(fileLinks).map(link => {
                // Create a div to represent a file item
                const div = document.createElement('div');
                const filename = link.textContent || 
                                (link.getAttribute('href') ? link.getAttribute('href') : 'unknown.stl');
                div.setAttribute('data-filename', filename);
                return div;
              });
            }
          }
          
          const files = fileElements.map((item) => {
            // Try different selectors for file name with fallbacks
            const nameSelectors = [
              '.file-name',
              'td:first-child',
              '.filename',
              'a[download]',
              'a'
            ];
            
            let name = 'unknown.stl';
            for (const selector of nameSelectors) {
              const element = item.querySelector(selector);
              if (element && element.textContent && element.textContent.trim()) {
                name = element.textContent.trim();
                break;
              }
            }
            
            // If we still don't have a name, check if the item itself has a data-filename attribute
            if (name === 'unknown.stl' && item.getAttribute('data-filename')) {
              name = item.getAttribute('data-filename');
            }
            
            // Try different selectors for file size with fallbacks
            const sizeSelectors = [
              '.file-size',
              'td:nth-child(2)',
              '.filesize',
              '.size'
            ];
            
            let size = '0 KB';
            for (const selector of sizeSelectors) {
              const element = item.querySelector(selector);
              if (element && element.textContent && element.textContent.trim()) {
                size = element.textContent.trim();
                break;
              }
            }
            
            return { name, size };
          });
          
          return {
            title,
            description,
            files,
          };
        });
        
        return data;
      } finally {
        await page.close();
      }
    } catch (error) {
      console.error('Error getting project data:', error);
      throw new Error(`Failed to get project data: ${error}`);
    } finally {
      await this.closeBrowser();
    }
  }

  async downloadFiles(url: string, destinationPath: string): Promise<string[]> {
    try {
      // Initialize browser if needed
      await this.initBrowser();
      if (!this.context) throw new Error('Browser context not initialized');

      // Wait for rate limiting
      await this.rateLimiter.waitForNextRequest();

      // Check if we can download
      if (!await this.downloadManager.canDownload()) {
        throw new Error('Download limit reached. Try again later.');
      }

      // Create a new page
      const page = await this.context.newPage();
      
      try {
        // Navigate to the URL
        await page.goto(url, { timeout: CONFIG.printablesApi.timeout });
        await this.humanLikeDelay('pageLoad');
        
        // Set up download handler
        const downloadedFiles: string[] = [];
        
        // Configure download behavior
        page.on('download', async download => {
          const fileName = download.suggestedFilename();
          const filePath = path.join(destinationPath, fileName);
          
          await download.saveAs(filePath);
          await this.downloadManager.trackDownload();
          
          downloadedFiles.push(fileName);
          console.log(`Downloaded: ${fileName}`);
        });

        // Try multiple download strategies
        
        // Strategy 1: Look for download buttons in the Files tab
        console.log("Trying to find download buttons in the Files tab...");
        
        // First, try to click on the Files tab if it exists
        try {
          const filesTabSelector = 'a[href="#files"], button:has-text("Files"), .nav-item:has-text("Files")';
          const filesTab = await page.$(filesTabSelector);
          if (filesTab) {
            await filesTab.click();
            await this.humanLikeDelay('interaction');
            console.log("Clicked on Files tab");
          }
        } catch (error) {
          console.warn("Could not find or click Files tab:", error);
        }
        
        // Find and click download buttons
        const downloadButtonSelectors = [
          '.download-button', 
          '.file-download-button', 
          'a[download]',
          'button:has-text("Download")',
          'a:has-text("Download")',
          '.file-item button',
          '.file-row button'
        ];
        
        const downloadButtons = await page.$$(downloadButtonSelectors.join(', '));
        console.log(`Found ${downloadButtons.length} download buttons`);
        
        for (const button of downloadButtons) {
          // Wait for rate limiting between downloads
          await this.rateLimiter.waitForNextRequest();
          await this.humanLikeDelay('download');
          
          try {
            // Click the download button
            await button.click();
            console.log("Clicked download button");
            
            // Wait for download to start
            await page.waitForTimeout(3000);
          } catch (error) {
            console.warn(`Failed to click download button: ${error}`);
          }
        }
        
        // Strategy 2: If no download buttons found or no files downloaded, try to find download links
        if (downloadButtons.length === 0 || downloadedFiles.length === 0) {
          console.log("Trying to find download links...");
          
          const downloadLinkSelectors = [
            'a[href*=".stl"]', 
            'a[href*=".3mf"]', 
            'a[href*=".obj"]',
            'a[href*="/download/"]'
          ];
          
          const downloadLinks = await page.$$eval(downloadLinkSelectors.join(', '), 
            links => links.map(link => ({
              url: link.getAttribute('href') || '',
              filename: link.getAttribute('download') || link.textContent || 'unknown.stl'
            }))
          );
          
          console.log(`Found ${downloadLinks.length} download links`);
          
          for (const link of downloadLinks) {
            // Only download supported file types or links with /download/ in the URL
            const ext = path.extname(link.filename).toLowerCase();
            const isDownloadLink = link.url.includes('/download/');
            
            if (!CONFIG.supportedFileTypes.includes(ext) && !isDownloadLink) {
              continue;
            }
            
            // Wait for rate limiting
            await this.rateLimiter.waitForNextRequest();
            await this.humanLikeDelay('download');
            
            try {
              // For relative URLs, make them absolute
              const absoluteUrl = link.url.startsWith('/')
                ? `${CONFIG.printablesApi.baseUrl}${link.url}`
                : link.url;
              
              console.log(`Trying to download from URL: ${absoluteUrl}`);
              
              // Navigate to download URL
              await page.goto(absoluteUrl, { timeout: CONFIG.printablesApi.timeout });
              
              // The download should trigger automatically
              await page.waitForTimeout(5000);
              
              // If no download triggered, try to find and click a download button on this page
              if (downloadedFiles.length === 0) {
                const directDownloadButtons = await page.$$('button:has-text("Download"), a:has-text("Download")');
                for (const button of directDownloadButtons) {
                  try {
                    await button.click();
                    await page.waitForTimeout(3000);
                  } catch (error) {
                    console.warn(`Failed to click direct download button: ${error}`);
                  }
                }
              }
            } catch (error) {
              console.warn(`Failed to download file ${link.filename}: ${error}`);
            }
          }
        }
        
        // Strategy 3: If still no files downloaded, try to find file table rows and click on them
        if (downloadedFiles.length === 0) {
          console.log("Trying to find file table rows...");
          
          const fileRowSelectors = [
            '.file-item', 
            '.file-row', 
            'tr:has(.file-name)',
            '.files-table tr'
          ];
          
          const fileRows = await page.$$(fileRowSelectors.join(', '));
          console.log(`Found ${fileRows.length} file rows`);
          
          for (const row of fileRows) {
            await this.rateLimiter.waitForNextRequest();
            await this.humanLikeDelay('interaction');
            
            try {
              // Try to find a download button within this row
              const rowButton = await row.$('button, a[href*="download"], a[download]');
              if (rowButton) {
                await rowButton.click();
                console.log("Clicked row download button");
                await page.waitForTimeout(3000);
              } else {
                // If no button found, try clicking the row itself
                await row.click();
                console.log("Clicked file row");
                await page.waitForTimeout(1000);
                
                // After clicking the row, look for a download button that might have appeared
                const popupButton = await page.$('button:has-text("Download"), a:has-text("Download")');
                if (popupButton) {
                  await popupButton.click();
                  console.log("Clicked popup download button");
                  await page.waitForTimeout(3000);
                }
              }
            } catch (error) {
              console.warn(`Failed to interact with file row: ${error}`);
            }
          }
        }
        
        // If we still have no files, create a dummy file with information
        if (downloadedFiles.length === 0) {
          console.log("No files could be downloaded automatically. Creating info file.");
          
          const infoFileName = "download_info.txt";
          const infoFilePath = path.join(destinationPath, infoFileName);
          
          const pageTitle = await page.title();
          const pageUrl = page.url();
          
          const infoContent = `
Model information:
-----------------
Title: ${pageTitle}
URL: ${pageUrl}
Date: ${new Date().toISOString()}

Note: Files could not be downloaded automatically.
Please visit the URL above to download the files manually.
          `.trim();
          
          await fs.writeFile(infoFilePath, infoContent);
          downloadedFiles.push(infoFileName);
          console.log(`Created info file: ${infoFileName}`);
        }
        
        return downloadedFiles;
      } finally {
        await page.close();
      }
    } catch (error) {
      console.error('Error downloading files:', error);
      throw new Error(`Failed to download files: ${error}`);
    } finally {
      // Close the browser after downloading
      await this.closeBrowser();
    }
  }

  /**
   * Extracts model URLs from a collection page
   */
  async getCollectionModelUrls(collectionUrl: string): Promise<string[]> {
    try {
      // Check if URL is a valid Printables collection URL
      const collectionRegex = /^https?:\/\/(www\.)?printables\.com\/(collection|collections)\/\d+(-[\w-]+)?/;
      if (!collectionRegex.test(collectionUrl)) {
        throw new Error(`Invalid Printables collection URL: ${collectionUrl}`);
      }

      // Initialize browser if needed
      await this.initBrowser();
      if (!this.context) throw new Error('Browser context not initialized');

      // Wait for rate limiting
      await this.rateLimiter.waitForNextRequest();

      // Create a new page
      const page = await this.context.newPage();
      
      try {
        // Navigate to the URL
        await page.goto(collectionUrl, { timeout: CONFIG.printablesApi.timeout });
        await this.humanLikeDelay('pageLoad');
        
        // Extract model URLs using web scraping
        const modelUrls = await page.evaluate(() => {
          // Try different selectors for model cards/links
          const modelElements = Array.from(
            document.querySelectorAll('.model-card a[href*="/model/"], .collection-item a[href*="/model/"], a[href*="/model/"]')
          );
          
          return modelElements
            .map(element => element.getAttribute('href'))
            .filter(href => href && href.includes('/model/'))
            .map(href => {
              // Convert relative URLs to absolute
              if (href && href.startsWith('/')) {
                return `https://printables.com${href}`;
              }
              return href;
            })
            .filter((value, index, self) => self.indexOf(value) === index); // Remove duplicates
        });
        
        console.log(`Found ${modelUrls.length} models in collection`);
        return modelUrls as string[];
      } finally {
        await page.close();
      }
    } catch (error) {
      console.error('Error getting collection models:', error);
      throw new Error(`Failed to get collection models: ${error}`);
    } finally {
      await this.closeBrowser();
    }
  }
}

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

class DownloadManager {
  private downloadCount = 0;
  private readonly maxDownloadsPerHour = 30;
  private downloadHistory: number[] = [];

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
