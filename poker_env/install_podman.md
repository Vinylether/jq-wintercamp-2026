# Podman 安装指南

## Windows 安装方法

**系统要求：** Windows 10/11 64位（专业版、企业版或教育版）

**方法一：使用 Podman Desktop（推荐）**

**安装步骤：**
1. 启用WSL2功能（以管理员身份运行PowerShell）：
```powershell
wsl --install
```
2. 重启计算机
3. 访问 [Podman官网](https://podman-desktop.io/) 下载 Podman Desktop for Windows
4. 运行安装程序，按照提示完成安装
5. 启动 Podman Desktop，等待初始化完成
**方法二：在 WSL2 中安装 Podman
```

**验证安装：**
```bash
podman --version
podman run hello-world
```

## macOS 安装方法

**系统要求：** macOS 10.15或更新版本

**方法一：使用 Homebrew（推荐）**

**安装步骤：**
1. 确保已安装 Homebrew，如果没有安装，请先安装 Homebrew：
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
2. 使用 Homebrew 安装 Podman：
```bash
brew install podman
```
3. 初始化 Podman 机器：
```bash
podman machine init
podman machine start
```

**方法二：使用 Podman Desktop**

**安装步骤：**
1. 访问 [Podman官网](https://podman-desktop.io/) 下载 Podman Desktop for Mac
2. 双击下载的.dmg文件，将Podman图标拖拽到Applications文件夹
3. 从应用程序文件夹启动Podman Desktop，按提示完成初始设置

**验证安装：**
```bash
podman --version
podman run hello-world
``` 


## Linux 安装方法（以Ubuntu为例）

**安装步骤：**
1. 更新软件包列表：
```bash
sudo apt-get update
```
2. 安装 Podman：
```bash
sudo apt-get install -y podman
```
3. 验证安装并检查版本：
```bash
podman --version
```

**其他 Linux 发行版：**

**CentOS/RHEL/Fedora:**
```bash
sudo dnf install -y podman
# 或对于较旧版本
sudo yum install -y podman
```

**Arch Linux:**
```bash
sudo pacman -S podman
```

**Debian:**
```bash
sudo apt-get update
sudo apt-get install -y podman
```

**验证安装：**
```bash
podman --version
podman run hello-world
```

**注意：** 如果遇到权限问题，可以配置 rootless Podman 或使用 sudo 运行命令。

您只需要安装 Podman 或 Docker 其中之一，脚本会自动识别并使用正确的命令。
