# 📄 Batch File Minifier
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js Version](https://img.shields.io/badge/node-%3E%3D%2014.0.0-brightgreen.svg)](https://nodejs.org/)


## ✨ Features
- 🔄 Batch change resolution multiple file types
- 📁 Multiple output options:
  - Create new output directory
  - Create output directory within each input directory
  - Overwrite original files (with optional backup)
- 🏷️ Optional suffix for processed files
- 🌲 Recursive directory processing
- 💾 Automatic backup creation
- 🧹 Cleanup tools for processed files and backups


## 🚀 Installation
```
# Clone the repository
git clone https://github.com/michalmietlinski/2025-simple-scripts.git

# Navigate to the project directory
cd batch-file-minifier

# Install dependencies
npm install
```

## 📖 Usage

### Process Files
```
npm start
# or
npm run process
```

Follow the interactive prompts to:
1. Select input directory
2. Choose max resolution
3. Choose output mode
4. Add optional suffix
5. Create backups (if overwriting)

Example:
```
Enter directory path (press Enter for current): ./src
Output options:
1. Create new output directory
2. Create output directory within each input directory
3. Overwrite original files
Choose output mode (1-3): 1
Add suffix to processed files? (y/N): y
Enter suffix (press Enter for 'min'): min
✓ Processed: output/scripts/app.min.js (Reduced by 40%)
✓ Processed: output/styles/main.min.css (Reduced by 35%)
```

### Clean Up Processed Files
```
npm run clean
```

Options:
1. Remove all suffixed files
2. Remove files with specific suffix (e.g., "min")

### Remove Backup Directories
```
npm run clean-backup
```


## 🔧 Configuration
Default settings in src/utils/constants.js:
```
const SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.gif'];
const OUTPUT_DIR = 'output';    // Default output directory name
const BACKUP_DIR = 'backup';    // Default backup directory name
```

## 🚫 Ignored Directories
The following directories are automatically skipped:
- node_modules
- output directories
- backup directories

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments
- Node.js for the runtime environment
