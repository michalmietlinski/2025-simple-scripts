import fs from 'fs-extra';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';

/**
 * Creates a directory if it doesn't exist
 */
export const createDirectory = async (dirPath: string): Promise<void> => {
  try {
    await fs.ensureDir(dirPath);
  } catch (error) {
    console.error(`Error creating directory ${dirPath}:`, error);
    throw new Error(`Failed to create directory: ${error}`);
  }
};

/**
 * Moves files from source to destination
 */
export const moveFiles = async (source: string, destination: string): Promise<void> => {
  try {
    await fs.move(source, destination, { overwrite: true });
  } catch (error) {
    console.error(`Error moving files from ${source} to ${destination}:`, error);
    throw new Error(`Failed to move files: ${error}`);
  }
};

/**
 * Generates a unique ID for projects or print jobs
 */
export const generateUniqueId = (prefix: 'proj' | 'job'): string => {
  const timestamp = Date.now();
  const randomPart = uuidv4().substring(0, 8);
  return `${prefix}_${timestamp}_${randomPart}`;
};

/**
 * Sanitizes a filename to ensure it's safe for the file system
 */
export const sanitizeFileName = (fileName: string): string => {
  // Replace invalid characters with underscores
  return fileName
    .replace(/[<>:"/\\|?*]/g, '_')
    .replace(/\s+/g, '_')
    .trim();
};

/**
 * Checks if a file exists
 */
export const fileExists = async (filePath: string): Promise<boolean> => {
  try {
    return await fs.pathExists(filePath);
  } catch (error) {
    console.error(`Error checking if file exists ${filePath}:`, error);
    return false;
  }
};

/**
 * Gets the file extension
 */
export const getFileExtension = (fileName: string): string => {
  return path.extname(fileName).toLowerCase();
};

/**
 * Checks if a file is a supported 3D printing file
 */
export const isSupportedFile = (fileName: string, supportedTypes: string[]): boolean => {
  const ext = getFileExtension(fileName);
  return supportedTypes.includes(ext);
};

/**
 * Generates a photo name based on project ID and file name
 */
export const generatePhotoName = (projectId: string, fileName: string, photoExt: string): string => {
  const timestamp = Date.now();
  const sanitizedFileName = sanitizeFileName(path.basename(fileName, path.extname(fileName)));
  return `${projectId}_${sanitizedFileName}_${timestamp}${photoExt}`;
}; 
