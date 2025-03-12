# Project Architecture

## Directory Structure

```
project_root/
├── src/
│   ├── index.ts                 # Application entry point
│   ├── types/                   # TypeScript type definitions
│   │   ├── Project.ts
│   │   ├── PrintJob.ts
│   │   └── Settings.ts
│   ├── services/               # Core functionality modules
│   │   ├── ProjectService.ts   # Project management
│   │   ├── PrintJobService.ts  # Print job management
│   │   ├── PhotoService.ts     # Photo management
│   │   ├── StorageService.ts   # File system operations
│   │   └── PrintablesAPI.ts    # Printables.com integration
│   ├── utils/                  # Helper functions
│   │   ├── statusManager.ts    # Status management logic
│   │   ├── descriptionGenerator.ts
│   │   └── fileUtils.ts
│   └── config/                 # Configuration files
│       └── settings.ts
├── data/                       # Data storage
│   ├── projects/
│   │   ├── [project_id]/
│   │   │   ├── files/
│   │   │   └── photos/
│   │   └── ...
│   ├── print_jobs/
│   │   ├── [job_id]/
│   │   │   ├── files/
│   │   │   └── photos/
│   │   └── ...
│   ├── index.json
│   └── print_jobs.json
├── package.json
└── tsconfig.json
```

## Core Types

```typescript
// types/Project.ts
interface Project {
  id: string;
  url: string;
  status: 'new' | 'scheduled' | 'made' | 'done';
  printJobs: string[];
  files: string[];
  addedDate: string;
  lastUpdated: string;
  statusHistory: StatusHistoryEntry[];
  printablesUploadDate?: string;
  successfulPrints: {
    [filename: string]: {
      printJob: string;
      printerSettings: PrinterSettings;
      makeDescription: string;
    };
  };
}

// types/PrintJob.ts
interface PrintJob {
  id: string;
  name: string;
  status:
    | 'planned'
    | 'in_progress'
    | 'completed'
    | 'partially_successful'
    | 'failed';
  projects: {
    [projectId: string]: {
      files: string[];
      successfulFiles: string[];
      failedFiles: string[];
    };
  };
  printerSettings: PrinterSettings;
  createdDate: string;
  scheduledDate?: string;
  completedDate?: string;
  photosAddedDate?: string;
  photos: {
    overview: string[];
    files: {
      [projectAndFile: string]: string[];
    };
  };
  statusHistory: StatusHistoryEntry[];
}
```

## Core Services

```typescript
// services/ProjectService.ts
class ProjectService {
  async addProject(url: string): Promise<Project>;
  async updateProjectStatus(
    projectId: string,
    status: ProjectStatus,
  ): Promise<void>;
  async getProject(projectId: string): Promise<Project>;
  async markProjectAsDone(projectId: string): Promise<void>;
  async generateMakeDescription(
    projectId: string,
    filename: string,
  ): Promise<string>;
}

// services/PrintJobService.ts
class PrintJobService {
  async createPrintJob(
    name: string,
    projects: Record<string, string[]>,
  ): Promise<PrintJob>;
  async updateJobStatus(jobId: string, status: PrintJobStatus): Promise<void>;
  async markPartialSuccess(
    jobId: string,
    successfulFiles: Record<string, string[]>,
  ): Promise<void>;
  async handleFailedFiles(jobId: string): Promise<string | undefined>;
  async addPhotosToJob(jobId: string, photos: PhotoData): Promise<void>;
}

// services/PhotoService.ts
class PhotoService {
  async addPhotos(jobId: string, photos: PhotoUpload): Promise<void>;
  async organizePhotos(
    jobId: string,
    photoMapping: PhotoMapping,
  ): Promise<void>;
  async validatePhotoStructure(photos: PhotoData): Promise<boolean>;
}

// services/StorageService.ts
interface Storage {
  projects: {
    [projectId: string]: Project;
  };
  printJobs: {
    [jobId: string]: PrintJob;
  };
}

class StorageService {
  private dataPath: string = './data/storage.json';
  private data: Storage;

  constructor() {
    this.data = this.loadData();
  }

  private loadData(): Storage {
    if (fs.existsSync(this.dataPath)) {
      return JSON.parse(fs.readFileSync(this.dataPath, 'utf8'));
    }
    return { projects: {}, printJobs: {} };
  }

  private saveData(): void {
    fs.writeFileSync(this.dataPath, JSON.stringify(this.data, null, 2));
  }

  async getProject(id: string): Promise<Project | null> {
    return this.data.projects[id] || null;
  }

  async saveProject(project: Project): Promise<void> {
    this.data.projects[project.id] = project;
    this.saveData();
  }

  async getPrintJob(id: string): Promise<PrintJob | null> {
    return this.data.printJobs[id] || null;
  }

  async savePrintJob(job: PrintJob): Promise<void> {
    this.data.printJobs[job.id] = job;
    this.saveData();
  }
}

// services/PrintablesAPI.ts
class PrintablesAPI {
  async getProjectData(url: string): Promise<ProjectData>;
  async downloadFiles(url: string, destinationPath: string): Promise<string[]>;
  async validateUrl(url: string): Promise<boolean>;
}
```

## Utility Functions

```typescript
// utils/statusManager.ts
export const updateProjectStatus = async (projectId: string): Promise<void>;
export const updatePrintJobStatus = async (jobId: string, status: PrintJobStatus): Promise<void>;
export const validateStatusTransition = (current: Status, next: Status): boolean;

// utils/descriptionGenerator.ts
export const generateMakeDescription = (settings: PrinterSettings): string;
export const formatPrinterSettings = (settings: PrinterSettings): string;

// utils/fileUtils.ts
export const createDirectory = async (path: string): Promise<void>;
export const moveFiles = async (source: string, destination: string): Promise<void>;
export const generateUniqueId = (): string;
```

## Main Application Flow

1. Adding New Project:

```typescript
// Example usage
const projectService = new ProjectService();
const printJobService = new PrintJobService();

// Add new project
const project = await projectService.addProject(
  'https://printables.com/model/12345',
);

// Create print job
const printJob = await printJobService.createPrintJob('Weekend Prints', {
  [project.id]: ['file1.stl', 'file2.stl'],
});

// Update status when printing starts
await printJobService.updateJobStatus(printJob.id, 'in_progress');

// Mark partial success with photos
await printJobService.markPartialSuccess(printJob.id, {
  [project.id]: ['file1.stl'],
});

// Add photos
await printJobService.addPhotosToJob(printJob.id, {
  overview: ['overview1.jpg'],
  files: {
    [`${project.id}/file1.stl`]: ['photo1.jpg', 'photo2.jpg'],
  },
});
```

## Configuration

```typescript
// config/settings.ts
export const CONFIG = {
  dataPath: './data',
  photoSizes: {
    maxWidth: 2048,
    maxHeight: 2048,
  },
  supportedFileTypes: ['.stl', '.3mf', '.obj'],
  printablesApi: {
    baseUrl: 'https://api.printables.com',
    timeout: 30000,
  },
};
```

## User Interface Components

```typescript
// src/cli/commands.ts
export class CliCommands {
  async addProject(url: string): Promise<void>;
  async createPrintJob(name: string): Promise<void>;
  async addFilesToJob(
    jobId: string,
    projectId: string,
    files: string[],
  ): Promise<void>;
  async updateJobStatus(jobId: string, status: PrintJobStatus): Promise<void>;
  async addPhotos(jobId: string, photos: string[]): Promise<void>;
}

// src/web/routes/projects.ts
export class ProjectRoutes {
  async listProjects(req: Request, res: Response): Promise<void>;
  async addProject(req: Request, res: Response): Promise<void>;
  async updateStatus(req: Request, res: Response): Promise<void>;
}

// src/web/routes/printJobs.ts
export class PrintJobRoutes {
  async listJobs(req: Request, res: Response): Promise<void>;
  async createJob(req: Request, res: Response): Promise<void>;
  async uploadPhotos(req: Request, res: Response): Promise<void>;
}
```

## CLI Interface

```typescript
// src/cli/commands/project.ts
export class ProjectCommands {
  async add(url: string): Promise<void>;
  async list(): Promise<void>;
  async status(projectId: string): Promise<void>;
  async markDone(projectId: string): Promise<void>;
}

// src/cli/commands/job.ts
export class JobCommands {
  async create(name: string): Promise<void>;
  async addFiles(
    jobId: string,
    projectId?: string,
    files?: string[],
  ): Promise<void>;
  async status(jobId: string): Promise<void>;
  async complete(jobId: string): Promise<void>;
  async markPartialSuccess(jobId: string): Promise<void>;
}

// src/cli/commands/photo.ts
export class PhotoCommands {
  async add(jobId: string, options: PhotoAddOptions): Promise<void>;
  async list(jobId: string): Promise<void>;
}

// src/cli/interactive.ts
export class InteractivePrompts {
  async selectProject(): Promise<string>;
  async selectFiles(projectId: string): Promise<string[]>;
  async selectPhotoType(): Promise<'overview' | 'file'>;
  async selectFileForPhoto(jobId: string): Promise<string>;
}
```
