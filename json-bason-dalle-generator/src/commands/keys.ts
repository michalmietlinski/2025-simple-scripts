import path from 'path';
import fs from 'fs-extra';
import chalk from 'chalk';
import ora from 'ora';
import { Command } from 'commander';
import { homedir } from 'os';

// Define the config directory in user's home
const CONFIG_DIR = path.join(homedir(), '.json-bason');
const KEYS_FILE = path.join(CONFIG_DIR, 'keys.json');

interface StoredKeys {
  'openai'?: string;
  'midjourney'?: string;
  'stability'?: string;
  [key: string]: string | undefined;
}

/**
 * Lists all stored API keys
 */
async function listKeys(): Promise<void> {
  try {
    // Ensure config directory exists
    await fs.ensureDir(CONFIG_DIR);

    // Check if keys file exists
    if (!await fs.pathExists(KEYS_FILE)) {
      console.log(chalk.yellow('No API keys stored.'));
      console.log(chalk.gray(`Use ${chalk.white('json-bason keys set <provider> <key>')} to add a key.`));
      return;
    }

    // Read keys
    const keys: StoredKeys = await fs.readJSON(KEYS_FILE);

    // Display keys
    console.log(chalk.bold('\nStored API Keys:'));
    Object.entries(keys).forEach(([provider, key]) => {
      if (key) {
        const maskedKey = `${key.substring(0, 4)}...${key.substring(key.length - 4)}`;
        console.log(`- ${chalk.cyan(provider)}: ${maskedKey}`);
      }
    });
  } catch (error) {
    console.error(chalk.red(`Error listing keys: ${error instanceof Error ? error.message : String(error)}`));
  }
}

/**
 * Sets an API key for a provider
 */
async function setKey(provider: string, key: string): Promise<void> {
  const spinner = ora('Storing API key').start();

  try {
    // Ensure config directory exists
    await fs.ensureDir(CONFIG_DIR);

    // Read existing keys if any
    let keys: StoredKeys = {};
    if (await fs.pathExists(KEYS_FILE)) {
      keys = await fs.readJSON(KEYS_FILE);
    }

    // Add or update key
    keys[provider.toLowerCase()] = key;

    // Save keys
    await fs.writeJSON(KEYS_FILE, keys, { spaces: 2 });

    spinner.succeed(`API key for ${provider} stored successfully`);
    console.log(chalk.yellow('\nNote: API keys are stored in plain text. Do not share your config directory.'));
  } catch (error) {
    spinner.fail(`Error storing API key: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Removes an API key for a provider
 */
async function removeKey(provider: string): Promise<void> {
  const spinner = ora('Removing API key').start();

  try {
    // Check if keys file exists
    if (!await fs.pathExists(KEYS_FILE)) {
      spinner.fail(`No API key found for ${provider}`);
      return;
    }

    // Read keys
    const keys: StoredKeys = await fs.readJSON(KEYS_FILE);

    // Remove key
    const normalizedProvider = provider.toLowerCase();
    if (!keys[normalizedProvider]) {
      spinner.fail(`No API key found for ${provider}`);
      return;
    }

    delete keys[normalizedProvider];

    // Save if there are remaining keys
    if (Object.keys(keys).length > 0) {
      await fs.writeJSON(KEYS_FILE, keys, { spaces: 2 });
    } else {
      // If no keys left, remove the file
      await fs.remove(KEYS_FILE);
    }

    spinner.succeed(`API key for ${provider} removed successfully`);
  } catch (error) {
    spinner.fail(`Error removing API key: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Gets an API key for a provider
 */
export async function getKey(provider: string): Promise<string | undefined> {
  try {
    // Check if keys file exists
    if (!await fs.pathExists(KEYS_FILE)) {
      return undefined;
    }

    // Read keys
    const keys: StoredKeys = await fs.readJSON(KEYS_FILE);
    return keys[provider.toLowerCase()];
  } catch (error) {
    console.error(chalk.red(`Error getting API key: ${error instanceof Error ? error.message : String(error)}`));
    return undefined;
  }
}

/**
 * Registers the keys command with the CLI
 * @param program Commander program instance
 */
export function registerKeysCommand(program: Command) {
  const keys = program
    .command('keys')
    .description('Manage API keys for different providers');

  keys
    .command('list')
    .description('List all stored API keys')
    .action(listKeys);

  keys
    .command('set')
    .description('Set an API key for a provider')
    .argument('<provider>', 'Provider name (openai, midjourney, stability)')
    .argument('<key>', 'API key')
    .action(setKey);

  keys
    .command('remove')
    .description('Remove an API key for a provider')
    .argument('<provider>', 'Provider name (openai, midjourney, stability)')
    .action(removeKey);
} 
