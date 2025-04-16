# Pexels 精选图片插件

作者：xiamuceer-j

这是一个基于 AstrBot 框架的插件，用于从全球知名的免费图片和视频网站 Pexels.com 获取高质量的精选图片。用户可以通过发送命令快速浏览 Pexels 上的优质摄影作品。

---

## 功能

- **获取图片**: 用户可以通过命令 `/pexel` 随机获取一批来自 Pexels 的精选图片。
- **图片信息**: 返回的结果会包含每张图片的：
    - 摄影师姓名
    - 摄影师 Pexels 主页链接
    - 图片的原图链接
- **查看帮助**: 用户可以通过命令 `/pexelhelp` 查看本插件的指令说明。

---

## 最新版本

## v1.0.1
**发布日期**: 2025-04-16
**更新内容**:
- 插件初始版本发布。
- 实现 `/pexel` 命令，用于获取 Pexels 精选图片及相关信息。
- 实现 `/pexel_s <关键词>` - 根据提供的关键词在 Pexels 上搜索图片，并随机返回一张搜索结果。例如：/pexel_s cat
- 实现 `/pexelhelp` 命令，用于显示帮助信息。
- 支持通过配置文件设置 Pexels API Key 和 Base URL。
- 修改request库为aiohttp，采用异步请求