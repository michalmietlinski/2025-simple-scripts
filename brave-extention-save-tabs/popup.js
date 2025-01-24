document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('saveButton').addEventListener('click', saveBookmarks);
});

async function saveBookmarks() {
    const bookmarks = {};
    const formatSelector = document.getElementById('formatSelector');
    const selectedFormat = formatSelector.value;
    
    try {
        // Get all tab groups and tabs in the current window
        const groups = await chrome.tabGroups.query({ windowId: chrome.windows.WINDOW_ID_CURRENT });
        const tabs = await chrome.tabs.query({ currentWindow: true });
        
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
                if (!bookmarks['Ungrouped']) {
                    bookmarks['Ungrouped'] = [];
                }
                bookmarks['Ungrouped'].push(tab.url);
            }
        });

        // Convert groupedTabs to bookmarks format
        groupedTabs.forEach(group => {
            if (group.tabs.length > 0) {
                const groupName = `${group.name} (${group.color || 'no color'})`;
                bookmarks[groupName] = group.tabs.map(tab => tab.url);
            }
        });

        // Create content based on selected format
        let content;
        let filename;
        
        if (selectedFormat === 'json') {
            content = JSON.stringify(bookmarks, null, 2);
            filename = 'tabs.json';
        } else {
            // Text format
            content = Object.entries(bookmarks)
                .map(([groupName, urls]) => {
                    return `=== ${groupName} ===\n${urls.map(url => `  ${url}`).join('\n')}`;
                })
                .join('\n\n');
            filename = 'tabs.txt';
        }

        // Create and trigger download
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Error saving tabs:', error);
    }
} 
