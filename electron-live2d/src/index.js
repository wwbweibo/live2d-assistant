const { app, BrowserWindow } = require('electron');
const { Worker } = require('worker_threads');
const path = require('path');
const fetch = require('node-fetch');
const logger = require('./utils/logger');

if (process.platform === 'win32') {
  process.env.LANG = 'zh_CN.UTF-8';
  process.env.LANGUAGE = 'zh_CN.UTF-8';
  process.env.LC_ALL = 'zh_CN.UTF-8';
}

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) {
  app.quit();
}

process.on('uncaughtException', (error) => {
  logger.error('主进程未捕获的异常:', error);
});

process.on('unhandledRejection', (reason) => {
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
  });

  mainWindow.webContents.on('crashed', () => {
    logger.error('窗口崩溃');
  });

  mainWindow.on('unresponsive', () => {
    logger.error('窗口无响应');
  });

  // 添加页面加载事件处理
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    logger.error('页面加载失败:', errorCode, errorDescription);
  });

  mainWindow.webContents.on('did-finish-load', () => {
    logger.info('页面加载完成');
  });

  let retryCount = 0;
  const maxRetries = 10;

  const waitForServer = async () => {
    try {
      logger.info('尝试连接服务器...');
      const response = await fetch('http://localhost:3000/health');
      const health = await response.json();
      
      if (health.status === 'OK' && health.indexExists) {
        const url = 'http://localhost:3000';
        logger.info('加载URL:', url);
        await mainWindow.loadURL(url);
        logger.info('成功连接到服务器');
      } else {
        throw new Error('健康检查失败或index.html不存在');
      }
    } catch (err) {
      retryCount++;
      logger.error('无法连接到服务器，请检查服务器是否正常启动', err.message);
      if (retryCount < maxRetries) {
        logger.warn(`等待服务器启动，重试次数: ${retryCount}`);
        setTimeout(waitForServer, 1000);
      } else {
        logger.error('无法连接到服务器，请检查服务器是否正常启动', err.message);
      }
    }
  };

  waitForServer();
}

function createBackgroundService() {
  const worker = new Worker(path.join(__dirname, 'background-service.js'));
  
  worker.on('message', (message) => {
    logger.info('收到后台服务消息:', message);
  });

  worker.on('error', (error) => {
    logger.error('后台服务错误:', error);
  });

  worker.on('exit', (code) => {
    if (code !== 0) {
      logger.error(`后台服务异常退出，退出码: ${code}`);
    }
  });

  return worker;
}

app.whenReady().then(() => {
  logger.info('应用程序启动');
  const backgroundService = createBackgroundService();
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
