import { Project, ProjectStatus } from '../types/Project';
import { PrintJob, PrintJobStatus } from '../types/PrintJob';
import { StorageService } from '../services/StorageService';

const storageService = new StorageService();

/**
 * Validates if a status transition is allowed for a project
 */
export const validateProjectStatusTransition = (
  current: ProjectStatus,
  next: ProjectStatus
): boolean => {
  // Define allowed transitions
  const allowedTransitions: Record<ProjectStatus, ProjectStatus[]> = {
    new: ['scheduled', 'made'],
    scheduled: ['made'],
    made: ['done'],
    done: [],
  };

  return allowedTransitions[current].includes(next);
};

/**
 * Validates if a status transition is allowed for a print job
 */
export const validatePrintJobStatusTransition = (
  current: PrintJobStatus,
  next: PrintJobStatus
): boolean => {
  // Define allowed transitions
  const allowedTransitions: Record<PrintJobStatus, PrintJobStatus[]> = {
    planned: ['in_progress'],
    in_progress: ['completed', 'partially_successful', 'failed'],
    completed: [],
    partially_successful: [],
    failed: [],
  };

  return allowedTransitions[current].includes(next);
};

/**
 * Updates a project's status and adds a status history entry
 */
export const updateProjectStatus = async (
  projectId: string,
  status: ProjectStatus,
  printJobId?: string
): Promise<void> => {
  const project = await storageService.getProject(projectId);
  if (!project) {
    throw new Error(`Project not found: ${projectId}`);
  }

  // Validate status transition
  if (!validateProjectStatusTransition(project.status, status)) {
    throw new Error(
      `Invalid status transition from ${project.status} to ${status}`
    );
  }

  // Update project status
  project.status = status;
  project.lastUpdated = new Date().toISOString();

  // Add status history entry
  project.statusHistory.push({
    status,
    date: new Date().toISOString(),
    printJob: printJobId,
  });

  // Save the updated project
  await storageService.saveProject(project);
};

/**
 * Updates a print job's status and adds a status history entry
 */
export const updatePrintJobStatus = async (
  jobId: string,
  status: PrintJobStatus
): Promise<void> => {
  const job = await storageService.getPrintJob(jobId);
  if (!job) {
    throw new Error(`Print job not found: ${jobId}`);
  }

  // Validate status transition
  if (!validatePrintJobStatusTransition(job.status, status)) {
    throw new Error(
      `Invalid status transition from ${job.status} to ${status}`
    );
  }

  // Update job status
  job.status = status;

  // Update date fields based on status
  if (status === 'in_progress') {
    job.scheduledDate = new Date().toISOString();
  } else if (
    status === 'completed' ||
    status === 'partially_successful' ||
    status === 'failed'
  ) {
    job.completedDate = new Date().toISOString();
  }

  // Add status history entry
  job.statusHistory.push({
    status,
    date: new Date().toISOString(),
  });

  // Save the updated job
  await storageService.savePrintJob(job);

  // If job is completed or partially successful, update project statuses
  if (status === 'completed' || status === 'partially_successful') {
    await updateProjectStatusesForJob(jobId);
  }
};

/**
 * Updates project statuses based on print job status
 */
export const updateProjectStatusesForJob = async (
  jobId: string
): Promise<void> => {
  const job = await storageService.getPrintJob(jobId);
  if (!job) {
    throw new Error(`Print job not found: ${jobId}`);
  }

  // Only process completed or partially successful jobs
  if (job.status !== 'completed' && job.status !== 'partially_successful') {
    return;
  }

  // Process each project in the job
  for (const [projectId, projectFiles] of Object.entries(job.projects)) {
    const project = await storageService.getProject(projectId);
    if (!project) continue;

    // If project is already 'made' or 'done', skip it
    if (project.status === 'made' || project.status === 'done') {
      continue;
    }

    // If job is completed, mark project as scheduled (if it's new)
    if (project.status === 'new') {
      await updateProjectStatus(projectId, 'scheduled', jobId);
    }

    // Check if all files for this project have photos
    const hasPhotosForAllFiles =
      job.photos &&
      job.photos.files &&
      projectFiles.successfulFiles.every((file) => {
        const key = `${projectId}/${file}`;
        return job.photos.files[key] && job.photos.files[key].length > 0;
      });

    // If all files have photos, mark project as 'made'
    if (
      hasPhotosForAllFiles &&
      project.status === 'scheduled' &&
      projectFiles.successfulFiles.length === projectFiles.files.length
    ) {
      await updateProjectStatus(projectId, 'made', jobId);
    }
  }
}; 
