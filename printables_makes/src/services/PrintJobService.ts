import { PrintJob, PrintJobStatus, PhotoData } from '../types/PrintJob';
import { PrinterSettings } from '../types/Project';
import { StorageService } from './StorageService';
import { ProjectService } from './ProjectService';
import { generateUniqueId } from '../utils/fileUtils';
import { updatePrintJobStatus, updateProjectStatusesForJob } from '../utils/statusManager';

export class PrintJobService {
  private storageService: StorageService;
  private projectService: ProjectService;

  constructor() {
    this.storageService = new StorageService();
    this.projectService = new ProjectService();
  }

  /**
   * Creates a new print job
   */
  async createPrintJob(
    name: string,
    projects: Record<string, string[]> = {},
    printerSettings: PrinterSettings = {
      printer: '',
      material: '',
      nozzleSize: '',
      layerHeight: '',
      infill: '',
    }
  ): Promise<PrintJob> {
    // Create job ID
    const jobId = generateUniqueId('job');

    // Create job object
    const now = new Date().toISOString();
    const job: PrintJob = {
      id: jobId,
      name,
      status: 'planned',
      projects: {},
      printerSettings,
      createdDate: now,
      photos: {
        overview: [],
        files: {},
      },
      statusHistory: [
        {
          status: 'planned',
          date: now,
        },
      ],
    };

    // Add projects and files to job
    for (const [projectId, files] of Object.entries(projects)) {
      // Validate project exists
      const project = await this.projectService.getProject(projectId);
      
      // Validate files exist in project
      const validFiles = files.filter(file => project.files.includes(file));
      
      if (validFiles.length > 0) {
        job.projects[projectId] = {
          files: validFiles,
          successfulFiles: [],
          failedFiles: [],
        };
        
        // Add job ID to project's print jobs
        if (!project.printJobs.includes(jobId)) {
          project.printJobs.push(jobId);
          project.lastUpdated = now;
          await this.storageService.saveProject(project);
          
          // Update project status to scheduled if it's new
          if (project.status === 'new') {
            await this.projectService.updateProjectStatus(projectId, 'scheduled', jobId);
          }
        }
      }
    }

    // Save job
    await this.storageService.savePrintJob(job);

    return job;
  }

  /**
   * Gets a print job by ID
   */
  async getPrintJob(jobId: string): Promise<PrintJob> {
    const job = await this.storageService.getPrintJob(jobId);
    if (!job) {
      throw new Error(`Print job not found: ${jobId}`);
    }
    return job;
  }

  /**
   * Gets all print jobs
   */
  async getAllPrintJobs(): Promise<PrintJob[]> {
    return this.storageService.getAllPrintJobs();
  }

  /**
   * Updates a print job's status
   */
  async updateJobStatus(jobId: string, status: PrintJobStatus): Promise<void> {
    await updatePrintJobStatus(jobId, status);
  }

  /**
   * Adds files to a print job
   */
  async addFilesToJob(
    jobId: string,
    projectId: string,
    files: string[]
  ): Promise<void> {
    const job = await this.getPrintJob(jobId);
    const project = await this.projectService.getProject(projectId);
    
    // Validate files exist in project
    const validFiles = files.filter(file => project.files.includes(file));
    
    if (validFiles.length === 0) {
      throw new Error('No valid files to add to print job');
    }
    
    // Add files to job
    if (!job.projects[projectId]) {
      job.projects[projectId] = {
        files: validFiles,
        successfulFiles: [],
        failedFiles: [],
      };
    } else {
      // Add only files that aren't already in the job
      const existingFiles = new Set(job.projects[projectId].files);
      const newFiles = validFiles.filter(file => !existingFiles.has(file));
      
      if (newFiles.length > 0) {
        job.projects[projectId].files.push(...newFiles);
      } else {
        throw new Error('All files are already in the print job');
      }
    }
    
    // Add job ID to project's print jobs if not already there
    if (!project.printJobs.includes(jobId)) {
      project.printJobs.push(jobId);
      project.lastUpdated = new Date().toISOString();
      await this.storageService.saveProject(project);
      
      // Update project status to scheduled if it's new
      if (project.status === 'new') {
        await this.projectService.updateProjectStatus(projectId, 'scheduled', jobId);
      }
    }
    
    // Save job
    await this.storageService.savePrintJob(job);
  }

  /**
   * Marks a print job as partially successful
   */
  async markPartialSuccess(
    jobId: string,
    successfulFiles: Record<string, string[]>
  ): Promise<void> {
    const job = await this.getPrintJob(jobId);
    
    // Validate job status
    if (job.status !== 'in_progress') {
      throw new Error(`Cannot mark job as partially successful. Current status: ${job.status}`);
    }
    
    // Update job status
    await updatePrintJobStatus(jobId, 'partially_successful');
    
    // Update successful and failed files
    for (const [projectId, files] of Object.entries(successfulFiles)) {
      if (!job.projects[projectId]) {
        continue;
      }
      
      // Validate files exist in job
      const validFiles = files.filter(file => job.projects[projectId].files.includes(file));
      
      // Update successful files
      job.projects[projectId].successfulFiles = validFiles;
      
      // Update failed files (all files that aren't successful)
      job.projects[projectId].failedFiles = job.projects[projectId].files.filter(
        file => !validFiles.includes(file)
      );
      
      // Add successful prints to project
      for (const file of validFiles) {
        await this.projectService.addSuccessfulPrint(projectId, file, {
          printJob: jobId,
          printerSettings: job.printerSettings,
          makeDescription: '', // Will be generated by the ProjectService
        });
      }
    }
    
    // Save job
    await this.storageService.savePrintJob(job);
    
    // Update project statuses
    await updateProjectStatusesForJob(jobId);
  }

  /**
   * Creates a new print job for failed files
   */
  async handleFailedFiles(jobId: string): Promise<string | undefined> {
    const job = await this.getPrintJob(jobId);
    
    // Collect all failed files by project
    const failedFiles: Record<string, string[]> = {};
    
    for (const [projectId, projectData] of Object.entries(job.projects)) {
      if (projectData.failedFiles.length > 0) {
        failedFiles[projectId] = projectData.failedFiles;
      }
    }
    
    if (Object.keys(failedFiles).length > 0) {
      // Create new print job for failed files
      const newJob = await this.createPrintJob(
        `Retry - ${job.name}`,
        failedFiles,
        job.printerSettings
      );
      
      return newJob.id;
    }
    
    return undefined;
  }

  /**
   * Adds photos to a print job
   */
  async addPhotosToJob(jobId: string, photos: PhotoData): Promise<void> {
    const job = await this.getPrintJob(jobId);
    
    // Create photo directories if they don't exist
    await this.storageService.createPrintJobPhotoDirectories(jobId);
    
    // Add photos to job
    if (!job.photos) {
      job.photos = {
        overview: [],
        files: {},
      };
    }
    
    // Add overview photos
    if (photos.overview && photos.overview.length > 0) {
      job.photos.overview.push(...photos.overview);
    }
    
    // Add file photos
    for (const [key, filePhotos] of Object.entries(photos.files)) {
      if (!job.photos.files[key]) {
        job.photos.files[key] = [];
      }
      
      job.photos.files[key].push(...filePhotos);
    }
    
    // Update photos added date
    job.photosAddedDate = new Date().toISOString();
    
    // Save job
    await this.storageService.savePrintJob(job);
    
    // Update project statuses
    await updateProjectStatusesForJob(jobId);
  }
} 
