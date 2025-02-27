# DALL-E Image Generator - Delete Functionality

This document provides detailed information about the delete functionality implemented in the DALL-E Image Generator application.

## Overview

The delete functionality allows users to:
- Delete individual prompts from the prompt history
- Delete individual generations from the generation history
- Clear all prompts from the database
- Clear all generations from the database

## User Interface

### Prompt History

In the prompt history tab, users can:
- Select a prompt and click the "Delete" button to remove it from the database
- Click the "Clear All" button to remove all prompts from the database

Both actions require confirmation via a dialog box to prevent accidental deletion.

### Generation History

In the generation history tab, users can:
- Select a generation and click the "Delete" button to remove it from the database
- Click the "Clear All" button to remove all generations from the database

Both actions require confirmation via a dialog box to prevent accidental deletion.

## Implementation Details

### Database Operations

The delete functionality is implemented in the `DatabaseManager` class:

- `delete_prompt(prompt_id)`: Deletes a prompt from the database
- `delete_generation(generation_id)`: Deletes a generation from the database and removes the associated image file
- `clear_all_prompts()`: Deletes all prompts from the database
- `clear_all_generations()`: Deletes all generations from the database and removes all associated image files

### Application Logic

The delete functionality is implemented in the `DALLEGeneratorApp` class:

- `delete_selected_prompt()`: Deletes the currently selected prompt after confirmation
- `clear_all_prompts()`: Clears all prompts after confirmation
- `delete_selected_generation()`: Deletes the currently selected generation after confirmation
- `clear_all_generations()`: Clears all generations after confirmation

After each delete operation, the UI is refreshed to reflect the changes.

## Testing

The delete functionality is tested in:

- `test_image_display.py`: Tests the UI components and application logic
- `test_database.py`: Tests the database operations

## Usage

To use the delete functionality:

1. **Delete a prompt**:
   - Navigate to the Prompt History tab
   - Select a prompt from the list
   - Click the "Delete" button
   - Confirm the deletion when prompted

2. **Clear all prompts**:
   - Navigate to the Prompt History tab
   - Click the "Clear All" button
   - Confirm the deletion when prompted

3. **Delete a generation**:
   - Navigate to the Generation History tab
   - Select a generation from the list
   - Click the "Delete" button
   - Confirm the deletion when prompted

4. **Clear all generations**:
   - Navigate to the Generation History tab
   - Click the "Clear All" button
   - Confirm the deletion when prompted

## Notes

- Deleting a prompt will permanently remove it from the database
- Deleting a generation will remove both the database entry and the associated image file
- All delete operations require confirmation to prevent accidental data loss
- The UI is automatically refreshed after each delete operation to reflect the changes 
