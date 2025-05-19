const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fetch = require('node-fetch');
const logger = require('./utils/logger');
const screen = require('electron').screen;
const fs = require('fs');
const config = require('./config');
const { dialog } = require('electron');
const { resolvePythonExecPath, resolvePythonVirtualEnvPath, isVirtualEnv } = require('./utils/file-system');

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
  logger.error('主进程未捕获的异常:', error.message);
  app.quit();
});

process.on('unhandledRejection', (reason) => {
  logger.error('主进程未处理的 Promise 拒绝:', reason.message);
  app.quit();
});

let backgroundService = null
// 在创建窗口前加载配置
const appConfig = config.getConfig();
if (!appConfig) {
  console.error('配置加载失败，使用默认配置');
}

function createWindow(config) {
  const mainWindow = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false
    },
    // transparent: true,
    // alwaysOnTop: true,
    // frame: true,
  });
  mainWindow.loadURL(`http://${config.server.host}:${config.server.port}/`);
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
}

function createBackgroundService(config, configPath) {
  const pythonExecPath = resolvePythonExecPath(config.server.pythonExec)
  const execCommand = [
    config.server.serverPath,
    "--config", configPath
  ]
  const cmd = execCommand.join(" ")
  logger.info('cmd:', pythonExecPath, cmd)
  var subprocess = null
  if (isVirtualEnv(pythonExecPath)) {
    subprocess = require('child_process').spawn(pythonExecPath, execCommand, {
      env: {
        VIRTUAL_ENV: resolvePythonVirtualEnvPath(pythonExecPath)
      }
    })
  } else {
    subprocess = require('child_process').spawn(pythonExecPath, execCommand)
  }
  subprocess.stdout.on('data', (data) => {
    logger.info(data.toString());
  });
  subprocess.stderr.on('data', (data) => {
    logger.error(data.toString());
  });
  subprocess.on('error', (error) => {
    logger.error('后台服务错误:', error.message);
  });
  subprocess.on('exit', (code) => {
    if (code !== 0) {
      logger.error(`后台服务异常退出，退出码: ${code}`);
      throw new Error(`后台服务异常退出，退出码: ${code}`);
    }
  });
  return subprocess;
}

async function waitForServer(config, retryCount = 0) {
  const maxRetries = 10;
  try {
    logger.info('尝试连接服务器...');
    const response = await fetch(`http://${config.server.host}:${config.server.port}/health`);
    const health = await response.json();
    logger.info('health:', health)
    logger.info('health.status === OK:', health.status === 'OK')
    logger.info('health.indexExists === true:', health.indexExists)
    if (health.status === 'OK' && health.indexExists) {
      logger.info('成功连接到服务器');
      createWindow(config);
      return true;
    } else {
      throw new Error('健康检查失败或index.html不存在');
    }
  } catch (err) {
    retryCount++;
    logger.error('连接服务器失败', err.message);
    if (retryCount < maxRetries) {
      logger.warn(`等待服务器启动，重试次数: ${retryCount}`);
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve(waitForServer(config, retryCount));
        }, 1000);
      });
    } else {
      logger.error('无法连接到服务器，请检查服务器是否正常启动', err.message);
      // 抛出异常，交由主进程处理
      throw new Error('无法连接到服务器，请检查服务器是否正常启动');
    }
  }
}

app.whenReady().then(async () => {
  try {
    logger.info('应用程序启动');
    backgroundService = createBackgroundService(appConfig, config.configPath);
    // 等待服务器启动
    await waitForServer(appConfig);
    // 监听后台服务的错误
    backgroundService.on('error', (error) => {
      logger.error('后台服务错误:', error.message);
      dialog.showErrorBox('后台服务错误', error.message);
      app.quit();
    });

  } catch (error) {
    logger.error('应用程序启动失败:', error.message);
    logger.error(error.stack);
    dialog.showErrorBox('应用程序启动失败', error.message);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
  backgroundService.kill();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
