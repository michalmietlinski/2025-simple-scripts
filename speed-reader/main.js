const { app, BrowserWindow, protocol } = require('electron')
const path = require('path')

function createWindow() {
    const win = new BrowserWindow({
        width: 1000,
        height: 800,
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

app.whenReady().then(() => {
    createWindow()

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow()
        }
    })
})

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})
