import { Command } from 'commander';
import { registerInitCommand } from './init';
import { registerValidateCommand } from './validate';
import { registerEstimateCommand } from './estimate';
import { registerKeysCommand } from './keys';

/**
 * Registers all commands with the CLI
 * @param program Commander program instance
 */
export function registerCommands(program: Command): void {
  registerInitCommand(program);
  registerValidateCommand(program);
  registerEstimateCommand(program);
  registerKeysCommand(program);
  
  // Add more command registrations here as they are implemented
} 
