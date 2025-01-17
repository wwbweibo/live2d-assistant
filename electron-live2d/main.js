const { app, BrowserWindow } = require('electron')
const { Worker } = require('worker_threads')
const path = require('path')
const logger = require(path.join(__dirname, 'src/utils/logger'))

if (process.platform === 'win32') {
  process.env.LANG = 'zh_CN.UTF-8';
}

process.on('uncaughtException', (error) => {
  logger.error('主进程未捕获的异常:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('主进程未处理的 Promise 拒绝:', reason);
});

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false
    },
    transparent: true,
    frame: false,
    alwaysOnTop: true
  })

  // 添加窗口错误处理
  mainWindow.webContents.on('crashed', () => {
    logger.error('窗口崩溃');
  });

  mainWindow.on('unresponsive', () => {
    logger.error('窗口无响应');
  });

  // 等待服务器启动
  let retryCount = 0;
  const maxRetries = 10;

  const waitForServer = async () => {
    try {
      logger.info('尝试连接服务器...');
      const response = await fetch('http://localhost:3000/health');
      if (response.ok) {
        const url = 'http://localhost:3000';
        logger.info('加载URL:', url);
        mainWindow.loadURL(url);
        logger.info('成功连接到服务器');
      }
    } catch (err) {
      retryCount++;
      if (retryCount < maxRetries) {
        logger.warn(`等待服务器启动，重试次数: ${retryCount}`);
        setTimeout(waitForServer, 1000);
      } else {
        logger.error('无法连接到服务器，请检查服务器是否正常启动', err);
      }
    }
  }

  waitForServer();
}

function createBackgroundService() {
  const worker = new Worker(path.join(__dirname, 'src/background-service.js'))
  
  worker.on('message', (message) => {
    logger.info('收到后台服务消息:', message)
  })

  worker.on('error', (error) => {
    logger.error('后台服务错误:', error)
  })

  worker.on('exit', (code) => {
    if (code !== 0) {
      logger.error(`后台服务异常退出，退出码: ${code}`)
    }
  })

  return worker
}

app.whenReady().then(() => {
  logger.info('应用程序启动')
  const backgroundService = createBackgroundService()
  createWindow()
})

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