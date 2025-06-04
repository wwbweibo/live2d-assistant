const fs = require('fs')
const path = require('path')
const logger = require('./utils/logger')

class Config {
  constructor() {
    this.configPath = path.join(__dirname, '../dist/config.json')
    this.config = this.loadConfig()
  }

  loadConfig() {
    try {
      if (fs.existsSync(this.configPath)) {
        const fs_content = fs.readFileSync(this.configPath, 'utf8')
        logger.info('加载配置文件成功:', fs_content)
        return JSON.parse(fs_content)
      } else {
        logger.error('配置文件不存在:', this.configPath) 
      }
    } catch (error) {
      logger.error('加载配置文件失败:', error)
      return null
    }
  }

  getConfig() {
    return this.config
  }
}

module.exports = new Config() 