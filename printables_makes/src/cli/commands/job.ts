import chalk from 'chalk';
import { PrintJobService } from '../../services/PrintJobService';
import { ProjectService } from '../../services/ProjectService';
import { PrintJobStatus } from '../../types/PrintJob';
import { InteractivePrompts } from '../interactive';
import { formatPrinterSettings, parsePrinterSettings } from '../../utils/descriptionGenerator';

export class JobCommands {
  private printJobService: PrintJobService;
  private projectService: ProjectService;
  private interactivePrompts: InteractivePrompts;

  constructor() {
    this.printJobService = new PrintJobService();
    this.projectService = new ProjectService();
    this.interactivePrompts = new InteractivePrompts();
  }

  /**
   * Create a new print job
   */
  async create(name: string): Promise<void> {
    try {
      console.log(chalk.blue(`Creating print job: ${name}`));
      
      // Get printer settings interactively
      const printerSettings = await this.interactivePrompts.getPrinterSettings();
      
      const job = await this.printJobService.createPrintJob(name, {}, printerSettings);
      
      console.log(chalk.green(`Created print job "${job.name}" (ID: ${job.id})`));
    } catch (error) {
      console.error(chalk.red(`Error creating print job: ${error}`));
    }
  }

  /**
   * Add files to a print job
   */
  async addFiles(
    jobId: string,
    projectId?: string,
    files?: string[]
  ): Promise<void> {
    try {
      // Get job
      const job = await this.printJobService.getPrintJob(jobId);
      
      console.log(chalk.blue(`Adding files to print job: ${job.name} (${job.id})`));
      
      // If project ID is not provided, select interactively
      if (!projectId) {
        projectId = await this.interactivePrompts.selectProject();
      }
      
      // Get project
      const project = await this.projectService.getProject(projectId);
      
      // If files are not provided, select interactively
      if (!files || files.length === 0) {
        files = await this.interactivePrompts.selectFiles(projectId);
      }
      
      // Add files to job
      await this.printJobService.addFilesToJob(jobId, projectId, files);
      
      console.log(chalk.green(`Added files to print job:`));
      if (files) {
        files.forEach(file => {
          console.log(chalk.green(`  - ${file}`));
        });
      }
    } catch (error) {
      console.error(chalk.red(`Error adding files to print job: ${error}`));
    }
  }

  /**
   * Show job status and included files
   */
  async status(jobId: string): Promise<void> {
    try {
      const job = await this.printJobService.getPrintJob(jobId);
      
      console.log(chalk.blue(`Print Job: ${job.name} (${job.id})`));
      console.log(chalk.yellow(`Status: ${job.status.toUpperCase()}`));
      console.log(chalk.gray(`Created: ${new Date(job.createdDate).toLocaleString()}`));
      
      if (job.scheduledDate) {
        console.log(chalk.gray(`Started: ${new Date(job.scheduledDate).toLocaleString()}`));
      }
      
      if (job.completedDate) {
        console.log(chalk.gray(`Completed: ${new Date(job.completedDate).toLocaleString()}`));
      }
      
      if (job.photosAddedDate) {
        console.log(chalk.gray(`Photos Added: ${new Date(job.photosAddedDate).toLocaleString()}`));
      }
      
      // Display printer settings
      console.log(chalk.yellow('\nPrinter Settings:'));
      console.log(chalk.gray(formatPrinterSettings(job.printerSettings)));
      
      // Display projects and files
      console.log(chalk.yellow('\nProjects and Files:'));
      
      for (const [projectId, projectFiles] of Object.entries(job.projects)) {
        try {
          const project = await this.projectService.getProject(projectId);
          console.log(chalk.green(`  ${project.title} (${projectId}):`));
          
          // Display files
          projectFiles.files.forEach(file => {
            if (projectFiles.successfulFiles.includes(file)) {
              console.log(chalk.green(`    ✓ ${file}`));
            } else if (projectFiles.failedFiles.includes(file)) {
              console.log(chalk.red(`    ✗ ${file}`));
            } else {
              console.log(chalk.gray(`    ○ ${file}`));
            }
          });
        } catch (error) {
          console.log(chalk.yellow(`  Unknown Project (${projectId}):`));
          projectFiles.files.forEach(file => {
            console.log(chalk.gray(`    - ${file}`));
          });
        }
      }
      
      // Display photos
      if (job.photos) {
        console.log(chalk.yellow('\nPhotos:'));
        
        if (job.photos.overview && job.photos.overview.length > 0) {
          console.log(chalk.green(`  Overview Photos: ${job.photos.overview.length}`));
        }
        
        if (job.photos.files) {
          const totalFilePhotos = Object.values(job.photos.files).reduce(
            (sum, photos) => sum + photos.length,
            0
          );
          
          console.log(chalk.green(`  File Photos: ${totalFilePhotos}`));
          
          for (const [key, photos] of Object.entries(job.photos.files)) {
            console.log(chalk.gray(`    ${key}: ${photos.length} photos`));
          }
        }
      }
      
      // Display status history
      console.log(chalk.yellow('\nStatus History:'));
      job.statusHistory.forEach(entry => {
        const date = new Date(entry.date).toLocaleString();
        console.log(chalk.gray(`  ${date}: ${entry.status.toUpperCase()}`));
      });
    } catch (error) {
      console.error(chalk.red(`Error showing job status: ${error}`));
    }
  }

  /**
   * Update job status
   */
  async updateStatus(jobId: string, status: PrintJobStatus): Promise<void> {
    try {
      await this.printJobService.updateJobStatus(jobId, status);
      
      const job = await this.printJobService.getPrintJob(jobId);
      
      console.log(chalk.green(`Print job "${job.name}" marked as ${status.toUpperCase()}.`));
      
      // If job is completed, ask if user wants to add photos
      if (status === 'completed') {
        const addPhotos = await this.interactivePrompts.confirmAddPhotos();
        
        if (addPhotos) {
          // This will be handled by the photos command
          console.log(chalk.blue('Use the photos add command to add photos to this job.'));
        }
      }
    } catch (error) {
      console.error(chalk.red(`Error updating job status: ${error}`));
    }
  }

  /**
   * Mark job as partially successful
   */
  async markPartialSuccess(jobId: string, files?: string[]): Promise<void> {
    try {
      const job = await this.printJobService.getPrintJob(jobId);
      
      console.log(chalk.blue(`Marking job "${job.name}" as partially successful.`));
      
      // If files are not provided, select interactively
      if (!files || files.length === 0) {
        files = await this.interactivePrompts.selectSuccessfulFiles(jobId);
      }
      
      // Convert files to the expected format
      const successfulFiles: Record<string, string[]> = {};
      
      if (files) {
        files.forEach(file => {
          // Format: projectId/fileName
          const [projectId, fileName] = file.split('/');
          
          if (!projectId || !fileName) {
            console.warn(chalk.yellow(`Invalid file format: ${file}. Expected: projectId/fileName`));
            return;
          }
          
          if (!successfulFiles[projectId]) {
            successfulFiles[projectId] = [];
          }
          
          successfulFiles[projectId].push(fileName);
        });
      }
      
      // Mark job as partially successful
      await this.printJobService.markPartialSuccess(jobId, successfulFiles);
      
      console.log(chalk.green(`Print job "${job.name}" marked as PARTIALLY SUCCESSFUL.`));
      
      // Display successful files
      console.log(chalk.green('Successful files:'));
      if (files) {
        files.forEach(file => {
          console.log(chalk.green(`  - ${file}`));
        });
      }
      
      // Check if there are failed files
      const failedFiles: string[] = [];
      
      for (const [projectId, projectFiles] of Object.entries(job.projects)) {
        projectFiles.files.forEach(file => {
          const fileKey = `${projectId}/${file}`;
          if (!files || !files.includes(fileKey)) {
            failedFiles.push(fileKey);
          }
        });
      }
      
      if (failedFiles.length > 0) {
        console.log(chalk.red('Failed files:'));
        failedFiles.forEach(file => {
          console.log(chalk.red(`  - ${file}`));
        });
        
        // Ask if user wants to create a new job for failed files
        const createNewJob = await this.interactivePrompts.confirmCreateNewJob();
        
        if (createNewJob) {
          const newJobId = await this.printJobService.handleFailedFiles(jobId);
          
          if (newJobId) {
            console.log(chalk.green(`Created new print job for failed files (ID: ${newJobId}).`));
          } else {
            console.log(chalk.yellow('No failed files to create a new job for.'));
          }
        }
      }
    } catch (error) {
      console.error(chalk.red(`Error marking job as partially successful: ${error}`));
    }
  }
} 
