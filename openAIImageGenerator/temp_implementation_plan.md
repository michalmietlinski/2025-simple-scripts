# Temporary Implementation Plan for New Features

## Feature Ideas to Implement

### Prompt Management
- [ ] Import/export features for prompts
  - Export to JSON/CSV formats
  - Import from external sources
  - Batch export of favorite prompts

- [ ] Batch operations for prompts
  - Batch tagging
  - Batch deletion
  - Batch rating

### Templates
- [x] Allow cloning templates
  - Added "Clone" button to template dialog
  - Implemented clone functionality in database
  - Updated UI to reflect cloned templates

- [x] Fix variables for templates
  - Added right-click context menu for paste functionality
  - Added Ctrl+V keyboard shortcut for paste
  - Added validation for missing variables
  - Added validation for unresolved variables

### History
- [x] Redesign history tab
  - [x] Move pagination controls to bottom
  - Add zoom in/out functionality for images
  - Implement image scrolling for large images

- [x] Allow removing elements from history
  - Add delete button to history items
  - Implement confirmation dialog
  - Update database to reflect deletions

### UI Improvements
- [x] Improve generation tab image display
  - Add zoom in/out controls
  - Implement scrolling for large images
  - Add image fit-to-window option
  - Add save and copy buttons

- [x] Add button to open output folder
  - Implement in main window
  - Use system file explorer

- [x] Fix usage statistics dialog
  - Fixed model distribution display
  - Corrected type mismatch between database and UI
  - Ensured proper data conversion between components

- [x] Display usage statistics next to generated image
  - Show token count
  - Show cost
  - Show model used

- [ ] Allow choosing model from available models
  - Add dropdown to select model
  - Dynamically populate based on API key capabilities
  - Save preference in settings

## Important Data to Track

### Database Tables
- `prompt_history`: For prompt import/export
- `template_variables`: For template cloning
- `generation_history`: For history redesign
- `usage_statistics`: For usage stats display

### File Paths
- Output directory: `settings_manager.get_output_dir()`
- Database path: `config_dir / "database.sqlite"`

### Key Classes
- `TemplateDialog`: For template cloning
- `HistoryTab`: For history redesign
- `GenerationTab`: For image display improvements
- `DatabaseManager`: For database operations
- `OpenAIImageClient`: For model selection

## Implementation Steps

### Step 1: Template Cloning ✅
1. ✅ Modify `TemplateDialog` to add clone button
2. ✅ Add clone method to `DatabaseManager`
3. ✅ Update UI to reflect cloned templates

### Step 2: Fix Variable Input ✅
1. ✅ Review `VariableInputDialog` logic
2. ✅ Fix paste functionality with context menu and keyboard shortcuts
3. ✅ Add validation for variable inputs

### Step 3: History Tab Redesign ✅
1. ✅ Update `HistoryTab` layout
2. ✅ Add zoom controls
3. ✅ Implement image scrolling
4. ✅ Move pagination to bottom

### Step 4: Image Display Improvements
1. Add zoom controls to `GenerationTab`
2. Implement scrolling for large images
3. Add fit-to-window option

### Step 5: Output Folder Button ✅
1. ✅ Add button to main window
2. ✅ Implement folder opening functionality

### Step 6: Model Selection
1. Update `OpenAIImageClient` to expose available models
2. Add model selection dropdown to UI
3. Save preference in settings

### Step 7: Import/Export Features
1. Implement export functionality for prompts
2. Add import functionality
3. Support batch operations

## Testing Plan
- Test each feature individually
- Ensure backward compatibility
- Verify database operations
- Check UI responsiveness

## Notes
- Remember to update project specification after implementation
- Consider adding these features to the roadmap
- Some features may require database schema updates
