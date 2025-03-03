import { Provider, ImageModel } from '../types';
import { DallE3Provider } from './dalle3';

/**
 * Provider factory for creating image generation providers
 */
export class ProviderFactory {
  private providers: Record<ImageModel, Provider>;
  
  /**
   * Creates a new provider factory
   * @param apiKeys API keys for different providers
   */
  constructor(apiKeys: Record<string, string>) {
    this.providers = {} as Record<ImageModel, Provider>;
    
    // Initialize providers with available API keys
    if (apiKeys.openai) {
      this.providers['dall-e-3'] = new DallE3Provider(apiKeys.openai);
    }
    
    // TODO: Add more providers as they are implemented
    // if (apiKeys.midjourney) {
    //   this.providers['midjourney'] = new MidjourneyProvider(apiKeys.midjourney);
    // }
    // 
    // if (apiKeys.stabilityai) {
    //   this.providers['stable-diffusion-xl'] = new StableDiffusionProvider(apiKeys.stabilityai);
    // }
  }
  
  /**
   * Gets a provider by name
   * @param name Provider name
   * @returns Provider instance
   */
  getProvider(name: ImageModel): Provider {
    const provider = this.providers[name];
    
    if (!provider) {
      throw new Error(`Provider "${name}" not available. Make sure you have provided the necessary API key.`);
    }
    
    return provider;
  }
  
  /**
   * Gets all available providers
   * @returns Object mapping provider names to provider instances
   */
  getAllProviders(): Record<string, Provider> {
    return { ...this.providers };
  }
  
  /**
   * Checks if a provider is available
   * @param name Provider name
   * @returns Whether the provider is available
   */
  isProviderAvailable(name: ImageModel): boolean {
    return !!this.providers[name];
  }
  
  /**
   * Gets the names of all available providers
   * @returns Array of provider names
   */
  getAvailableProviderNames(): ImageModel[] {
    return Object.keys(this.providers) as ImageModel[];
  }
} 
