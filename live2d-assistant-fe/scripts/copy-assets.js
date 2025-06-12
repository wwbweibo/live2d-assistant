import { copyFileSync, mkdirSync, cpSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

const assets = [
  {
    source: 'assets',
    destination: 'assets',
    isDirectory: true
  },
  {
    source: 'webfonts',
    destination: 'webfonts',
    isDirectory: true
  }
]

// 确保目标目录存在
mkdirSync(join(__dirname, '../dist'), { recursive: true })

// 复制资源
assets.forEach(asset => {
  try {
    const sourcePath = join(__dirname, '../public', asset.source)
    const destPath = join(__dirname, '../dist', asset.destination)

    if (asset.isDirectory) {
      cpSync(sourcePath, destPath, { recursive: true })
      console.log(`Copied directory: ${asset.source}`)
    } else {
      copyFileSync(sourcePath, destPath)
      console.log(`Copied file: ${asset.source}`)
    }
  } catch (err) {
    console.error(`Failed to copy ${asset.source}:`, err)
  }
})

console.log('Assets copied successfully!') 