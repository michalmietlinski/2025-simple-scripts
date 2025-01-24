# Tab Saver Chrome Extension

Tab Saver is a Chrome extension that helps you manage and organize your browser tabs by allowing you to save them to a file and import them back later. It preserves tab groups and their colors, making it perfect for managing multiple workspaces or projects.

## Features

- Save all open tabs to a file (JSON or TXT format)
- Import tabs from previously saved files
- Preserve tab groups and their colors
- Avoid duplicate tabs when importing
- Support for ungrouped tabs
- Simple and intuitive interface

## Installation

1. Clone this repository or download the source code
2. Open Chrome and navigate to ```chrome://extensions/``
3. Enable "Developer mode" in the top right corner
4. Click "Load unpacked" and select the extension directory

## Usage

### Saving Tabs

1. Click the Tab Saver icon in your Chrome toolbar
2. Select your preferred format:
   - Text File (.txt) - Human-readable format
   - JSON File (.json) - Better for programmatic processing
3. Click "Save Bookmarks"
4. Choose where to save the file on your computer

### Importing Tabs

1. Click the Tab Saver icon in your Chrome toolbar
2. Click "Import Tabs"
3. Select your previously saved .txt or .json file
4. The extension will:
   - Create new tab groups if they don't exist
   - Add tabs to existing groups if they match
   - Skip duplicate tabs within the same group
   - Show progress in the status window

### File Formats

#### Text Format (.txt)
```
=== Group Name (color) ===
  https://example.com
  https://another-example.com

=== Another Group (blue) ===
  https://some-url.com
```

#### JSON Format (.json)
```
{
  "Group Name (color)": [
    "https://example.com",
    "https://another-example.com"
  ],
  "Another Group (blue)": [
    "https://some-url.com"
  ]
}
```

## Permissions

The extension requires the following permissions:
- ```tabs```: To access and manage browser tabs
- ```downloads```: To save tab information to files
- ```activeTab```: To interact with the current tab
- ```tabGroups```: To manage tab groups
- ```<all_urls>```: To create new tabs with the saved URLs

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
