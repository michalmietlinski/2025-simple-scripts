# Implementation Plan

## Project Structure

1. Core Components

   - URL processor and validator
   - File downloader
   - Index manager
   - Project tracker
   - Storage manager
   - Status manager
   - Photo manager
   - Print job organizer

2. Directory Structure
   ```
   project_root/
   ├── data/
   │   ├── storage.json     # All metadata (projects and print jobs)
   │   ├── files/          # STL files storage
   │   │   ├── [project_id]/
   │   │   │   └── [filename.stl]
   │   └── photos/         # Photos storage
   │       ├── [job_id]/
   │       │   ├── overview/
   │       │   └── files/
   ├── src/
   └── config/
   ```

## Technology Stack

[To be determined based on preferences]
Suggested options:

- Python (for easy web scraping and file handling)
- SQLite/JSON (for index storage)
- Git (for version control)

## Development Phases

1. Phase 1: Core Infrastructure

   - Set up project structure
   - Implement URL processing
   - Create basic file management system

2. Phase 2: Data Management

   - Implement index system
   - Create make tracking functionality
   - Add verification system

3. Phase 3: User Interface

   - Implement CLI/GUI (to be determined)
   - Add user interaction features

4. Phase 4: Status Management
   - Implement status tracking system
   - Add photo management
   - Create print job organization
   - Add Printables upload tracking

[Additional sections to be filled based on technology choices and requirements clarification]

## Timeline

[To be filled after requirements confirmation]

## Testing Strategy

1. Unit Testing

   - URL processing validation
   - File management operations
   - Index operations

2. Integration Testing
   - End-to-end workflow testing
   - Data integrity verification

## Deployment Strategy

[To be determined based on preferred distribution method]

## Data Structure

1. Project Index (index.json)

   ```json
   {
     "projects": {
       "project_id_1": {
         "url": "https://printables.com/...",
         "status": "printed",
         "print_jobs": ["job_id_1", "job_id_2"],
         "files": ["file1.stl", "file2.stl"],
         "added_date": "2024-03-20",
         "last_updated": "2024-03-21",
         "status_history": [
           {
             "status": "new",
             "date": "2024-03-20T10:00:00Z"
           },
           {
             "status": "scheduled",
             "date": "2024-03-20T11:30:00Z",
             "print_job": "job_id_1"
           },
           {
             "status": "printed",
             "date": "2024-03-21T15:45:00Z",
             "print_job": "job_id_1"
           }
         ],
         "printables_upload_date": null,
         "successful_prints": {
           "file1.stl": {
             "print_job": "job_id_1",
             "printer_settings": {
               "printer": "Printer1",
               "material": "PLA",
               "nozzle_size": "0.4mm",
               "layer_height": "0.2mm",
               "infill": "20%",
               "supports": "yes"
             },
             "make_description": "Printed on Printer1 using PLA with 0.4mm nozzle, 0.2mm layers, 20% infill. Supports were used."
           }
         }
       }
     }
   }
   ```

2. Print Jobs Index (print_jobs.json)
   ```json
   {
     "print_jobs": {
       "job_id_1": {
         "name": "Combined Print 1",
         "status": "partially_successful",
         "projects": {
           "project_id_1": {
             "files": ["file1.stl"],
             "successful_files": ["file1.stl"],
             "failed_files": []
           },
           "project_id_2": {
             "files": ["part1.stl", "part2.stl"],
             "successful_files": ["part1.stl"],
             "failed_files": ["part2.stl"]
           }
         },
         "printer_settings": {
           "printer": "Printer1",
           "material": "PLA",
           "nozzle_size": "0.4mm",
           "layer_height": "0.2mm",
           "infill": "20%",
           "supports": "yes",
           "other_settings": {}
         },
         "created_date": "2024-03-20",
         "scheduled_date": "2024-03-22",
         "completed_date": "2024-03-23",
         "photos_added_date": "2024-03-23",
         "photos": {
           "overview": ["job_complete.jpg"],
           "files": {
             "project_id_1/file1.stl": ["photo1.jpg", "photo2.jpg"],
             "project_id_2/part1.stl": ["photo3.jpg"],
             "project_id_2/part2.stl": ["photo4.jpg", "photo5.jpg"]
           }
         },
         "status_history": [
           {
             "status": "planned",
             "date": "2024-03-20T10:00:00Z"
           },
           {
             "status": "in_progress",
             "date": "2024-03-22T09:00:00Z"
           },
           {
             "status": "completed",
             "date": "2024-03-23T14:30:00Z"
           }
         ]
       }
     }
   }
   ```

## Status Management Logic

1. Project Status Updates:

```typescript
async function updateProjectStatus(projectId: string): Promise<void> {
  const project = await getProject(projectId);
  const allFiles = new Set(project.files);
  const printedFiles = new Set<string>();

  // Check all print jobs containing this project
  for (const jobId of project.printJobs) {
    const job = await getPrintJob(jobId);
    if (job.status === 'completed' && job.photos) {
      job.projects[projectId].successfulFiles.forEach((file) =>
        printedFiles.add(file),
      );
    }
  }

  // Update project status based on printed files
  if (printedFiles.size === allFiles.size) {
    await setProjectStatus(projectId, 'made');
  }
}
```

2. Print Job Status Updates:

```typescript
async function completePrintJob(
  jobId: string,
  photos?: PhotoData,
): Promise<void> {
  const job = await getPrintJob(jobId);
  job.status = 'completed';
  job.completedDate = new Date().toISOString();

  if (photos) {
    job.photos = photos;
    job.photosAddedDate = new Date().toISOString();

    // Update status for all projects in this job
    for (const projectId of Object.keys(job.projects)) {
      await updateProjectStatus(projectId);
    }
  }

  await savePrintJob(job);
}
```

3. Photo Upload Logic:

```typescript
interface PhotoData {
  overview: string[];
  files: {
    [projectAndFile: string]: string[];
  };
}

async function addPhotosToJob(
  jobId: string,
  photosData: PhotoData,
): Promise<void> {
  const job = await getPrintJob(jobId);
  job.photos = photosData;
  job.photosAddedDate = new Date().toISOString();

  // Update project statuses based on photo evidence
  for (const projectId of Object.keys(job.projects)) {
    const allProjectFiles = new Set(job.projects[projectId].files);
    const photographedFiles = new Set(
      Object.keys(photosData.files)
        .filter((key) => key.startsWith(`${projectId}/`))
        .map((key) => key.split('/')[1]),
    );

    if (isSubset(allProjectFiles, photographedFiles)) {
      await updateProjectStatus(projectId);
    }
  }

  await savePrintJob(job);
}
```

4. Mark Print Job Partial Success:

```typescript
async function markPrintJobPartialSuccess(
  jobId: string,
  successfulFiles: Record<string, string[]>,
): Promise<void> {
  const job = await getPrintJob(jobId);
  job.status = 'partially_successful';

  for (const [projectId, files] of Object.entries(successfulFiles)) {
    const projectFiles = new Set(job.projects[projectId].files);
    const successFiles = new Set(files);

    job.projects[projectId].successfulFiles = Array.from(successFiles);
    job.projects[projectId].failedFiles = Array.from(
      difference(projectFiles, successFiles),
    );

    await updateProjectStatus(projectId);
  }

  await savePrintJob(job);
}
```

5. Auto Print Job Creation:

```typescript
async function handleFailedFiles(jobId: string): Promise<string | undefined> {
  const job = await getPrintJob(jobId);
  const failedFiles: Record<string, string[]> = {};

  // Collect all failed files by project
  for (const [projectId, projectData] of Object.entries(job.projects)) {
    if (projectData.failedFiles.length > 0) {
      failedFiles[projectId] = projectData.failedFiles;
    }
  }

  if (Object.keys(failedFiles).length > 0) {
    // Create new print job for failed files
    const newJobId = await createPrintJob({
      name: `Retry - ${job.name}`,
      projects: failedFiles,
      printerSettings: job.printerSettings, // Use same settings
    });
    return newJobId;
  }
}
```

6. Make Description Generator:

```typescript
interface PrinterSettings {
  printer: string;
  material: string;
  nozzleSize: string;
  layerHeight: string;
  infill: string;
  supports?: boolean;
}

function generateMakeDescription(settings: PrinterSettings): string {
  const template =
    `Printed on ${settings.printer} using ${settings.material} with ` +
    `${settings.nozzleSize} nozzle, ${settings.layerHeight} layers, ` +
    `${settings.infill} infill.`;

  return settings.supports ? `${template} Supports were used.` : template;
}
```

## Research Tasks

1. Printables API Investigation

   - Check API documentation availability
   - Verify authentication requirements
   - Test available endpoints:
     - Project data retrieval
     - File downloads
     - Make uploads (if possible)
   - Document rate limits and restrictions
   - Evaluate error handling needs

2. Auto Print Job Creation

   ```python
   def handle_failed_files(job_id):
       """
       Create new print jobs for failed files
       """
       job = get_print_job(job_id)
       failed_files = {}

       # Collect all failed files by project
       for project_id, project_data in job['projects'].items():
           if project_data['failed_files']:
               failed_files[project_id] = project_data['failed_files']

       if failed_files:
           # Create new print job for failed files
           new_job_id = create_print_job(
               name=f"Retry - {job['name']}",
               projects=failed_files,
               printer_settings=job['printer_settings']  # Use same settings
           )
           return new_job_id
   ```

3. Make Description Generator

   ```python
   def generate_make_description(settings):
       """
       Generate standardized make description from print settings
       """
       template = "Printed on {printer} using {material} with {nozzle_size} nozzle, {layer_height} layers, {infill} infill."
       if settings.get('supports') == 'yes':
           template += " Supports were used."

       return template.format(**settings)
   ```

## Data Storage Strategy

1. Single JSON File

   - All metadata stored in storage.json
   - Regular backups by file copy
   - Simple version control
   - No complex queries needed

2. File Organization
   - STL files stored by project ID
   - Photos stored by print job ID
   - Simple directory structure
   - Easy to browse and manage

## User Interface Options

1. Command Line Interface (CLI)

## CLI Implementation

1. Command Structure

   ```
   printables-tracker
   ├── project
   │   ├── add <url>
   │   ├── list
   │   ├── status <project_id>
   │   └── done <project_id>
   ├── job
   │   ├── create <name>
   │   ├── add-files <job_id> [project_id] [files...]
   │   ├── status <job_id>
   │   ├── start <job_id>
   │   ├── complete <job_id>
   │   └── partial <job_id>
   └── photos
       ├── add <job_id> [--file <project/file>] [--overview] <photo_path>
       └── list <job_id>
   ```

2. Interactive Mode
   - When project_id or files are not provided, enter interactive mode
   - Show numbered lists for selection
   - Support multiple selection for files
   - Validate inputs before processing
