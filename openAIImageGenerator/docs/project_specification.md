# DALL-E Image Generator Project Specification

## Project Overview
A GUI application for generating images using OpenAI's DALL-E model, with prompt management, token usage tracking, and organized image storage.

## Core Features

### Image Generation
- Connect to OpenAI API for DALL-E image generation
- Support for different image sizes (256x256, 512x512, 1024x1024, etc.)
- Quality and style parameter controls
- Preview generated images in the application
- Upload reference images to inspire DALL-E generations
- Support for image variations based on uploaded examples

### Prompt Management
- Text area for entering generation prompts
- Save history of all prompts used
- Display prompt history in the GUI
- Allow reusing previous prompts
- Search/filter through prompt history
- Import/export prompt history in JSON/CSV formats
- Batch export of favorite or filtered prompts
- AI-assisted prompt enhancement using OpenAI models
- Prompt analysis to suggest improvements for better results
- Template prompts with variable substitution for batch generation
- Collection generation using variable lists within rate limits

### API Key Management
- First-run dialog to input OpenAI API key
- Store API key securely in `.env` file (gitignored)
- Settings menu to update API key
- Validate API key before saving
- Basic obfuscation for stored key

### Token Usage Tracking
- Monitor and display token usage for each generation
- Track cumulative usage and estimated costs
- Display usage statistics in the GUI
- Export usage reports

### File Management
- Save generated images in date-organized directories
- Include descriptive filenames with timestamps and prompt summaries
- Option to add custom descriptions to filenames
- Thumbnail view of previously generated images

## Technical Specifications

### Project Structure 

### Technology Stack
- Python 3.7+
- Tkinter for GUI
- OpenAI Python library
- SQLite for prompt history storage
- dotenv for environment variable management
- pytest for automated testing
- Pillow for image processing and manipulation
- requests for API communication
- python-dateutil for date handling
- ttkthemes for enhanced UI themes
- SpeechRecognition for voice-to-prompt functionality
- opencv-python for advanced image processing
- numpy for numerical operations
- matplotlib for usage statistics visualization
- pdfkit for PDF export capabilities
- pyperclip for clipboard integration

### Database Structure
- **prompt_history** table:
  - id: INTEGER PRIMARY KEY
  - prompt_text: TEXT
  - creation_date: TIMESTAMP
  - last_used: TIMESTAMP
  - favorite: BOOLEAN
  - tags: TEXT (comma-separated)
  - usage_count: INTEGER
  - average_rating: FLOAT
  - is_template: BOOLEAN
  - template_variables: TEXT (JSON string of variable names)
  - version: INTEGER
  - parent_id: INTEGER (for tracking prompt versions)

- **template_variables** table:
  - id: INTEGER PRIMARY KEY
  - name: TEXT
  - values: TEXT (JSON array of possible values)
  - creation_date: TIMESTAMP
  - last_used: TIMESTAMP
  - usage_count: INTEGER
  - category: TEXT

- **batch_generations** table:
  - id: INTEGER PRIMARY KEY
  - template_prompt_id: INTEGER (foreign key to prompt_history)
  - start_time: TIMESTAMP
  - end_time: TIMESTAMP
  - total_images: INTEGER
  - completed_images: INTEGER
  - status: TEXT
  - variable_combinations: TEXT (JSON string of used combinations)
  - priority: INTEGER
  - error_count: INTEGER
  - retry_count: INTEGER

- **generation_history** table:
  - id: INTEGER PRIMARY KEY
  - prompt_id: INTEGER (foreign key to prompt_history)
  - batch_id: INTEGER (foreign key to batch_generations, nullable)
  - image_path: TEXT
  - generation_date: TIMESTAMP
  - parameters: TEXT (JSON string of generation parameters)
  - token_usage: INTEGER
  - cost: FLOAT
  - user_rating: INTEGER
  - description: TEXT
  - model: TEXT
  - size: TEXT
  - style: TEXT
  - quality: TEXT

- **usage_statistics** table:
  - id: INTEGER PRIMARY KEY
  - date: DATE
  - total_tokens: INTEGER
  - total_cost: FLOAT
  - generations_count: INTEGER
  - model: TEXT

- **tags** table:
  - id: INTEGER PRIMARY KEY
  - name: TEXT
  - color: TEXT
  - category: TEXT
  - usage_count: INTEGER

- **prompt_tags** table:
  - id: INTEGER PRIMARY KEY
  - prompt_id: INTEGER (foreign key to prompt_history)
  - tag_id: INTEGER (foreign key to tags)

- **user_preferences** table:
  - id: INTEGER PRIMARY KEY
  - key: TEXT
  - value: TEXT
  - category: TEXT
  - last_updated: TIMESTAMP

- **schema_version** table:
  - id: INTEGER PRIMARY KEY
  - version: INTEGER
  - migration_date: TIMESTAMP
  - description: TEXT

### Testing Implementation
- Unit tests for all utility modules
- Integration tests for API interactions
- GUI tests using pytest-tk
- Test fixtures for database operations
- Mock OpenAI API responses for testing without API calls
- Performance testing for database operations
- Test coverage reporting

### GUI Layout
- Prompt input section
- Generation controls panel
- Image preview area
- Prompt history sidebar
- Usage statistics dashboard
- Settings menu

## Implementation Decisions
- Use SQLite database for prompt history for persistence and searchability
- Implement tabbed interface for switching between generation and history views
- Include export functionality for both images and usage data
- Add basic error handling for API failures
- Implement simple caching to avoid regenerating identical prompts
- Support import/export of prompt history in JSON/CSV formats
- Allow batch export of favorite or filtered prompts
- Integrate OpenAI's text models to analyze and enhance prompts
- Track which prompt improvements led to better results
- Rate limiting system for batch generations to comply with OpenAI limits
- Variable substitution engine for template-based prompt generation

## Future Enhancements (Optional)
- Batch processing of multiple prompts
- Image editing capabilities
- Integration with other AI image models
- Advanced prompt templates and variables
- Prompt categorization and tagging system
- AI-powered prompt generation based on themes or concepts
- Learning system that improves suggestions based on user preferences
- Support for DALL-E 3 HD and other upcoming model improvements
- Integration with local LLMs for offline prompt enhancement
- Image variation controls with fine-tuning parameters
- Collaborative prompt library with sharing capabilities
- Export to various formats including PDF portfolios
- Custom UI themes and layout customization
- Voice-to-prompt functionality using speech recognition
- Mobile companion app for viewing and sharing generated images
- Template cloning for faster workflow
- Enhanced image viewing with zoom and scroll capabilities (Implemented)
- Direct access to output folders from the application (Implemented)
- Dynamic model selection based on API key capabilities
- Real-time usage statistics display during generation

## Upcoming Development (Next Release)
### Enhanced Prompt Management
- AI-assisted prompt refinement using GPT-4
- Semantic tagging system for better organization
- Prompt version history tracking
- Community prompt templates integration

### Advanced Generation Features
- Multi-model comparison (generate same prompt with different models)
- Style transfer between generated images
- Outpainting and inpainting capabilities
- Animation sequences from related images
- Upscaling integration for higher resolution outputs

### Improved User Experience
- Customizable workspace layouts
- Dark mode and theme support
- Keyboard shortcuts for power users
- Streamlined batch processing interface
- Progress tracking for long-running operations

### Integration Capabilities
- Export to social media platforms
- Integration with design tools (Photoshop, Figma)
- API for third-party applications
- Plugin system for community extensions

## Build Plan and Checkpoints

### Phase 1: Project Setup and Basic Structure (Days 1-2)
- [x] Create project directory structure
- [x] Set up virtual environment and install initial dependencies
- [x] Create configuration file system
- [x] Implement API key management
- [x] Set up basic logging
- **Checkpoint 1**: ✅ Verified project structure and configuration loading

### Phase 2: Core OpenAI Integration (Days 3-4)
- [x] Implement OpenAI client wrapper
- [x] Create basic image generation functionality
- [x] Add token usage tracking
- [x] Implement error handling for API calls
- [x] Add reference image upload and processing
- **Checkpoint 2**: ✅ Test image generation with sample prompts

### Phase 3: Database Implementation (Days 5-6)
- [x] Create SQLite database schema
- [x] Implement database connection and management
- [x] Create data models for prompts and generations
- [x] Set up template and batch generation tables
- **Checkpoint 3**: ✅ Verify database operations with test data

### Phase 4: GUI Implementation
- [x] Create main application window
- [x] Implement prompt input interface
- [x] Add generation controls
- [x] Create image preview area
- [x] Add reference image upload interface
- [x] Implement settings menu
- [x] Add full resolution image viewer
- [x] Implement output directory access button

**Checkpoint 4:** ✅ Verified basic GUI functionality with all components working together.

### Phase 5: File Management (Days 10-11)
- [x] Implement date-based directory structure
- [x] Create filename generation with descriptions
- [x] Add image saving functionality
- [x] Implement thumbnail generation
- **Checkpoint 5**: ✅ Verified image saving and organization

### Phase 6: Prompt History and Management (Days 12-14)
- [x] Implement prompt history view
- [x] Add search/filter functionality
- [ ] Create import/export features for prompts (JSON/CSV)
- [ ] Implement template prompt creation interface
- [ ] Add variable collection management
- [x] Add delete/clear functionality for prompts and generations
- [ ] Add prompt tagging system
- [ ] Implement prompt rating and sorting
- [ ] Add template cloning functionality
- [ ] Fix variable input validation and paste functionality
**Checkpoint 6**: Test prompt management features

### Phase 7: Advanced Features and Refinement (Days 15-17)
- [x] Implement usage statistics dashboard
- [ ] Add batch operations for prompts
- [ ] Create template system with variable substitution
- [ ] Implement rate-limited batch generation
- [ ] Add batch generation queue and progress tracking
- [x] Implement parallel processing with rate limiting
- [ ] Add support for DALL-E 3 HD
- [ ] Implement basic image editing capabilities
- [ ] Add keyboard shortcuts for common operations
- [x] Improve image display with zoom and scroll capabilities
- [x] Add button to open output folder directly
- [ ] Display real-time usage statistics during generation
- [ ] Implement model selection dropdown
**Checkpoint 7**: Verify advanced features

### Phase 8: Testing and Documentation (Days 18-20)
- [x] Write unit tests for all modules
- [x] Create integration tests
- [x] Add user documentation
- [x] Create installation guide
- [ ] Perform final bug fixes and optimizations
- **Checkpoint 8**: Complete test suite and documentation review

### Phase 9: Final Review and Release (Day 21)
- [ ] Conduct end-to-end testing
- [ ] Review code quality and performance
- [ ] Package application for distribution
- [ ] Create release notes
- **Final Checkpoint**: Application ready for use
