import { Project } from './Project';
import { PrintJob } from './PrintJob';

export interface Storage {
  projects: {
    [projectId: string]: Project;
  };
  printJobs: {
    [jobId: string]: PrintJob;
  };
  version: string;
  lastUpdated: string;
}

export interface ValidationResult {
  valid: boolean;
  issues: ValidationIssue[];
}

export interface ValidationIssue {
  type: 'missing_file' | 'missing_photo' | 'invalid_reference' | 'inconsistent_status';
  description: string;
  entityId: string;
  entityType: 'project' | 'print_job';
  fixable: boolean;
}

export interface FileNaming {
  projectId: string; // Format: proj_[timestamp]_[hash]
  fileName: string; // Original filename, sanitized
  photoName: string; // Format: [projectId]_[fileName]_[timestamp].[ext]
} 
