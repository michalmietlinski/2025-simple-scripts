export type ProjectStatus = 'new' | 'scheduled' | 'made' | 'done';

export interface StatusHistoryEntry {
  status: ProjectStatus;
  date: string;
  printJob?: string;
}

export interface PrinterSettings {
  printer: string;
  material: string;
  nozzleSize: string;
  layerHeight: string;
  infill: string;
  supports?: boolean;
  otherSettings?: Record<string, string>;
}

export interface SuccessfulPrint {
  printJob: string;
  printerSettings: PrinterSettings;
  makeDescription: string;
}

export interface Project {
  id: string;
  url: string;
  title: string;
  status: ProjectStatus;
  printJobs: string[];
  files: string[];
  addedDate: string;
  lastUpdated: string;
  statusHistory: StatusHistoryEntry[];
  printablesUploadDate?: string;
  successfulPrints: {
    [filename: string]: SuccessfulPrint;
  };
}

export interface ProjectData {
  title: string;
  description: string;
  files: {
    name: string;
    size: string;
  }[];
} 
