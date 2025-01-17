const { Worker, isMainThread, parentPort } = require('worker_threads');
const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs-extra');

// 设置环境变量
if (process.platform === 'win32') {
  process.env.LANG = 'zh_CN.UTF-8';
  process.env.LANGUAGE = 'zh_CN.UTF-8';
  process.env.LC_ALL = 'zh_CN.UTF-8';
}

if (!isMainThread) {
  process.on('uncaughtException', (error) => {
    console.error('未捕获的异常:', error);
    process.exit(1);
  });

  process.on('unhandledRejection', (reason) => {
    console.error('未处理的 Promise 拒绝:', reason);
    process.exit(1);
  });

  console.log('后台服务已启动');
  
  function startServer() {
    try {
      const app = express();
      const port = 3000;

      app.use(cors());
      
      // 获取正确的 www 路径
      let wwwPath;
      if (process.resourcesPath) {
        // 打包后的环境
        wwwPath = path.join(process.resourcesPath, 'www');
      } else {
        // 开发环境
        wwwPath = path.join(process.cwd(), 'www');
      }

      // 验证路径是否存在
      if (!fs.existsSync(wwwPath)) {
        console.error('静态文件目录不存在:', wwwPath);
        throw new Error(`静态文件目录不存在: ${wwwPath}`);
      }

      // 验证 index.html 是否存在
      const indexPath = path.join(wwwPath, 'index.html');
      if (!fs.existsSync(indexPath)) {
        console.error('index.html 不存在:', indexPath);
        throw new Error(`index.html 不存在: ${indexPath}`);
      }

      console.log('静态文件路径:', wwwPath);
      
      // 设置静态文件中间件
      app.use(express.static(wwwPath));

      // 设置路由
      app.get('/', (req, res) => {
        res.sendFile(indexPath);
      });

      app.get('/health', (req, res) => {
        res.status(200).json({
          status: 'OK',
          wwwPath: wwwPath,
          indexExists: fs.existsSync(indexPath)
        });
      });

      const server = app.listen(port, () => {
        const message = {
          type: 'server-status',
          data: `服务器已启动在端口 ${port}`,
          wwwPath: wwwPath,
          indexPath: indexPath
        };
        console.log(message.data);
        parentPort.postMessage(message);
      });

      server.on('error', (error) => {
        console.error('服务器错误:', error);
        process.exit(1);
      });

      // 添加错误处理中间件
      app.use((err, req, res, next) => {
        console.error('Express 错误:', err);
        res.status(500).send('服务器错误');
      });

    } catch (error) {
      console.error('启动服务器时出错:', error);
      process.exit(1);
    }
  }

  startServer();

  function runBackgroundTask() {
    setInterval(() => {
      const message = {
        type: 'status',
        data: '后台服务正在运行'
      };
      console.log(message.data);
      parentPort.postMessage(message);
    }, 5000);
  }

  runBackgroundTask();
} 