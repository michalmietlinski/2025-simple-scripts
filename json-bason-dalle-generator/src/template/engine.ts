import { ImageGenerationConfig, ExpandedPrompt } from '../types';

/**
 * Expands a template string by replacing variables with their values
 * @param template Template string with variables in {curly_braces}
 * @param variables Object containing variable values
 * @returns Expanded string with variables replaced
 */
export function expandTemplate(template: string, variables: Record<string, string>): string {
  return template.replace(/{([^{}]+)}/g, (match, key) => {
    const value = variables[key];
    if (value === undefined) {
      return match; // Keep the original placeholder if variable not found
    }
    return value;
  });
}

/**
 * Generates all possible combinations of variables
 * @param variables Object with arrays of variable values
 * @returns Array of objects, each containing one combination of variables
 */
export function generateCombinations(variables: Record<string, string[]>): Record<string, string>[] {
  // If no variables, return an empty object
  if (Object.keys(variables).length === 0) {
    return [{}];
  }

  // Start with an array containing one empty object
  let result: Record<string, string>[] = [{}];

  // For each variable, create new combinations
  Object.entries(variables).forEach(([key, values]) => {
    const newResult: Record<string, string>[] = [];

    // For each existing combination
    result.forEach(combination => {
      // For each value of the current variable
      values.forEach(value => {
        // Create a new combination with the current value
        newResult.push({
          ...combination,
          [key]: value
        });
      });
    });

    // Replace the result with the new combinations
    result = newResult;
  });

  return result;
}

/**
 * Expands a prompt template with all possible combinations of variables
 * @param config Image generation configuration
 * @returns Array of expanded prompts
 */
export function expandPromptTemplate(config: ImageGenerationConfig): ExpandedPrompt[] {
  const { prompt_template, variables } = config;
  
  // Generate all combinations of variables
  const combinations = generateCombinations(variables);
  
  // Expand the template for each combination
  return combinations.map(variableCombination => ({
    prompt: expandTemplate(prompt_template, variableCombination),
    variables: variableCombination,
    original_config: config
  }));
}

/**
 * Expands a filename template with variables
 * @param template Filename template
 * @param variables Variables to substitute
 * @param additionalVars Additional variables like timestamp
 * @returns Expanded filename
 */
export function expandFilenameTemplate(
  template: string, 
  variables: Record<string, string>,
  additionalVars: Record<string, string> = {}
): string {
  // Combine variables and additionalVars
  const allVars = { ...variables, ...additionalVars };
  
  // Expand the template
  const expanded = expandTemplate(template, allVars);
  
  // Sanitize the filename (remove characters that are invalid in filenames)
  return sanitizeFilename(expanded);
}

/**
 * Sanitizes a filename by removing invalid characters
 * @param filename Filename to sanitize
 * @returns Sanitized filename
 */
function sanitizeFilename(filename: string): string {
  // Replace invalid characters with underscores
  return filename
    .replace(/[/\\?%*:|"<>]/g, '_') // Invalid characters in most file systems
    .replace(/\s+/g, '_')           // Replace spaces with underscores
    .replace(/__+/g, '_')           // Replace multiple underscores with a single one
    .trim();
}

/**
 * Generates a hash for a prompt (for use in filenames)
 * @param prompt Prompt text
 * @returns Short hash string
 */
export function generatePromptHash(prompt: string): string {
  let hash = 0;
  for (let i = 0; i < prompt.length; i++) {
    const char = prompt.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  // Convert to a positive hexadecimal string and take the first 8 characters
  return Math.abs(hash).toString(16).substring(0, 8);
}

/**
 * Generates additional variables for templates
 * @returns Object with additional variables like timestamp
 */
export function generateAdditionalVariables(): Record<string, string> {
  const now = new Date();
  
  return {
    timestamp: now.toISOString().replace(/[:.]/g, '-'),
    date: now.toISOString().split('T')[0],
    time: now.toISOString().split('T')[1].split('.')[0].replace(/:/g, '-'),
    random: Math.random().toString(36).substring(2, 10)
  };
} 
