# FATE ENDS 算力分配 APK 打包

## 一键打包（GitHub Actions，免费、不断线）

### 操作步骤

**第 1 步**：把整个文件夹上传到 GitHub 新仓库

1. 打开 https://github.com/new 创建一个**公开仓库**（免费）
2. 下载 [GitHub Desktop](https://desktop.github.com/) 或使用命令行
3. 把这个文件夹的所有内容推送到仓库

**第 2 步**：等待自动构建

- 推送后 GitHub Actions 会**自动开始构建**，不需要任何操作
- 也可以在仓库页面点 **Actions** → **Build APK** → **Run workflow** 手动触发

**第 3 步**：下载 APK（约 15 分钟后）

- 进入仓库 → **Actions** → 点击最新的构建记录
- 在 **Artifacts** 区域点击 **TRC20-算力分配** 下载

---

## 文件说明

```
├── .github/workflows/build.yml   # GitHub Actions 自动构建配置
├── mobile/
│   ├── main.py                   # 应用源码（Kivy）
│   ├── buildozer.spec            # 打包配置
│   ├── icon.png                  # 图标
│   └── presplash.png             # 启动闪屏
```
