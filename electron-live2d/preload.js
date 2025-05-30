const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  checkFile: (filePath) => ipcRenderer.invoke('check-file', filePath),
  listDir: (dirPath) => ipcRenderer.invoke('list-dir', dirPath),
  getAppPath: () => ipcRenderer.invoke('get-app-path')
}) 