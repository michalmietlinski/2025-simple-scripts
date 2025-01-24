document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('saveButton').addEventListener('click', saveBookmarks);
    document.getElementById('importButton').addEventListener('click', () => {
        document.getElementById('fileInput').click();
    });
    document.getElementById('fileInput').addEventListener('change', handleFileImport);
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

async function handleFileImport(event) {
    const file = event.target.files[0];
    if (!file) return;

    try {
        const content = await file.text();
        const isJson = file.name.endsWith('.json');
        let tabGroups;

        if (isJson) {
            tabGroups = JSON.parse(content);
        } else {
            tabGroups = {};
            let currentGroup = null;
            
            const lines = content.split('\n');
            for (let line of lines) {
                line = line.trim();
                if (!line) continue;
                
                if (line.startsWith('=== ') && line.endsWith(' ===')) {
                    // Remove the === markers and spaces
                    currentGroup = line.slice(4, -4).trim();
                    if (!tabGroups[currentGroup]) {
                        tabGroups[currentGroup] = [];
                    }
                } else if (currentGroup) {
                    const url = line.trim();
                    if (url && url.startsWith('http')) {
                        tabGroups[currentGroup].push(url);
                    }
                }
            }
        }

        const currentWindow = await chrome.windows.getCurrent();

        for (const [groupName, urls] of Object.entries(tabGroups)) {
            if (!urls || urls.length === 0) continue;

            const tabPromises = urls.map(url => 
                chrome.tabs.create({
                    url: url,
                    windowId: currentWindow.id,
                    active: false
                })
            );

            const tabs = await Promise.all(tabPromises);
            if (groupName === 'Ungrouped') continue;

            const colorMatch = groupName.match(/\((.*?)\)$/);
            const color = colorMatch ? colorMatch[1] : 'grey';
            const title = groupName.replace(/\s*\(.*?\)$/, '').trim();

            if (tabs.length > 0) {
                const groupId = await chrome.tabs.group({
                    tabIds: tabs.map(tab => tab.id)
                });
                
                await chrome.tabGroups.update(groupId, {
                    title: title,
                    color: color === 'no color' ? 'grey' : color
                });
            }
        }

    } catch (error) {
        console.error('Error importing tabs:', error);
    }

    event.target.value = '';
} 
