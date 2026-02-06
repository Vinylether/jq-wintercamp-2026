# Poker Bot 环境检测工具

## 项目简介

本项目目的是为检测poker bot需要的环境是否安装成功，用于在 **Windows**、**Linux**、**macOS** 操作系统上检测：

1. **容器运行时检测**：自动检测系统是否安装了 Docker 或 Podman
2. **运行环境验证**：验证容器运行时是否能正常运行所需要的程序
3. **错误日志输出**：当检测失败时，提供详细的错误日志信息
4. **成功标识**：当检测成功时，显示明确的成功标识

## 前置要求

在开始之前，请确保已安装容器运行时。本工具支持 Docker 或 Podman，可以任意选择一个安装。

- [Docker 安装指南](install_docker.md)
- [Podman 安装指南](install_podman.md)


## 快速开始

### 步骤 1: 安装容器运行时

请根据您的操作系统选择合适的容器运行时并安装，本工具支持 Docker 或 Podman，可以任意选择一个安装。

- [Docker 安装指南](install_docker.md) 
- [Podman 安装指南](install_podman.md)  


**验证安装：**

如果安装了 Docker：
```bash
docker --version
docker run hello-world
```

如果安装了 Podman：
```bash
podman --version
podman run hello-world
```


**注意：** 本框架的脚本会自动检测系统中安装的是 Podman 还是 Docker，无需手动配置。

### 步骤 2: 加载容器镜像

根据您的操作系统运行相应的脚本：

- **Linux/macOS:** 
  ```bash
  ./setup.sh
  ```

- **Windows (PowerShell):**
  1. **打开 PowerShell**：
     - 按 `Win + X`，然后选择 "Windows PowerShell" 或 "终端"
     - 或者在开始菜单搜索 "PowerShell" 并打开
     - 或者在文件资源管理器中，按住 `Shift` 键并右键点击项目文件夹，选择 "在此处打开 PowerShell 窗口"
  
  2. **设置执行策略**（首次运行可能需要）：
     ```powershell
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
     ```
     如果系统提示，输入 `Y` 确认。
  
  3. **运行脚本**：
     ```powershell
     .\setup.ps1
     ```

此步骤会加载 `pokerengine.tar` 镜像文件到本地容器环境。

**自动检测：** 脚本会自动检测并使用系统中安装的容器运行时（Podman 或 Docker），无需手动配置。运行时会显示检测到的容器运行时。

**检测结果：**
- ✅ **成功标识**：如果检测到 Docker 或 Podman，会显示 "Detected Docker" 或 "Detected Podman"（绿色）
- ❌ **错误日志**：如果未检测到任何容器运行时，会显示错误信息并退出，提示用户安装 Docker 或 Podman

### 步骤 3: 运行测试

运行测试脚本，脚本会自动运行 5 轮测试来验证 Fish Player 是否能正常运行：

- **Linux/macOS:**
  ```bash
  ./run.sh
  ```

- **Windows (PowerShell):**
  1. **打开 PowerShell**（如果还没有打开）：
     - 按 `Win + X`，然后选择 "Windows PowerShell" 或 "终端"
     - 或者在开始菜单搜索 "PowerShell" 并打开
     - 或者在文件资源管理器中，按住 `Shift` 键并右键点击项目文件夹，选择 "在此处打开 PowerShell 窗口"
  
  2. **运行脚本**：
     ```powershell
     .\run.ps1
     ```
 

**检测和运行结果：**

脚本运行后会显示以下结果：

- ✅ **成功标识**：
  - 检测到容器运行时：显示 "✅ Detected Docker" 或 "✅ Detected Podman"
  - 所有轮次完成：显示 "✅ SUCCESS:"

- ❌ **错误日志**：
  - 未检测到容器运行时：显示 "❌ Error: Neither Docker nor Podman is installed or not in PATH"，并提示查看安装指南
  - 测试失败：显示 "❌ FAILED: X out of 5 rounds failed."，并提示查看日志文件获取详细错误信息  

## 故障排除

如果遇到问题，请检查：

1. **容器运行时是否正确安装并运行**
   - Podman：`podman --version` 和 `podman ps`
   - Docker：`docker --version` 和 `docker ps`
   - 如果命令失败，说明容器运行时未正确安装或未添加到 PATH

2. **镜像是否成功加载**
   - Podman：`podman images` 查看镜像列表，应该能看到 `pokerengine` 镜像
   - Docker：`docker images` 查看镜像列表，应该能看到 `pokerengine` 镜像
   - 如果镜像不存在，运行 `setup.sh`（Linux/macOS）或 `setup.ps1`（Windows）加载镜像

3. **脚本是否能检测到容器运行时**
   - 如果脚本提示找不到 Docker 或 Podman，请确保它们已正确安装并在 PATH 中 

## 相关文档

- [Podman 安装指南](install_podman.md)  
- [Docker 安装指南](install_docker.md) 