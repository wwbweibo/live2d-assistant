const fs = require('fs-extra');
const path = require('path');

async function copyServer() {
    // 将 server 目录复制到 dist 目录下
    const srcDir = path.join(__dirname, '../../server');
    const destDir = path.join(__dirname, '../dist/server');
    if (fs.existsSync(destDir)) {
        fs.removeSync(destDir);
    }
    await fs.ensureDir(destDir);
    await fs.copy(srcDir, destDir, {
        overwrite: true,
        errorOnExist: false
    });
    console.log('server 目录复制完成');
}

async function copyVenv() {
    // 将 venv 目录复制到 dist 目录下
    const srcDir = path.join(__dirname, '../../venv');
    const destDir = path.join(__dirname, '../dist/venv');
    if (fs.existsSync(destDir)) {
        fs.removeSync(destDir);
    }
    await fs.ensureDir(destDir);
    await fs.copy(srcDir, destDir, {
        overwrite: true,
        errorOnExist: false
    });
    // python python3 python3.12 是软连接，需要从软连接找到真实文件
    try {
        const realPythonPath = fs.realpathSync(path.join(srcDir, 'bin/python'));
        const realPython3Path = fs.realpathSync(path.join(srcDir, 'bin/python3'));
        const realPython312Path = fs.realpathSync(path.join(srcDir, 'bin/python3.12'));
        fs.copySync(realPythonPath, path.join(destDir, 'bin/python'));
        fs.copySync(realPython3Path, path.join(destDir, 'bin/python3'));
        fs.copySync(realPython312Path, path.join(destDir, 'bin/python3.12'));
    } catch (error) {
        console.error('错误:', error);
    }
    console.log('venv 目录复制完成');
}

async function copyWwwFiles() {
    const srcDir = path.join(__dirname, '../../dist');
    const destDir = path.join(__dirname, '../dist/www');
    if (fs.existsSync(destDir)) {
        fs.removeSync(destDir);
    }
    await fs.ensureDir(destDir);
    await fs.copy(srcDir, destDir, {
        overwrite: true,
        errorOnExist: false
    });
    console.log('www 目录复制完成');
}

async function generateConfig() {
    // 生成 config.json 文件
    const config = {
        "debug": true,
        "server": {
            "pythonExec": "../dist/venv/bin/python",
            "serverPath": "../dist/server/server.py",
            "port": 3000,
            "host": "0.0.0.0",
            "staticPath": "../dist/www",
            "tts": {
                "enabled": false,
                "modulePath": "./dist/py_script/asset/zero_shot_prompt.wav",
                "promptPath": "./dist/www/jinxi.wav",
                "promptText": "欢迎来到今州，远道而来的贵客，事务繁忙，招待不周之处还请见谅。若是有什么要紧事，可以来边庭找我。",
                "sampleRate": 16000,
                "cosyvoiceInstallPath": "./dist/venv/Lib/site-packages/cosyvoice"
            },
            "llm": {
                "provider": "ollama",
                "api_key": "ollama",
                "base_url": "http://localhost:11434/v1",
                "sys_prompt": "你是一个AI助手，请根据用户的问题给出回答。"
            },
            "mcp_servers": [
                {
                    "name": "music-player",
                    "transport": "sse",
                    "url": "http://127.0.0.1:8000/sse"
                }
            ]
        }
    }
    await fs.writeFile(path.join(__dirname, '../dist/config.json'), JSON.stringify(config, null, 2));
    console.log('config.json 文件生成完成');
}

copyServer();
copyVenv();
copyWwwFiles();
generateConfig();