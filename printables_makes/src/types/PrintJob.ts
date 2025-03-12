import { PrinterSettings } from './Project';

export type PrintJobStatus = 'planned' | 'in_progress' | 'completed' | 'partially_successful' | 'failed';

export interface StatusHistoryEntry {
  status: PrintJobStatus;
  date: string;
}

export interface ProjectFiles {
  files: string[];
  successfulFiles: string[];
  failedFiles: string[];
}

export interface PhotoData {
  overview: string[];
  files: {
    [projectAndFile: string]: string[];
  };
}

export interface PrintJob {
  id: string;
  name: string;
  status: PrintJobStatus;
  projects: {
    [projectId: string]: ProjectFiles;
  };
  printerSettings: PrinterSettings;
  createdDate: string;
  scheduledDate?: string;
  completedDate?: string;
  photosAddedDate?: string;
  photos: PhotoData;
  statusHistory: StatusHistoryEntry[];
}

export interface PhotoAddOptions {
  jobId: string;
  file?: string; // Format: "project_id/filename"
  overview?: boolean;
  photoPath: string;
}

export interface PartialSuccessOptions {
  jobId: string;
  files?: string[]; // If not provided, enter interactive mode
}

export interface AddFilesOptions {
  jobId: string;
  projectId?: string;
  files?: string[]; // If not provided, enter interactive mode
} 
