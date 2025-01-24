document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('saveButton').addEventListener('click', saveBookmarks);
    document.getElementById('importButton').addEventListener('click', () => {
        document.getElementById('fileInput').click();
    });
    document.getElementById('fileInput').addEventListener('change', handleFileImport);
});

function addStatusItem(text, isGroup = false) {
    const status = document.getElementById('status');
    const item = document.createElement('div');
    item.className = `status-item ${isGroup ? 'group' : 'url'}`;
    item.textContent = text;
    status.appendChild(item);
    status.scrollTop = status.scrollHeight;
}

function clearStatus() {
    const status = document.getElementById('status');
    status.innerHTML = '';
}

async function saveBookmarks() {
    clearStatus();
    addStatusItem('Starting export...', true);
    
    const bookmarks = {};
    const formatSelector = document.getElementById('formatSelector');
    const selectedFormat = formatSelector.value;
    
    try {
        const groups = await chrome.tabGroups.query({ windowId: chrome.windows.WINDOW_ID_CURRENT });
        const tabs = await chrome.tabs.query({ currentWindow: true });
        
        const groupedTabs = new Map();
        groups.forEach(group => {
            groupedTabs.set(group.id, {
                name: group.title || 'Unnamed Group',
                color: group.color,
                tabs: []
            });
            addStatusItem(`Found group: ${group.title || 'Unnamed Group'}`, true);
        });

        tabs.forEach(tab => {
            if (tab.groupId !== -1) {
                groupedTabs.get(tab.groupId).tabs.push(tab);
                addStatusItem(`Added: ${tab.url}`);
            } else {
                if (!bookmarks['Ungrouped']) {
                    bookmarks['Ungrouped'] = [];
                    addStatusItem('Ungrouped tabs:', true);
                }
                bookmarks['Ungrouped'].push(tab.url);
                addStatusItem(`Added: ${tab.url}`);
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

        addStatusItem('Export completed!', true);

    } catch (error) {
        console.error('Error saving tabs:', error);
        addStatusItem(`Error: ${error.message}`, true);
    }
}

async function handleFileImport(event) {
    clearStatus();
    addStatusItem('Starting import...', true);
    
    const file = event.target.files[0];
    if (!file) return;

    try {
        // Get existing groups and tabs first
        const existingGroups = await chrome.tabGroups.query({ windowId: chrome.windows.WINDOW_ID_CURRENT });
        const existingTabs = await chrome.tabs.query({ currentWindow: true });

        // Create mappings for existing items
        const existingGroupsByName = new Map();
        const existingUrlsByGroup = new Map();

        // Map existing groups
        existingGroups.forEach(group => {
            const groupName = `${group.title || 'Unnamed Group'} (${group.color})`;
            existingGroupsByName.set(groupName, group);
        });

        // Map existing tabs to their groups
        existingTabs.forEach(tab => {
            const groupId = tab.groupId;
            if (!existingUrlsByGroup.has(groupId)) {
                existingUrlsByGroup.set(groupId, new Set());
            }
            existingUrlsByGroup.get(groupId).add(tab.url);
        });

        // Parse the import file
        const content = await file.text();
        const isJson = file.name.endsWith('.json');
        let tabGroups;

        if (isJson) {
            tabGroups = JSON.parse(content);
            addStatusItem('Parsed JSON file', true);
        } else {
            tabGroups = {};
            let currentGroup = null;
            
            const lines = content.split('\n');
            for (let line of lines) {
                line = line.trim();
                if (!line) continue;
                
                if (line.startsWith('=== ') && line.endsWith(' ===')) {
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
            addStatusItem('Parsed text file', true);
        }

        const currentWindow = await chrome.windows.getCurrent();

        for (const [groupName, urls] of Object.entries(tabGroups)) {
            if (!urls || urls.length === 0) continue;

            addStatusItem(`Processing group: ${groupName}`, true);

            // Filter out URLs that already exist in the same group
            const existingGroup = existingGroupsByName.get(groupName);
            const existingUrls = existingGroup ? 
                existingUrlsByGroup.get(existingGroup.id) : new Set();
            
            const newUrls = urls.filter(url => !existingUrls?.has(url));

            if (newUrls.length === 0) {
                addStatusItem(`No new tabs to add in group: ${groupName}`, true);
                continue;
            }

            addStatusItem(`Adding ${newUrls.length} new tabs to ${groupName}`, true);
            
            const tabPromises = newUrls.map(url => 
                chrome.tabs.create({
                    url: url,
                    windowId: currentWindow.id,
                    active: false
                })
            );

            const newTabs = await Promise.all(tabPromises);
            if (groupName === 'Ungrouped') continue;

            const colorMatch = groupName.match(/\((.*?)\)$/);
            const color = colorMatch ? colorMatch[1] : 'grey';
            const title = groupName.replace(/\s*\(.*?\)$/, '').trim();

            if (newTabs.length > 0) {
                if (existingGroup) {
                    // Add new tabs to existing group
                    await chrome.tabs.group({
                        tabIds: newTabs.map(tab => tab.id),
                        groupId: existingGroup.id
                    });
                    addStatusItem(`Added tabs to existing group "${title}"`, true);
                } else {
                    // Create new group
                    const groupId = await chrome.tabs.group({
                        tabIds: newTabs.map(tab => tab.id)
                    });
                    
                    await chrome.tabGroups.update(groupId, {
                        title: title,
                        color: color === 'no color' ? 'grey' : color
                    });
                    addStatusItem(`Created new group "${title}"`, true);
                }
            }
        }

        addStatusItem('Import completed!', true);

    } catch (error) {
        console.error('Error importing tabs:', error);
        addStatusItem(`Error: ${error.message}`, true);
    }

    event.target.value = '';
} 
