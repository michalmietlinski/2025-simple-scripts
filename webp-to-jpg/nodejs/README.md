# Node.js WebP to JPG Converter

A Node.js-based tool that automatically converts WebP images to JPG format by watching a directory for new files.

## Features
- 📁 Directory watching
- 🔄 Automatic conversion
- 📦 Batch processing
- 🎨 High-quality conversion using Sharp

## Prerequisites
- Node.js installed on your system
- npm (Node Package Manager)

## Installation
1. Navigate to this directory:
   ```bash
   cd nodejs
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

## Usage
1. Start the converter:
   ```bash
   npm start
   ```
2. Place WebP files in the `input` directory
3. Find converted JPG files in the `output` directory

The tool will automatically:
- Create `input` and `output` directories if they don't exist
- Watch for new WebP files in the input directory
- Convert them to JPG format
- Save the converted files in the output directory

## Configuration
The default quality setting for JPG conversion is 90%. You can modify this in `convert.js` if needed. 
