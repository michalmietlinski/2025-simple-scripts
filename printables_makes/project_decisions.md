# Project Decisions and Clarifications

## 1. Project Management

- [ ] Should we track failed/abandoned projects?

  > No they can just remain as added.

- [ ] Do we need to handle project versions (if original files are updated on Printables)?

  > No

- [ ] Should we track remixes or project relationships?
  > No

## 2. Print Job Management

- [ ] Do we need to track failed prints and their reasons?

  > No

- [ ] Should we support print queue management (priority, scheduling)?

  > No

- [ ] Do we need to track printer-specific settings for each job?

  > Yes, lets add that to each project as well, we can add it to our description of the project.

- [ ] Should we handle print time tracking and material usage?
  > No, multiple projects can be printed on the same print job.

## 3. Photo Management

- [ ] Do we need to store photo metadata (date taken, camera settings)?

  > No, we just want to put it in correct folder and rename it to the project name.

- [ ] Should we support photo annotations or descriptions?

  > No

- [ ] Do we need to handle photo compression/resizing?

  > No

- [ ] Should we backup photos separately?
  > No

## 4. Status Workflows

- [ ] What happens if a print job is partially successful?

  > I want to add files which were printed successfully to the print job and then mark the print job as partially successful. Other projects can remain as scheduled. i want to have a method to mark the print job as completed and then add the files which were printed successfully to the print job other project which were added to print job but not uploaded photos (failed) marked as failed.

- [ ] Can a project be marked as "Done" without photos?

  > No it is marked as done when all files are printed and photos are uploaded. if photos are uploaded then it is marked as made.

- [ ] Should we track multiple attempts at printing the same file?

  > No

- [ ] How do we handle project modifications/improvements?
  > No we download the latest file from printables once, and treat it as snapshot.

## 5. Data Management

- [ ] Do we need export/import functionality?

  > No, we can just use the index file to export data.

- [ ] Should we implement backup strategies?

  > No, we can just use the index file to backup data.

- [ ] Do we need to sync data across devices?

  > No, we can just use the index file to sync data across devices.

- [ ] How should we handle storage limitations?
  > No, we can just use the index file to handle storage limitations.

## 6. User Interface

- [ ] Do we need a way to bulk update statuses?

  > Yes, we can add a button to bulk update statuses for projects based on print job status and photos uploaded.

- [ ] Should we support batch operations for photos?

  > No

- [ ] Do we need search/filter capabilities?

  > No

- [ ] Should we support different views (list, grid, calendar)?
  > No

## 7. Integration

- [ ] Do we need API integration with Printables?

  > Check if possible to get the data from printables api.

- [ ] Should we support other 3D printing platforms?

  > To be added later.?

- [ ] Do we need printer integration?

  > No

- [ ] Should we support sharing data between users?
  > No
