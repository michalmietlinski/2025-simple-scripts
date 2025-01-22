document.getElementById('saveTabsBtn').addEventListener('click', async () => {
  try {
    // Get all tab groups in the current window
    const groups = await chrome.tabGroups.query({ windowId: chrome.windows.WINDOW_ID_CURRENT });
    // Get all tabs in the current window
    const tabs = await chrome.tabs.query({ currentWindow: true });
    
    let content = '';
    
    // Create a map of grouped tabs
    const groupedTabs = new Map();
    groups.forEach(group => {
      groupedTabs.set(group.id, {
        name: group.title || 'Unnamed Group',
        color: group.color,
        tabs: []
      });
    });
    
    // Sort tabs into groups or ungrouped
    tabs.forEach(tab => {
      if (tab.groupId !== -1) {
        groupedTabs.get(tab.groupId).tabs.push(tab);
      } else {
        if (!groupedTabs.has('ungrouped')) {
          groupedTabs.set('ungrouped', {
            name: 'Ungrouped Tabs',
            tabs: []
          });
        }
        groupedTabs.get('ungrouped').tabs.push(tab);
      }
    });
    
    // Format the content with groups
    for (const [_, group] of groupedTabs) {
      if (group.tabs.length > 0) {
        content += `=== ${group.name} ${group.color ? `(${group.color})` : ''} ===\n\n`;
        content += group.tabs.map(tab => 
          `${tab.title}\n${tab.url}\n`
        ).join('\n');
        content += '\n\n';
      }
    }
    
    // Create a Blob with the content
    const blob = new Blob([content], { type: 'text/plain' });
    
    // Generate timestamp for the filename
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    // Download the file
    chrome.downloads.download({
      url: URL.createObjectURL(blob),
      filename: `tabs-${timestamp}.txt`,
      saveAs: true
    });
  } catch (error) {
    console.error('Error saving tabs:', error);
  }
}); 
