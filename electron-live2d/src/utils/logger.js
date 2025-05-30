const fs = require('fs-extra');
const path = require('path');
const { isMainThread } = require('worker_threads');

class Logger {
  constructor() {
    // 获取应用数据目录
    let userDataPath;
    userDataPath = process.cwd();
    this.logDir = path.join(userDataPath, 'logs');
    this.logFile = path.join(this.logDir, `app-${new Date().toISOString().split('T')[0]}.log`);
    
    try {
      // 确保日志目录存在
      fs.ensureDirSync(this.logDir);
      // 写入 UTF-8 BOM
      // if (!fs.existsSync(this.logFile)) {
      //   fs.writeFileSync(this.logFile, '\ufeff', { encoding: 'utf8' });
      // }
    } catch (error) {
      console.error('无法创建日志目录:', error);
    }
  }

  _writeLog(level, message, ...args) {
    try {
      const timestamp = new Date().toISOString();
      let logMessage = `[${timestamp}] [${level}] ${message}`;
      
      if (args.length > 0) {
        const argsStr = args.map(arg => {
          if (typeof arg === 'object') {
            return JSON.stringify(arg);
          }
          return arg;
        }).join(' ');
        logMessage += ' ' + argsStr;
      }

      // 写入日志文件，使用 UTF-8 编码
      fs.appendFileSync(this.logFile, logMessage + '\n', { encoding: 'utf8' });
      process.stdout.write(logMessage + '\n');
    } catch (error) {
      console.error('Logger error:', error);
    }
  }

  info(message, ...args) {
    this._writeLog('INFO', message, ...args);
  }

  error(message, ...args) {
    this._writeLog('ERROR', message, ...args);
  }

  warn(message, ...args) {
    this._writeLog('WARN', message, ...args);
  }

  debug(message, ...args) {
    this._writeLog('DEBUG', message, ...args);
  }
}

// 设置 Windows 控制台编码为 UTF-8
if (process.platform === 'win32') {
  // 设置 Windows 控制台代码页为 UTF-8
  try {
    const cp = require('child_process');
    cp.execSync('chcp 65001', { stdio: ['ignore', 'ignore', 'ignore'] });
  } catch (error) {
    console.error('设置控制台编码失败:', error);
  }
}

let instance = null;
module.exports = (() => {
  if (!instance) {
    instance = new Logger();
  }
  return instance;
})(); 