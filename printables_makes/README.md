# Printables Tracker

A command-line tool to track and manage 3D printing projects from Printables.com.

## Features

- Add projects from Printables.com URLs
- Download project files automatically
- Organize projects by status (New, Scheduled, Made, Done)
- Create print jobs combining files from multiple projects
- Track print job status and success
- Manage photos of completed prints
- Generate make descriptions for Printables uploads

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd printables-tracker

# Install dependencies
npm install

# Build the project
npm run build

# Create a global link (optional)
npm link
```

## Usage

```bash
# Add a new project
printables-tracker project add https://printables.com/model/12345

# List all projects
printables-tracker project list

# Create a new print job
printables-tracker job create "Weekend Prints"

# Add files to a print job
printables-tracker job add-files <job_id>

# Mark a job as completed
printables-tracker job complete <job_id>

# Add photos to a job
printables-tracker photos add <job_id>

# Mark a project as uploaded to Printables
printables-tracker project done <project_id>
```

## Project Structure

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
├── src/
│   ├── index.ts                 # Application entry point
│   ├── types/                   # TypeScript type definitions
│   ├── services/                # Core functionality modules
│   ├── utils/                   # Helper functions
│   ├── config/                  # Configuration files
│   └── cli/                     # CLI commands and interfaces
└── dist/                        # Compiled JavaScript files
```

## License

ISC 
