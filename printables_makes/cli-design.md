# CLI Design

## Command Structure

```
printables-tracker
├── project
│   ├── add <url>              # Add new project from Printables URL
│   ├── list                   # List all projects and their files
│   ├── status <project_id>    # Show project status and details
│   └── done <project_id>      # Mark project as uploaded to Printables
├── job
│   ├── create <name>          # Create new print job
│   ├── add-files <job_id>     # Add files to print job (interactive if no files specified)
│   ├── status <job_id>        # Show job status and included files
│   ├── start <job_id>         # Mark job as in progress
│   ├── complete <job_id>      # Mark entire job as completed
│   └── partial <job_id>       # Mark job as partially successful (interactive)
└── photos
    ├── add <job_id>           # Add photos to job (interactive if no files specified)
    └── list <job_id>          # List all photos in a job

```

## Interactive Flows

1. Adding Project:

```bash
$ printables-tracker project add https://printables.com/model/12345
> Added project "Cool Model" (ID: proj_123)
> Downloaded files:
>   - base.stl
>   - top_part.stl
>   - optional_stand.stl
```

2. Creating Print Job:

```bash
$ printables-tracker job create "Weekend Prints"
> Created print job "Weekend Prints" (ID: job_456)

$ printables-tracker job add-files job_456
> Select project (number or ID):
  1. Cool Model (proj_123)
  2. Another Model (proj_789)
> 1
> Available files:
  1. base.stl
  2. top_part.stl
  3. optional_stand.stl
> Select files (comma-separated numbers): 1,2
> Added files to print job:
  - base.stl
  - top_part.stl
```

3. Adding Photos:

```bash
$ printables-tracker photos add job_456
> Select photo type:
  1. Overview photo
  2. File-specific photo
> 2
> Select file:
  1. base.stl
  2. top_part.stl
> 1
> Enter photo path: ./photos/print1.jpg
> Added photo for base.stl
```

4. Direct Commands:

```bash
# Add files directly
$ printables-tracker job add-files job_456 proj_123 base.stl top_part.stl

# Add photos with specific mapping
$ printables-tracker photos add job_456 --file proj_123/base.stl ./photos/print1.jpg
$ printables-tracker photos add job_456 --overview ./photos/overview.jpg

# Mark job as partially successful
$ printables-tracker job partial job_456
> Select successful files:
  1. [proj_123] base.stl
  2. [proj_123] top_part.stl
> 1
> Marked base.stl as successful
> Remaining files will be marked as failed
```

## Implementation Classes

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

## Command Options

```typescript
interface PhotoAddOptions {
  jobId: string;
  file?: string; // Format: "project_id/filename"
  overview?: boolean;
  photoPath: string;
}

interface PartialSuccessOptions {
  jobId: string;
  files?: string[]; // If not provided, enter interactive mode
}

interface AddFilesOptions {
  jobId: string;
  projectId?: string;
  files?: string[]; // If not provided, enter interactive mode
}
```
