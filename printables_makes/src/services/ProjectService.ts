import { Project, ProjectStatus, SuccessfulPrint } from '../types/Project';
import { StorageService } from './StorageService';
import { PrintablesScraper } from './PrintablesAPI';
import { generateUniqueId } from '../utils/fileUtils';
import { updateProjectStatus } from '../utils/statusManager';
import { generateMakeDescription } from '../utils/descriptionGenerator';

export class ProjectService {
  private storageService: StorageService;
  private printablesScraper: PrintablesScraper;

  constructor() {
    this.storageService = new StorageService();
    this.printablesScraper = new PrintablesScraper();
  }

  /**
   * Adds a new project from a Printables URL
   */
  async addProject(url: string): Promise<Project> {
    // Validate URL
    const isValid = await this.printablesScraper.validateUrl(url);
    if (!isValid) {
      throw new Error(`Invalid Printables URL: ${url}`);
    }

    // Check if project already exists
    const existingProjects = await this.storageService.getAllProjects();
    const existingProject = existingProjects.find(p => p.url === url);
    if (existingProject) {
      return existingProject;
    }

    // Get project data from Printables
    const projectData = await this.printablesScraper.getProjectData(url);

    // Create project ID
    const projectId = generateUniqueId('proj');

    // Create project directory
    const projectDir = await this.storageService.createProjectDirectory(projectId);

    // Download files
    const downloadedFiles = await this.printablesScraper.downloadFiles(url, projectDir);

    // Create project object
    const now = new Date().toISOString();
    const project: Project = {
      id: projectId,
      url,
      title: projectData.title,
      status: 'new',
      printJobs: [],
      files: downloadedFiles,
      addedDate: now,
      lastUpdated: now,
      statusHistory: [
        {
          status: 'new',
          date: now,
        },
      ],
      successfulPrints: {},
    };

    // Save project
    await this.storageService.saveProject(project);

    return project;
  }

  /**
   * Gets a project by ID
   */
  async getProject(projectId: string): Promise<Project> {
    const project = await this.storageService.getProject(projectId);
    if (!project) {
      throw new Error(`Project not found: ${projectId}`);
    }
    return project;
  }

  /**
   * Gets all projects
   */
  async getAllProjects(): Promise<Project[]> {
    return this.storageService.getAllProjects();
  }

  /**
   * Updates a project's status
   */
  async updateProjectStatus(
    projectId: string,
    status: ProjectStatus,
    printJobId?: string
  ): Promise<void> {
    await updateProjectStatus(projectId, status, printJobId);
  }

  /**
   * Marks a project as done (uploaded to Printables)
   */
  async markProjectAsDone(projectId: string): Promise<void> {
    const project = await this.getProject(projectId);
    
    // Validate current status
    if (project.status !== 'made') {
      throw new Error(`Cannot mark project as done. Current status: ${project.status}`);
    }

    // Update status
    await updateProjectStatus(projectId, 'done');

    // Update upload date
    project.printablesUploadDate = new Date().toISOString();
    await this.storageService.saveProject(project);
  }

  /**
   * Adds a successful print record to a project
   */
  async addSuccessfulPrint(
    projectId: string,
    filename: string,
    printData: SuccessfulPrint
  ): Promise<void> {
    const project = await this.getProject(projectId);
    
    // Validate file exists in project
    if (!project.files.includes(filename)) {
      throw new Error(`File not found in project: ${filename}`);
    }

    // Add successful print record
    project.successfulPrints[filename] = {
      ...printData,
      makeDescription: generateMakeDescription(printData.printerSettings),
    };

    // Save project
    project.lastUpdated = new Date().toISOString();
    await this.storageService.saveProject(project);
  }

  /**
   * Generates a make description for a specific file
   */
  async generateMakeDescription(
    projectId: string,
    filename: string
  ): Promise<string> {
    const project = await this.getProject(projectId);
    
    // Check if file has a successful print record
    if (project.successfulPrints[filename]) {
      return project.successfulPrints[filename].makeDescription;
    }
    
    throw new Error(`No successful print record found for file: ${filename}`);
  }

  /**
   * Adds all projects from a Printables collection
   */
  async addCollection(collectionUrl: string): Promise<{
    added: Project[];
    skipped: string[];
    failed: { url: string; error: string }[];
  }> {
    // Get all model URLs from the collection
    const modelUrls = await this.printablesScraper.getCollectionModelUrls(collectionUrl);
    
    if (modelUrls.length === 0) {
      throw new Error('No models found in the collection');
    }
    
    console.log(`Found ${modelUrls.length} models in the collection. Starting to add them...`);
    
    const results = {
      added: [] as Project[],
      skipped: [] as string[],
      failed: [] as { url: string; error: string }[],
    };
    
    // Process each model URL
    for (const url of modelUrls) {
      try {
        // Check if project already exists
        const existingProjects = await this.storageService.getAllProjects();
        const existingProject = existingProjects.find(p => p.url === url);
        
        if (existingProject) {
          console.log(`Skipping existing project: ${url}`);
          results.skipped.push(url);
          continue;
        }
        
        // Add the project
        console.log(`Adding project: ${url}`);
        const project = await this.addProject(url);
        results.added.push(project);
        
        // Add a small delay between projects to avoid overwhelming the server
        await new Promise(resolve => setTimeout(resolve, 5000));
      } catch (error: any) {
        console.error(`Failed to add project ${url}: ${error}`);
        results.failed.push({ url, error: error.toString() });
      }
    }
    
    console.log(`Collection processing complete. Added: ${results.added.length}, Skipped: ${results.skipped.length}, Failed: ${results.failed.length}`);
    return results;
  }
} 
