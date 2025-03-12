import inquirer from 'inquirer';
import { ProjectService } from '../services/ProjectService';
import { PrintJobService } from '../services/PrintJobService';
import { PrinterSettings } from '../types/Project';
import { parsePrinterSettings } from '../utils/descriptionGenerator';

export class InteractivePrompts {
  private projectService: ProjectService;
  private printJobService: PrintJobService;

  constructor() {
    this.projectService = new ProjectService();
    this.printJobService = new PrintJobService();
  }

  /**
   * Select a project interactively
   */
  async selectProject(): Promise<string> {
    const projects = await this.projectService.getAllProjects();
    
    if (projects.length === 0) {
      throw new Error('No projects found. Add a project first.');
    }
    
    const choices = projects.map(project => ({
      name: `${project.title} (${project.id})`,
      value: project.id,
    }));
    
    const { projectId } = await inquirer.prompt({
      type: 'list',
      name: 'projectId',
      message: 'Select a project:',
      choices,
    });
    
    return projectId;
  }

  /**
   * Select files from a project interactively
   */
  async selectFiles(projectId: string): Promise<string[]> {
    const project = await this.projectService.getProject(projectId);
    
    if (project.files.length === 0) {
      throw new Error('No files found in this project.');
    }
    
    const choices = project.files.map(file => ({
      name: file,
      value: file,
    }));
    
    const { files } = await inquirer.prompt({
      type: 'checkbox',
      name: 'files',
      message: 'Select files to add:',
      choices,
      validate: (input) => {
        if (input.length === 0) {
          return 'You must select at least one file.';
        }
        return true;
      },
    });
    
    return files;
  }

  /**
   * Select successful files from a print job interactively
   */
  async selectSuccessfulFiles(jobId: string): Promise<string[]> {
    const job = await this.printJobService.getPrintJob(jobId);
    
    const choices: { name: string; value: string }[] = [];
    
    for (const [projectId, projectFiles] of Object.entries(job.projects)) {
      try {
        const project = await this.projectService.getProject(projectId);
        
        projectFiles.files.forEach(file => {
          choices.push({
            name: `[${project.title}] ${file}`,
            value: `${projectId}/${file}`,
          });
        });
      } catch (error) {
        // If project not found, still add the files
        projectFiles.files.forEach(file => {
          choices.push({
            name: `[${projectId}] ${file}`,
            value: `${projectId}/${file}`,
          });
        });
      }
    }
    
    if (choices.length === 0) {
      throw new Error('No files found in this print job.');
    }
    
    const { files } = await inquirer.prompt({
      type: 'checkbox',
      name: 'files',
      message: 'Select successfully printed files:',
      choices,
      validate: (input) => {
        if (input.length === 0) {
          return 'You must select at least one file.';
        }
        return true;
      },
    });
    
    return files;
  }

  /**
   * Get printer settings interactively
   */
  async getPrinterSettings(): Promise<PrinterSettings> {
    const { settingsInput } = await inquirer.prompt({
      type: 'input',
      name: 'settingsInput',
      message: 'Enter printer settings (format: printer=Ender 3,material=PLA,nozzle_size=0.4mm,layer_height=0.2mm,infill=20%,supports=yes):',
      default: 'printer=Ender 3,material=PLA,nozzle_size=0.4mm,layer_height=0.2mm,infill=20%,supports=yes',
    });
    
    const settings = parsePrinterSettings(settingsInput);
    
    // Ensure all required fields are present
    const requiredFields = ['printer', 'material', 'nozzleSize', 'layerHeight', 'infill'];
    const missingFields = requiredFields.filter(field => !settings[field as keyof PrinterSettings]);
    
    if (missingFields.length > 0) {
      throw new Error(`Missing required printer settings: ${missingFields.join(', ')}`);
    }
    
    return settings as PrinterSettings;
  }

  /**
   * Confirm adding photos
   */
  async confirmAddPhotos(): Promise<boolean> {
    const { confirm } = await inquirer.prompt({
      type: 'confirm',
      name: 'confirm',
      message: 'Do you want to add photos now?',
      default: true,
    });
    
    return confirm;
  }

  /**
   * Confirm creating a new job for failed files
   */
  async confirmCreateNewJob(): Promise<boolean> {
    const { confirm } = await inquirer.prompt({
      type: 'confirm',
      name: 'confirm',
      message: 'Do you want to create a new print job for the failed files?',
      default: true,
    });
    
    return confirm;
  }
} 
