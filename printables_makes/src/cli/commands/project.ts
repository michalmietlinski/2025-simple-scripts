import chalk from 'chalk';
import { ProjectService } from '../../services/ProjectService';
import { formatPrinterSettings } from '../../utils/descriptionGenerator';

export class ProjectCommands {
  private projectService: ProjectService;

  constructor() {
    this.projectService = new ProjectService();
  }

  /**
   * Add a new project from Printables URL
   */
  async add(url: string): Promise<void> {
    try {
      console.log(chalk.blue(`Adding project from URL: ${url}`));
      
      const project = await this.projectService.addProject(url);
      
      console.log(chalk.green(`Added project "${project.title}" (ID: ${project.id})`));
      console.log(chalk.green('Downloaded files:'));
      
      project.files.forEach(file => {
        console.log(chalk.green(`  - ${file}`));
      });
    } catch (error) {
      console.error(chalk.red(`Error adding project: ${error}`));
    }
  }

  /**
   * Add all projects from a Printables collection
   */
  async addCollection(url: string): Promise<void> {
    try {
      console.log(chalk.blue(`Adding collection from URL: ${url}`));
      
      const results = await this.projectService.addCollection(url);
      
      console.log(chalk.green(`Collection processing complete.`));
      console.log(chalk.green(`Added ${results.added.length} projects:`));
      
      results.added.forEach(project => {
        console.log(chalk.green(`  - ${project.title} (${project.id})`));
      });
      
      if (results.skipped.length > 0) {
        console.log(chalk.yellow(`Skipped ${results.skipped.length} existing projects.`));
      }
      
      if (results.failed.length > 0) {
        console.log(chalk.red(`Failed to add ${results.failed.length} projects:`));
        results.failed.forEach(failure => {
          console.log(chalk.red(`  - ${failure.url}: ${failure.error}`));
        });
      }
    } catch (error) {
      console.error(chalk.red(`Error adding collection: ${error}`));
    }
  }

  /**
   * List all projects
   */
  async list(): Promise<void> {
    try {
      const projects = await this.projectService.getAllProjects();
      
      if (projects.length === 0) {
        console.log(chalk.yellow('No projects found.'));
        return;
      }
      
      console.log(chalk.blue(`Found ${projects.length} projects:`));
      
      // Group projects by status
      const groupedProjects = projects.reduce((acc, project) => {
        if (!acc[project.status]) {
          acc[project.status] = [];
        }
        acc[project.status].push(project);
        return acc;
      }, {} as Record<string, typeof projects>);
      
      // Display projects by status
      for (const [status, statusProjects] of Object.entries(groupedProjects)) {
        console.log(chalk.yellow(`\n${status.toUpperCase()} (${statusProjects.length}):`));
        
        statusProjects.forEach(project => {
          console.log(chalk.green(`  ${project.id}: ${project.title}`));
          console.log(chalk.gray(`    URL: ${project.url}`));
          console.log(chalk.gray(`    Files: ${project.files.length}`));
          console.log(chalk.gray(`    Added: ${new Date(project.addedDate).toLocaleString()}`));
        });
      }
    } catch (error) {
      console.error(chalk.red(`Error listing projects: ${error}`));
    }
  }

  /**
   * Show project status and details
   */
  async status(projectId: string): Promise<void> {
    try {
      const project = await this.projectService.getProject(projectId);
      
      console.log(chalk.blue(`Project: ${project.title} (${project.id})`));
      console.log(chalk.yellow(`Status: ${project.status.toUpperCase()}`));
      console.log(chalk.gray(`URL: ${project.url}`));
      console.log(chalk.gray(`Added: ${new Date(project.addedDate).toLocaleString()}`));
      console.log(chalk.gray(`Last Updated: ${new Date(project.lastUpdated).toLocaleString()}`));
      
      if (project.printablesUploadDate) {
        console.log(chalk.gray(`Uploaded to Printables: ${new Date(project.printablesUploadDate).toLocaleString()}`));
      }
      
      // Display files
      console.log(chalk.yellow('\nFiles:'));
      project.files.forEach(file => {
        const printInfo = project.successfulPrints[file];
        
        if (printInfo) {
          console.log(chalk.green(`  ✓ ${file}`));
          console.log(chalk.gray(`    Printed in job: ${printInfo.printJob}`));
          console.log(chalk.gray(`    Settings: ${printInfo.printerSettings.printer}, ${printInfo.printerSettings.material}`));
        } else {
          console.log(chalk.gray(`  ○ ${file}`));
        }
      });
      
      // Display print jobs
      if (project.printJobs.length > 0) {
        console.log(chalk.yellow('\nPrint Jobs:'));
        project.printJobs.forEach(jobId => {
          console.log(chalk.gray(`  - ${jobId}`));
        });
      }
      
      // Display status history
      console.log(chalk.yellow('\nStatus History:'));
      project.statusHistory.forEach(entry => {
        const date = new Date(entry.date).toLocaleString();
        const jobInfo = entry.printJob ? ` (Job: ${entry.printJob})` : '';
        console.log(chalk.gray(`  ${date}: ${entry.status.toUpperCase()}${jobInfo}`));
      });
    } catch (error) {
      console.error(chalk.red(`Error showing project status: ${error}`));
    }
  }

  /**
   * Mark project as uploaded to Printables
   */
  async markDone(projectId: string): Promise<void> {
    try {
      await this.projectService.markProjectAsDone(projectId);
      
      const project = await this.projectService.getProject(projectId);
      
      console.log(chalk.green(`Project "${project.title}" marked as DONE.`));
      console.log(chalk.gray(`Upload date: ${new Date(project.printablesUploadDate!).toLocaleString()}`));
    } catch (error) {
      console.error(chalk.red(`Error marking project as done: ${error}`));
    }
  }
} 
