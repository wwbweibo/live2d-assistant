const fs = require('fs-extra');
const path = require('path');

async function copyWwwFiles() {
  try {
    const srcDir = path.join(__dirname, '../src/www');
    const destDir = path.join(__dirname, '../www');

    // 确保目标目录存在
    await fs.ensureDir(destDir);

    // 复制文件
    await fs.copy(srcDir, destDir, {
      overwrite: true,
      errorOnExist: false
    });

    console.log('静态文件复制完成');
  } catch (err) {
    console.error('复制文件时出错:', err);
    process.exit(1);
  }
}

copyWwwFiles(); 