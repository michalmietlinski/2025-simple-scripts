# 📄 Batch File Minifier
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js Version](https://img.shields.io/badge/node-%3E%3D%2014.0.0-brightgreen.svg)](https://nodejs.org/)

A powerful command-line utility for batch minifying JavaScript, CSS, and HTML files with flexible output options, backup functionality, and cleanup tools.

## ✨ Features
- 🔄 Batch minify multiple file types
- 📁 Multiple output options:
  - Create new output directory
  - Create output directory within each input directory
  - Overwrite original files (with optional backup)
- 🏷️ Optional suffix for processed files
- 🌲 Recursive directory processing
- 💾 Automatic backup creation
- 🧹 Cleanup tools for processed files and backups
- 🎯 Support for js, css, and html files

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
2. Choose file types to minify
3. Choose output mode
4. Add optional suffix
5. Create backups (if overwriting)

Example:
```
Enter directory path (press Enter for current): ./src
Select file types to minify (js,css,html): js,css
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

## 📁 Directory Structure
```
your-project/
├── src/                    # Your source files
│   ├── scripts/
│   │   └── app.js
│   └── styles/
│       └── main.css
├── output/                 # Processed files (option 1)
│   ├── scripts/
│   │   └── app.min.js
│   └── styles/
│       └── main.min.css
├── src/output/            # Processed files (option 2)
│   ├── app.min.js
│   └── main.min.css
└── backup/                # Original files (when overwriting)
    ├── scripts/
    │   └── app.js
    └── styles/
        └── main.css
```

## ⚙️ Supported Formats
- JavaScript (.js)
- CSS (.css)
- HTML (.html, .htm)

## 🔧 Configuration
Default settings in src/utils/constants.js:
```
const SUPPORTED_FORMATS = ['.js', '.css', '.html', '.htm'];
const OUTPUT_DIR = 'output';    // Default output directory name
const BACKUP_DIR = 'backup';    // Default backup directory name
```

## 🚫 Ignored Directories
The following directories are automatically skipped:
- node_modules
- output directories
- backup directories

## 🛟 Error Handling
- Validates input directory existence
- Skips files that are already minified
- Creates directories as needed
- Provides detailed error messages
- Safe backup creation before overwriting
- Confirmation prompts for destructive operations

## 🤝 Contributing
1. Fork the repository
2. Create your feature branch (git checkout -b feature/amazing-feature)
3. Commit your changes (git commit -m 'Add amazing feature')
4. Push to the branch (git push origin feature/amazing-feature)
5. Open a Pull Request

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments
- Terser for JavaScript minification
- Clean-css for CSS minification
- Html-minifier for HTML minification
- Node.js for the runtime environment
