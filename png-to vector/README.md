# Image to SVG Converter

A Node.js utility to convert PNG and JPEG images to SVG vector format.

## Features

- Converts both PNG and JPEG images (jpg, jpeg) to SVG format
- Batch processes multiple files at once
- Processes files from subdirectories recursively
- Customizable input and output directories
- Automatically creates input/output directories as needed
- Parallel processing with concurrency control
- Uses Potrace algorithm for high-quality vectorization

## Installation

1. Clone this repository
2. Install dependencies:

```bash
npm install
```

## Usage

### Basic Usage

The script automatically creates `input` and `output` directories if they don't exist.

1. Place your image files (PNG, JPG, JPEG) in the `input` directory
2. Run the conversion:

```bash
npm start
```

3. Find your converted SVG files in the `output` directory, with the same directory structure as the input.

### Custom Directories

You can specify custom input and output directories:

```bash
node index.js /path/to/input/directory /path/to/output/directory
```

The script will create these directories if they don't exist.

## Development Notes

- The `input` and `output` directories are excluded from git to prevent committing large binary files
- You can modify the script behavior by editing the configuration variables at the top of `index.js`

## How It Works

1. The script recursively scans the input directory for supported image files
2. Files are processed in batches (default: 4 at a time) to improve performance
3. Each image is traced into vector paths using Potrace
4. SVG files are saved to the output directory, preserving the folder structure
5. A summary of the conversion process is displayed

## Configuration

You can modify the following constants in `index.js` to customize the behavior:

- `MAX_CONCURRENT`: Number of files to process simultaneously
- `RECURSIVE`: Whether to scan subdirectories for image files
- `SUPPORTED_EXTENSIONS`: Array of supported file extensions
- `potraceParams`: Vectorization settings:
  - `threshold`: Threshold for black and white (0-255)
  - `turdSize`: Suppress speckles of a specified size
  - `turnPolicy`: How to resolve ambiguities in path decomposition

## Troubleshooting

If you encounter errors during conversion:

- Check if the image files are valid and not corrupted
- Try adjusting the threshold parameter in `potraceParams`
- For large images, you may need to increase available memory

## Dependencies

- [potrace](https://www.npmjs.com/package/potrace) - For vectorization
- [jimp](https://www.npmjs.com/package/jimp) - For image processing
- [fs-extra](https://www.npmjs.com/package/fs-extra) - Enhanced file system operations

## License

MIT 
