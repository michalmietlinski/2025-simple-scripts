const { app, BrowserWindow, protocol } = require('electron')
const path = require('path')

function createWindow() {
    const win = new BrowserWindow({
        width: 1000,
        height: 800,
        autoHideMenuBar: true,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            webSecurity: false,
            additionalArguments: ['--no-sandbox'],
            webviewTag: true
        }
    })

    // Enable loading of ES modules from node_modules
    protocol.registerFileProtocol('node-modules', (request, callback) => {
        const url = request.url.substr('node-modules://'.length)
        callback({ path: path.normalize(`${__dirname}/node_modules/${url}`) })
    })

    win.loadFile('index.html')
}

// Prevent multiple instances of the app
const gotTheLock = app.requestSingleInstanceLock()

if (!gotTheLock) {
    app.quit()
} else {
    app.on('second-instance', (event, commandLine, workingDirectory) => {
        // Someone tried to run a second instance, we should focus our window.
        if (BrowserWindow.getAllWindows().length) {
            const win = BrowserWindow.getAllWindows()[0]
            if (win.isMinimized()) win.restore()
            win.focus()
        }
    })

    app.whenReady().then(createWindow)
}

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow()
    }
})
