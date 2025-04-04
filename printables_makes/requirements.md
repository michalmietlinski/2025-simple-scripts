# Project Requirements

## Overview

A tool to automate tracking and managing 3D printing projects from Printables.com. The system will help organize both planned and completed makes, download associated files, and maintain a searchable database of projects.

## Functional Requirements

1. URL Processing

   - Accept and process Printables.com URLs (single projects and collections)
   - Validate URLs for correct format and accessibility
   - Extract project information from the provided URLs

2. File Management

   - Automatically download project files to indexed directories
   - Create and maintain a simple file structure:
     - Single JSON file for all metadata (storage.json)
     - Files directory for STL files organized by project
     - Photos directory organized by print job
   - No database required, all data stored in JSON format
   - Simple backup by copying the data directory

3. Make Tracking

   - Track project status with following states:
     - New - Just added to system
     - Scheduled - Part of at least one scheduled print job
     - Made - All files printed and photos uploaded
     - Done - Project uploaded to Printables
   - Store printer settings used for successful prints
   - Status change rules updated:
     - Project is "Scheduled" when added to any print job
     - Project becomes "Made" when all its files have photos
     - "Done" status requires manual confirmation of Printables upload

4. Print Job Management

   - Create print jobs combining multiple STL files from different projects
   - Track relationships between print jobs and projects (many-to-many)
   - Store per-job information:
     - Included projects and their specific files
     - Print settings for the combined job (will be used to generate make descriptions)
     - Status tracking (Planned, In Progress, Completed, Partially Successful, Failed)
     - Successfully printed files tracking
     - Photos organization:
       - Overview photos of complete print job
       - Per-file photos with specific mapping
   - Partial success handling:
     - Track successfully printed files
     - Allow marking remaining files as failed
     - Update project statuses based on successful files
   - Allow splitting project files across multiple print jobs
   - Automatic project status updates when:
     - Job is marked as completed
     - Photos are uploaded to the job
   - Auto-create new print jobs for failed files (optional)

5. Photo Management
   - Allow multiple photos per printed file
   - Support overview photos of complete print jobs
   - Maintain clear mapping between photos and specific files
   - Use photo evidence to verify print completion
   - Support batch photo uploads with file mapping

## Non-Functional Requirements

1. Storage

   - Efficient file organization system
   - Backup capability for downloaded files
   - Version control for project files

2. Performance

   - Fast URL processing and validation
   - Efficient file downloading system
   - Quick search and verification of existing makes

3. Data Organization
   - Clear status tracking system
   - Organized photo storage
   - Efficient print job management
   - Easy status updates

## User Stories

1. As a user, I want to add a new project by providing a Printables URL
2. As a user, I want to check if I've already made a specific project
3. As a user, I want to download all files for a project automatically
4. As a user, I want to maintain an organized list of my planned and completed makes
5. As a user, I want to easily find the local files for any saved project
6. As a user, I want to group multiple STL files into a single print job
7. As a user, I want to mark prints as scheduled and track their status
8. As a user, I want to attach photos to completed prints
9. As a user, I want to mark projects as complete once uploaded to Printables
10. As a user, I want to see all my prints organized by status

## Constraints

1. System must work with Printables.com website structure
2. Must handle various file formats used in 3D printing
3. Must maintain data integrity between index file and stored projects

[Additional sections to be filled based on answers to clarifying questions]
