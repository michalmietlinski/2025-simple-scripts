import fs from 'fs-extra';
import path from 'path';
import { Storage } from '../types/Storage';
import { Project } from '../types/Project';
import { PrintJob } from '../types/PrintJob';
import { CONFIG } from '../config/settings';

export class StorageService {
  private dataPath: string = path.join(CONFIG.dataPath, 'storage.json');
  private data: Storage;

  constructor() {
    this.data = this.loadData();
  }

  private loadData(): Storage {
    try {
      if (fs.existsSync(this.dataPath)) {
        return JSON.parse(fs.readFileSync(this.dataPath, 'utf8'));
      }
    } catch (error) {
      console.error('Error loading data:', error);
    }
    
    // Initialize with empty data if file doesn't exist or is invalid
    return {
      projects: {},
      printJobs: {},
      version: '1.0.0',
      lastUpdated: new Date().toISOString(),
    };
  }

  private saveData(): void {
    try {
      // Ensure the directory exists
      fs.ensureDirSync(path.dirname(this.dataPath));
      
      // Update the lastUpdated timestamp
      this.data.lastUpdated = new Date().toISOString();
      
      // Write the data to file
      fs.writeFileSync(this.dataPath, JSON.stringify(this.data, null, 2));
    } catch (error) {
      console.error('Error saving data:', error);
      throw new Error(`Failed to save data: ${error}`);
    }
  }

  async getProject(id: string): Promise<Project | null> {
    return this.data.projects[id] || null;
  }

  async getAllProjects(): Promise<Project[]> {
    return Object.values(this.data.projects);
  }

  async saveProject(project: Project): Promise<void> {
    this.data.projects[project.id] = project;
    this.saveData();
  }

  async deleteProject(id: string): Promise<boolean> {
    if (this.data.projects[id]) {
      delete this.data.projects[id];
      this.saveData();
      return true;
    }
    return false;
  }

  async getPrintJob(id: string): Promise<PrintJob | null> {
    return this.data.printJobs[id] || null;
  }

  async getAllPrintJobs(): Promise<PrintJob[]> {
    return Object.values(this.data.printJobs);
  }

  async savePrintJob(job: PrintJob): Promise<void> {
    this.data.printJobs[job.id] = job;
    this.saveData();
  }

  async deletePrintJob(id: string): Promise<boolean> {
    if (this.data.printJobs[id]) {
      delete this.data.printJobs[id];
      this.saveData();
      return true;
    }
    return false;
  }

  async createProjectDirectory(projectId: string): Promise<string> {
    console.log(`Creating project directory for project ID: ${projectId}`);
    const projectDir = path.join(CONFIG.dataPath, 'files', projectId);
    console.log(`Project directory path: ${projectDir}`);
    
    try {
      await fs.ensureDir(projectDir);
      console.log(`Successfully created project directory: ${projectDir}`);
      
      // Verify the directory exists
      const exists = await fs.pathExists(projectDir);
      console.log(`Directory exists check: ${exists}`);
      
      return projectDir;
    } catch (error) {
      console.error(`Error creating project directory: ${error}`);
      throw new Error(`Failed to create project directory: ${error}`);
    }
  }

  async createPrintJobPhotoDirectories(jobId: string): Promise<{ overview: string; files: string }> {
    const jobDir = path.join(CONFIG.dataPath, 'photos', jobId);
    const overviewDir = path.join(jobDir, 'overview');
    const filesDir = path.join(jobDir, 'files');
    
    fs.ensureDirSync(overviewDir);
    fs.ensureDirSync(filesDir);
    
    return {
      overview: overviewDir,
      files: filesDir,
    };
  }

  async getProjectFilePath(projectId: string, fileName: string): Promise<string> {
    return path.join(CONFIG.dataPath, 'files', projectId, fileName);
  }

  async getPhotoPath(jobId: string, isOverview: boolean, fileName?: string): Promise<string> {
    if (isOverview) {
      return path.join(CONFIG.dataPath, 'photos', jobId, 'overview', fileName || '');
    } else {
      return path.join(CONFIG.dataPath, 'photos', jobId, 'files', fileName || '');
    }
  }
} 
