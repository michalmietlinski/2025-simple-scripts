import chalk from 'chalk';
import { PhotoService } from '../../services/PhotoService';
import { PrintJobService } from '../../services/PrintJobService';
import { PhotoAddOptions } from '../../types/PrintJob';

export class PhotoCommands {
  private photoService: PhotoService;
  private printJobService: PrintJobService;

  constructor() {
    this.photoService = new PhotoService();
    this.printJobService = new PrintJobService();
  }

  /**
   * Add photos to a job
   */
  async add(jobId: string, options: PhotoAddOptions): Promise<void> {
    try {
      console.log(chalk.blue(`Adding photo to job: ${jobId}`));
      
      // Validate options
      if (!options.overview && !options.file) {
        console.error(chalk.red('Either --overview or --file must be specified.'));
        return;
      }
      
      // Add photo
      await this.photoService.addPhotos(
        jobId,
        options.photoPath,
        options.overview,
        options.file
      );
      
      console.log(chalk.green('Photo added successfully.'));
      
      // Show job status
      const job = await this.printJobService.getPrintJob(jobId);
      
      if (options.overview) {
        console.log(chalk.green(`Overview photos: ${job.photos.overview.length}`));
      } else if (options.file) {
        const filePhotos = job.photos.files[options.file] || [];
        console.log(chalk.green(`Photos for ${options.file}: ${filePhotos.length}`));
      }
    } catch (error) {
      console.error(chalk.red(`Error adding photo: ${error}`));
    }
  }

  /**
   * List all photos in a job
   */
  async list(jobId: string): Promise<void> {
    try {
      const photos = await this.photoService.listPhotos(jobId);
      const job = await this.printJobService.getPrintJob(jobId);
      
      console.log(chalk.blue(`Photos for job: ${job.name} (${job.id})`));
      
      // Display overview photos
      if (photos.overview && photos.overview.length > 0) {
        console.log(chalk.yellow('\nOverview Photos:'));
        photos.overview.forEach(photo => {
          console.log(chalk.gray(`  - ${photo}`));
        });
      } else {
        console.log(chalk.yellow('\nNo overview photos.'));
      }
      
      // Display file photos
      if (photos.files && Object.keys(photos.files).length > 0) {
        console.log(chalk.yellow('\nFile Photos:'));
        
        for (const [key, filePhotos] of Object.entries(photos.files)) {
          console.log(chalk.green(`  ${key}:`));
          
          filePhotos.forEach(photo => {
            console.log(chalk.gray(`    - ${photo}`));
          });
        }
      } else {
        console.log(chalk.yellow('\nNo file photos.'));
      }
    } catch (error) {
      console.error(chalk.red(`Error listing photos: ${error}`));
    }
  }
} 
