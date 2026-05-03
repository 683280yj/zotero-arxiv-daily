# Docker 部署指南

本文档面向“每天给 `yggcmm@outlook.com` 发送中文 Zotero 论文推荐邮件”的 MVP 场景。

## 1. 准备环境文件

复制 `.env.example` 为 `.env`，至少填写以下参数：

```dotenv
ZOTERO_KEY=replace-with-your-zotero-api-key
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SENDER=sender@example.com
SENDER_PASSWORD=replace-with-your-smtp-password
```

说明：

- `ZOTERO_ID` 可以留空，容器会在启动时通过 `GET https://api.zotero.org/keys/current` 自动解析。
- `RECEIVER` 默认是 `yggcmm@outlook.com`。
- `LANGUAGE` 默认是 `Chinese`。
- 推荐优先使用通用 SMTP 或邮件服务作为发件端，不默认依赖 Outlook.com 发信。
- 若你自行选用 Outlook.com 作为发件服务，需要确认现代认证支持；Outlook.com 已于 **2024-09-16** 停用 Basic Auth。

## 2. 启动

```bash
docker compose up -d --build
```

容器会：

- 读取 `.env`
- 将当前环境导入 `/etc/environment` 供 cron 任务使用
- 按宿主机时区注册默认 `0 8 * * *` 的每日任务
- 通过前台 `cron -f` 保持容器存活

## 3. 查看日志

本项目已把 cron 任务日志直接输出到容器标准输出，查看方式：

```bash
docker compose logs -f zotero-arxiv-daily
```

这比把 `cron` 放到后台再 `tail` 文件更稳定，也避免了原先日志文件名拼写不一致的问题。

## 4. 修改执行时间

如需调整执行时间，修改 `docker-compose.yml` 中的 `CRON_SCHEDULE` 环境变量，例如：

```yaml
CRON_SCHEDULE: "0 22 * * *"
```

上例表示每天 `22:00 UTC` 执行。

## 5. 常见故障

### 容器启动后立刻退出

检查 `docker-compose.yml` 是否仍使用旧的 `cron -f && tail -f ...` 写法。新的配置只保留一个前台进程：`cron -f`。

### Zotero 用户 ID 解析失败

检查：

- `ZOTERO_KEY` 是否有效
- 容器是否能访问 `https://api.zotero.org/keys/current`

### 没有收到邮件

优先检查：

- SMTP 主机、端口、授权码是否正确
- 发件服务是否要求 SSL/TLS 特殊配置
- 收件箱垃圾邮件目录
