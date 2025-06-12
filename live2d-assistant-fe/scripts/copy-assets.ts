import { copyFileSync, mkdirSync, cpSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

interface AssetConfig {
  source: string;
  destination: string;
  isDirectory?: boolean;
}

const assets: AssetConfig[] = [
  {
    source: 'live2dcubismcore.min.js',
    destination: 'live2dcubismcore.min.js'
  },
  {
    source: 'live2d.min.js',
    destination: 'live2d.min.js'
  },
  {
    source: 'all.min.css',
    destination: 'all.min.css'
  },
  {
    source: 'models',
    destination: 'models',
    isDirectory: true
  },
  {
    source: 'webfonts',
    destination: 'webfonts',
    isDirectory: true
  }
]

// 确保目标目录存在
mkdirSync(join(__dirname, '../dist/assets'), { recursive: true })

// 复制资源
assets.forEach((asset: AssetConfig) => {
  try {
    const sourcePath = join(__dirname, '../public/assets', asset.source)
    const destPath = join(__dirname, '../dist/assets', asset.destination)

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
console.log('Assets copied successfully!') 