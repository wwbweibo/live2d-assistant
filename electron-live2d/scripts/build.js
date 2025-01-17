const { execSync } = require('child_process')
const { cpSync, mkdirSync } = require('fs')
const path = require('path')

// 检查是否是 Windows 构建
const isWinBuild = process.argv.includes('--win')

// 构建 Vue 项目
console.log('Building Vue project...')
execSync('npm run build', { 
  cwd: path.join(__dirname, '../../'),
  stdio: 'inherit'
})

// 确保 www 目录存在
mkdirSync(path.join(__dirname, '../www'), { recursive: true })

// 复制构建文件到 www 目录
console.log('Copying build files...')
cpSync(
  path.join(__dirname, '../../dist'),
  path.join(__dirname, '../www'),
  { recursive: true }
)

// 构建 Electron 应用
console.log('Building Electron app...')
const buildCommand = isWinBuild ? 'electron-builder --win' : 'electron-builder'
execSync(buildCommand, {
  cwd: path.join(__dirname, '../'),
  stdio: 'inherit',
  env: {
    ...process.env,
    // 使用国内镜像
    ELECTRON_MIRROR: 'https://npmmirror.com/mirrors/electron/',
    ELECTRON_BUILDER_BINARIES_MIRROR: 'https://npmmirror.com/mirrors/electron-builder-binaries/'
  }
}) 