import { PrinterSettings } from '../types/Project';

/**
 * Generates a standardized make description from printer settings
 */
export const generateMakeDescription = (settings: PrinterSettings): string => {
  const template =
    `Printed on ${settings.printer} using ${settings.material} with ` +
    `${settings.nozzleSize} nozzle, ${settings.layerHeight} layers, ` +
    `${settings.infill} infill.`;

  return settings.supports ? `${template} Supports were used.` : template;
};

/**
 * Formats printer settings into a human-readable string
 */
export const formatPrinterSettings = (settings: PrinterSettings): string => {
  const lines = [
    `Printer: ${settings.printer}`,
    `Material: ${settings.material}`,
    `Nozzle Size: ${settings.nozzleSize}`,
    `Layer Height: ${settings.layerHeight}`,
    `Infill: ${settings.infill}`,
  ];

  if (settings.supports !== undefined) {
    lines.push(`Supports: ${settings.supports ? 'Yes' : 'No'}`);
  }

  // Add any other custom settings
  if (settings.otherSettings) {
    Object.entries(settings.otherSettings).forEach(([key, value]) => {
      lines.push(`${key}: ${value}`);
    });
  }

  return lines.join('\n');
};

/**
 * Parses printer settings from a string input
 * Format: key=value,key=value
 */
export const parsePrinterSettings = (input: string): Partial<PrinterSettings> => {
  const settings: Partial<PrinterSettings> = {};
  const otherSettings: Record<string, string> = {};

  const pairs = input.split(',');
  for (const pair of pairs) {
    const [key, value] = pair.split('=').map(s => s.trim());
    
    // Handle known settings
    switch (key.toLowerCase()) {
      case 'printer':
        settings.printer = value;
        break;
      case 'material':
        settings.material = value;
        break;
      case 'nozzle_size':
      case 'nozzlesize':
        settings.nozzleSize = value;
        break;
      case 'layer_height':
      case 'layerheight':
        settings.layerHeight = value;
        break;
      case 'infill':
        settings.infill = value;
        break;
      case 'supports':
        settings.supports = value.toLowerCase() === 'yes' || value === 'true' || value === '1';
        break;
      default:
        // Store as other setting
        otherSettings[key] = value;
    }
  }

  if (Object.keys(otherSettings).length > 0) {
    settings.otherSettings = otherSettings;
  }

  return settings;
}; 
