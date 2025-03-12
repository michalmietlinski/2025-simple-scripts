import fs from 'fs-extra';
import path from 'path';
import { PhotoData } from '../types/PrintJob';
import { StorageService } from './StorageService';
import { PrintJobService } from './PrintJobService';
import { generatePhotoName, fileExists } from '../utils/fileUtils';

export class PhotoService {
  private storageService: StorageService;
  private printJobService: PrintJobService;

  constructor() {
    this.storageService = new StorageService();
    this.printJobService = new PrintJobService();
  }

  /**
   * Adds photos to a print job
   */
  async addPhotos(
    jobId: string,
    photoPath: string,
    isOverview: boolean = false,
    projectAndFile?: string
  ): Promise<void> {
    // Validate job exists
    const job = await this.printJobService.getPrintJob(jobId);
    
    // Validate photo file exists
    if (!await fileExists(photoPath)) {
      throw new Error(`Photo file not found: ${photoPath}`);
    }
    
    // Create photo directories
    const directories = await this.storageService.createPrintJobPhotoDirectories(jobId);
    
    // Determine destination path and filename
    let destDir: string;
    let destFileName: string;
    
    if (isOverview) {
      // Handle overview photo
      destDir = directories.overview;
      destFileName = `overview_${Date.now()}${path.extname(photoPath)}`;
    } else if (projectAndFile) {
      // Handle file-specific photo
      // Validate format: projectId/filename
      const [projectId, fileName] = projectAndFile.split('/');
      
      if (!projectId || !fileName) {
        throw new Error('Invalid project/file format. Expected: projectId/fileName');
      }
      
      // Validate project and file exist in job
      if (!job.projects[projectId] || !job.projects[projectId].files.includes(fileName)) {
        throw new Error(`File ${fileName} not found in project ${projectId} for this job`);
      }
      
      destDir = directories.files;
      destFileName = generatePhotoName(projectId, fileName, path.extname(photoPath));
    } else {
      throw new Error('Either isOverview must be true or projectAndFile must be provided');
    }
    
    // Copy photo to destination
    const destPath = path.join(destDir, destFileName);
    await fs.copy(photoPath, destPath);
    
    // Update job with photo information
    const photoData: PhotoData = {
      overview: [],
      files: {},
    };
    
    if (isOverview) {
      photoData.overview = [destFileName];
    } else if (projectAndFile) {
      photoData.files[projectAndFile] = [destFileName];
    }
    
    // Add photos to job
    await this.printJobService.addPhotosToJob(jobId, photoData);
  }

  /**
   * Adds multiple photos to a print job with mapping
   */
  async addMultiplePhotos(
    jobId: string,
    photoMapping: Record<string, string[]>
  ): Promise<void> {
    // Validate job exists
    await this.printJobService.getPrintJob(jobId);
    
    // Create photo directories
    const directories = await this.storageService.createPrintJobPhotoDirectories(jobId);
    
    const photoData: PhotoData = {
      overview: [],
      files: {},
    };
    
    // Process overview photos
    if (photoMapping.overview) {
      for (const photoPath of photoMapping.overview) {
        // Validate photo file exists
        if (!await fileExists(photoPath)) {
          console.warn(`Photo file not found: ${photoPath}`);
          continue;
        }
        
        const destFileName = `overview_${Date.now()}${path.extname(photoPath)}`;
        const destPath = path.join(directories.overview, destFileName);
        
        // Copy photo to destination
        await fs.copy(photoPath, destPath);
        
        // Add to photo data
        photoData.overview.push(destFileName);
      }
    }
    
    // Process file photos
    for (const [projectAndFile, photoPaths] of Object.entries(photoMapping)) {
      // Skip overview key
      if (projectAndFile === 'overview') continue;
      
      // Validate format: projectId/filename
      const [projectId, fileName] = projectAndFile.split('/');
      
      if (!projectId || !fileName) {
        console.warn(`Invalid project/file format: ${projectAndFile}. Expected: projectId/fileName`);
        continue;
      }
      
      photoData.files[projectAndFile] = [];
      
      for (const photoPath of photoPaths) {
        // Validate photo file exists
        if (!await fileExists(photoPath)) {
          console.warn(`Photo file not found: ${photoPath}`);
          continue;
        }
        
        const destFileName = generatePhotoName(projectId, fileName, path.extname(photoPath));
        const destPath = path.join(directories.files, destFileName);
        
        // Copy photo to destination
        await fs.copy(photoPath, destPath);
        
        // Add to photo data
        photoData.files[projectAndFile].push(destFileName);
      }
    }
    
    // Add photos to job
    await this.printJobService.addPhotosToJob(jobId, photoData);
  }

  /**
   * Lists all photos for a print job
   */
  async listPhotos(jobId: string): Promise<PhotoData> {
    const job = await this.printJobService.getPrintJob(jobId);
    return job.photos || { overview: [], files: {} };
  }

  /**
   * Validates the structure of photo data
   */
  async validatePhotoStructure(photos: PhotoData): Promise<boolean> {
    // Check if overview is an array
    if (photos.overview && !Array.isArray(photos.overview)) {
      return false;
    }
    
    // Check if files is an object
    if (photos.files && typeof photos.files !== 'object') {
      return false;
    }
    
    // Check each file entry
    for (const [key, value] of Object.entries(photos.files)) {
      // Check if key has the format projectId/fileName
      if (!key.includes('/')) {
        return false;
      }
      
      // Check if value is an array
      if (!Array.isArray(value)) {
        return false;
      }
    }
    
    return true;
  }
} 
