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
                const linkText = link.textContent || '';
                const hrefAttr = link.getAttribute('href');
                const filename = linkText || (hrefAttr ? hrefAttr : 'unknown.stl');
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
            if (name === 'unknown.stl') {
              const dataFilename = item.getAttribute('data-filename');
              if (dataFilename) {
                name = dataFilename;
              }
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
    console.log(`Starting download process for ${url}`);
    console.log(`Files will be saved to: ${destinationPath}`);
    
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

      // Create a new page with download permissions
      const page = await this.context.newPage();
      
      // Enable more verbose logging
      page.on('console', msg => console.log(`PAGE LOG: ${msg.text()}`));
      
      try {
        // Navigate to the URL
        console.log(`Navigating to ${url}`);
        await page.goto(url, { timeout: CONFIG.printablesApi.timeout, waitUntil: 'networkidle' });
        await this.humanLikeDelay('pageLoad');
        
        // Take a screenshot for debugging
        const screenshotPath = path.join(destinationPath, 'page_screenshot.png');
        console.log(`Taking screenshot and saving to: ${screenshotPath}`);
        await page.screenshot({ path: screenshotPath });
        console.log(`Saved screenshot to ${screenshotPath}`);
        
        // Set up download handler
        const downloadedFiles: string[] = [];
        
        // Configure download behavior
        page.on('download', async download => {
          const fileName = download.suggestedFilename();
          const filePath = path.join(destinationPath, fileName);
          
          console.log(`Download started: ${fileName}`);
          console.log(`Saving to: ${filePath}`);
          
          try {
            await fs.ensureDir(destinationPath);
            console.log(`Ensured directory exists: ${destinationPath}`);
            await download.saveAs(filePath);
            console.log(`File saved successfully: ${filePath}`);
            await this.downloadManager.trackDownload();
            
            downloadedFiles.push(fileName);
            console.log(`Added to downloaded files list: ${fileName}`);
          } catch (error) {
            console.error(`Error saving download ${fileName}:`, error);
          }
        });

        // Printables-specific strategy: Check for the new UI with download buttons
        console.log("Checking for Printables-specific download buttons...");
        
        // First, try to click on the Files tab if it exists (new UI)
        try {
          // Look for the Files tab in the new UI
          const filesTabSelectors = [
            'a[href="#files"]', 
            'button:has-text("Files")', 
            '.nav-item:has-text("Files")',
            'div[role="tab"]:has-text("Files")',
            'li:has-text("Files")'
          ];
          
          for (const selector of filesTabSelectors) {
            const filesTab = await page.$(selector);
            if (filesTab) {
              console.log(`Found Files tab with selector: ${selector}`);
              await filesTab.click();
              await this.humanLikeDelay('interaction');
              console.log("Clicked on Files tab");
              break;
            }
          }
        } catch (error) {
          console.warn("Could not find or click Files tab:", error);
        }
        
        // Wait for any dynamic content to load
        await page.waitForTimeout(2000);
        
        // Try to find the download all button first (most efficient)
        const downloadAllSelectors = [
          'button:has-text("Download All")',
          'a:has-text("Download All")',
          '.download-all-button'
        ];
        
        let downloadAllClicked = false;
        for (const selector of downloadAllSelectors) {
          try {
            const downloadAllButton = await page.$(selector);
            if (downloadAllButton) {
              console.log(`Found Download All button with selector: ${selector}`);
              await downloadAllButton.click();
              console.log("Clicked Download All button");
              await page.waitForTimeout(5000); // Wait longer for the zip to start downloading
              downloadAllClicked = true;
              break;
            }
          } catch (error) {
            console.warn(`Failed to click Download All button with selector ${selector}:`, error);
          }
        }
        
        // If we didn't click Download All, try individual file downloads
        if (!downloadAllClicked) {
          // Find and click download buttons for individual files
          const downloadButtonSelectors = [
            '.download-button', 
            '.file-download-button', 
            'a[download]',
            'button:has-text("Download")',
            'a:has-text("Download")',
            '.file-item button',
            '.file-row button',
            'button.btn-primary',
            'a.btn-primary'
          ];
          
          // Get all download buttons
          const downloadButtons = await page.$$(downloadButtonSelectors.join(', '));
          console.log(`Found ${downloadButtons.length} download buttons`);
          
          for (const button of downloadButtons) {
            // Wait for rate limiting between downloads
            await this.rateLimiter.waitForNextRequest();
            await this.humanLikeDelay('download');
            
            try {
              // Get button text for debugging
              const buttonText = await button.evaluate(el => el.textContent);
              console.log(`Attempting to click button: ${buttonText}`);
              
              // Click the download button
              await button.click();
              console.log("Clicked download button");
              
              // Wait for download to start
              await page.waitForTimeout(3000);
            } catch (error) {
              console.warn(`Failed to click download button: ${error}`);
            }
          }
        }
        
        // If no files downloaded yet, try to find download links
        if (downloadedFiles.length === 0) {
          console.log("Trying to find download links...");
          
          // Get all links on the page
          const allLinks = await page.$$eval('a', links => 
            links.map(link => ({
              url: link.href,
              text: link.textContent?.trim() || '',
              download: link.hasAttribute('download'),
              classes: link.className
            }))
          );
          
          console.log(`Found ${allLinks.length} links on the page`);
          console.log("Link samples:", allLinks.slice(0, 5));
          
          // Filter for potential download links
          const potentialDownloadLinks = allLinks.filter(link => 
            link.download || 
            link.url.includes('.stl') || 
            link.url.includes('.3mf') || 
            link.url.includes('.obj') ||
            link.url.includes('/download/') ||
            link.text.includes('Download')
          );
          
          console.log(`Found ${potentialDownloadLinks.length} potential download links`);
          
          // Try to click each potential download link
          for (const linkInfo of potentialDownloadLinks) {
            try {
              console.log(`Trying to click link: ${linkInfo.text} (${linkInfo.url})`);
              
              // Find the link on the page
              const link = await page.$(`a[href="${linkInfo.url}"]`);
              if (link) {
                await this.rateLimiter.waitForNextRequest();
                await this.humanLikeDelay('download');
                
                await link.click();
                console.log(`Clicked link: ${linkInfo.text}`);
                await page.waitForTimeout(3000);
              }
            } catch (error) {
              console.warn(`Failed to click link: ${linkInfo.text}`, error);
            }
          }
        }
        
        // If we still have no files, create a dummy file with information
        if (downloadedFiles.length === 0) {
          console.log("No files could be downloaded automatically. Creating info file.");
          
          // Save the page HTML for debugging
          const html = await page.content();
          const htmlPath = path.join(destinationPath, 'page_content.html');
          await fs.writeFile(htmlPath, html);
          console.log(`Saved page HTML to ${htmlPath}`);
          
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

The page screenshot and HTML content have been saved for debugging.
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
