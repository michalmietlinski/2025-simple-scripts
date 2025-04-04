# Storage Design

## Directory Structure

```
project_root/
├── data/
│   ├── storage.json     # Main metadata store
│   ├── files/          # STL files storage
│   │   ├── [project_id]/
│   │   │   └── [filename.stl]
│   └── photos/         # Photos storage
│       ├── [job_id]/
│       │   ├── overview/
│       │   └── files/
└── backups/           # Automated backups
    └── YYYY-MM-DD/    # Daily snapshots
```

## File Naming Conventions

1. Project Files:

```typescript
interface FileNaming {
  projectId: string; // Format: proj_[timestamp]_[hash]
  fileName: string; // Original filename, sanitized
  photoName: string; // Format: [projectId]_[fileName]_[timestamp].[ext]
}
```

2. Examples:

```
Project ID  : proj_20240325_a1b2c3
File Name   : cool-model.stl -> cool-model.stl
Photo Name  : proj_20240325_a1b2c3_cool-model_12345.jpg
```

## Validation Rules

```typescript
export const StorageValidation = {
  files: {
    supportedFormats: ['.stl', '.3mf', '.obj'],
    maxSize: 100 * 1024 * 1024, // 100MB
    namePattern: /^[a-zA-Z0-9-_]+\.[a-zA-Z0-9]+$/,
  },
  photos: {
    supportedFormats: ['.jpg', '.jpeg', '.png'],
    maxSize: 10 * 1024 * 1024, // 10MB
    maxDimensions: {
      width: 4096,
      height: 4096,
    },
  },
  paths: {
    maxLength: 255,
    allowedChars: /^[a-zA-Z0-9-_/]+$/,
  },
};
```

## Backup Strategy

```typescript
interface BackupConfig {
  schedule: {
    frequency: 'daily' | 'hourly';
    time: string; // HH:mm format
    retention: number; // Days to keep
  };
  storage: {
    path: string;
    compress: boolean;
    maxSize: number; // Maximum backup size
  };
  validation: {
    validateOnBackup: boolean;
    repairOnRestore: boolean;
  };
}

const defaultBackupConfig: BackupConfig = {
  schedule: {
    frequency: 'daily',
    time: '00:00',
    retention: 7,
  },
  storage: {
    path: './backups',
    compress: true,
    maxSize: 1024 * 1024 * 1024, // 1GB
  },
  validation: {
    validateOnBackup: true,
    repairOnRestore: true,
  },
};
```

## Data Integrity

1. Validation:

```typescript
interface DataValidation {
  validateStorage(): Promise<ValidationResult>;
  validateProject(projectId: string): Promise<ValidationResult>;
  validatePrintJob(jobId: string): Promise<ValidationResult>;
  repairInconsistencies(issues: ValidationIssue[]): Promise<void>;
}
```

2. Error Recovery:

```typescript
interface ErrorRecovery {
  createSnapshot(): Promise<string>;
  restoreSnapshot(snapshotId: string): Promise<void>;
  rollbackChanges(timestamp: string): Promise<void>;
}
```

## Migration Strategy

1. Version Control:

```typescript
interface StorageVersion {
  version: string;
  timestamp: string;
  changes: string[];
}

interface MigrationStrategy {
  up(): Promise<void>;
  down(): Promise<void>;
  validate(): Promise<boolean>;
}
```
