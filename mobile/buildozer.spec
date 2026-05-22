[app]

# 应用基本信息
title = FATE ENDS 算力分配
package.name = trc20power
package.domain = com.fateends
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0
requirements = python3,kivy

# 权限（网络访问必需）
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE

# 应用方向
orientation = portrait

# 图标
icon.filename = icon.png

# 启动画面
presplash.filename = presplash.png

# 全屏
fullscreen = 0

# Python 版本
osx.python_version = 3

# Android 最低 API
android.minapi = 21
android.api = 33
android.ndk = 25b

# Kivy 版本
p4a.branch = master

# 日志级别
log_level = 2

# 允许的架构（仅64位，减少一半编译时间）
android.arch = arm64-v8a

# 清理旧构建
android.allow_backup = True

[buildozer]

log_level = 2
warn_on_root = 1
