const fs = require('fs')
const path = require('path')

function isVirtualEnv(pythonExecPath) {
    const venvDir = path.dirname(path.dirname(pythonExecPath))
    try {
        return fs.existsSync(path.join(venvDir, 'pyvenv.cfg'))
    } catch {
        return false
    }
}

function resolvePythonExecPath(pythonExecPath) {
    if (process.platform !== 'win32') {
        try {
            // 仅当不是虚拟环境时解析真实路径
            if (!isVirtualEnv(pythonExecPath)) {
                pythonExecPath = fs.realpathSync.native(pythonExecPath)
            }
            return pythonExecPath
        } catch (e) {
            throw e
        }
    }
    return pythonExecPath
}

function resolvePythonVirtualEnvPath(pythonExecPath) {
    if (isVirtualEnv(pythonExecPath)) {
        return path.dirname(path.dirname(pythonExecPath))
    }
    return process.env.VIRTUAL_ENV
}

module.exports = {
    resolvePythonExecPath,
    resolvePythonVirtualEnvPath,
    isVirtualEnv
}