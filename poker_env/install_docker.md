# Docker 安装指南

## Windows 安装方法

**系统要求：** Windows 10/11 64位（专业版、企业版或教育版）

**安装步骤：**
1. 启用WSL2功能（以管理员身份运行PowerShell）：
```powershell
wsl --install
```
2. 重启计算机
3. 访问 [Docker官网](https://www.docker.com/products/docker-desktop) 下载Docker Desktop for Windows
4. 运行安装程序，安装过程中选择"Use WSL 2 instead of Hyper-V"
5. 安装完成后重启计算机，启动Docker Desktop

**验证安装：**
```bash
docker --version
docker run hello-world
```

## Linux 安装方法（以Ubuntu为例）

**安装步骤：**
1. 使用官方一键安装脚本：
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```
2. 将当前用户加入docker组：
```bash
sudo usermod -aG docker $USER
```
3. 注销并重新登录系统

**验证安装：**
```bash
docker --version
docker run hello-world
```

## macOS 安装方法

**系统要求：** macOS 10.15或更新版本

**安装步骤：**
1. 访问 [Docker官网](https://www.docker.com/products/docker-desktop) 下载Docker Desktop for Mac
2. 双击下载的.dmg文件，将Docker图标拖拽到Applications文件夹
3. 从应用程序文件夹启动Docker，按提示完成初始设置

**验证安装：**
```bash
docker --version
docker run hello-world
```