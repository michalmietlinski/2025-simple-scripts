# 2025-simple-scripts
Set of simple scripts for 2025 - use if you want, will move more complex ones to separate repositories

# 2025 Simple Scripts Collection

A collection of utility scripts for various tasks.

## Projects Overview

| Project | Description | Technologies | Key Features |
|---------|-------------|--------------|--------------|
| batch-file-minifier | Batch image processing utility | - Node.js<br>- Sharp<br>- Inquirer | - Recursive image processing<br>- Multiple output modes<br>- Size presets<br>- Backup functionality<br>- Custom suffixes |
| simple-test-image-generator | Test image generation tool | - Node.js | - Clean up functionality<br>- Basic image generation |
| brave-extension-save-tabs | Browser extension for tab management | - JavaScript<br>- Browser API | - Save all tabs to file<br>- Export tabs as URLs<br>- Browser action button |


## Project Details

### batch-file-minifier
A flexible image processing utility that can handle batch operations on multiple images:
- Process images recursively in directories
- Multiple output modes (new directory, subdirectory, or in-place)
- Save and load dimension presets
- Automatic backup functionality
- Size suffix options

### simple-test-image-generator
Basic utility for generating test images:
- Generate simple test images
- Includes cleanup functionality

### brave-extension-save-tabs
Browser extension for saving and managing tabs:
- Export all open tabs to a text file
- Simple one-click operation via browser action
- Compatible with Chromium-based browsers


## Usage

Each project contains its own package.json with relevant scripts. Navigate to the project directory and use npm commands to run the utilities.

Example:
```bash
cd batch-file-minifier
npm install
npm start
```
