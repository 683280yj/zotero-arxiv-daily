# GitHub Actions 部署指南

本文档面向“每天给 `yggcmm@outlook.com` 发送中文 Zotero 论文推荐邮件”的 MVP 场景，默认使用：

- `RECEIVER=yggcmm@outlook.com`
- `LANGUAGE=Chinese`
- `ARXIV_QUERY=cs.AI+cs.CV+cs.LG+cs.CL`

## 1. 准备发件服务

本项目默认使用通用 SMTP/邮件服务作为发件端，不把 Outlook.com 作为默认发件依赖。

建议使用支持 SMTP 的邮箱或事务邮件服务，例如：

- 企业邮箱 SMTP
- Gmail App Password
- QQ 邮箱授权码
- Resend、Mailgun、SendGrid 等 SMTP 中继

注意：`yggcmm@outlook.com` 在本方案中只作为收件邮箱。若你考虑让 Outlook.com 负责发信，需要自行确认该服务端的现代认证方案；Outlook.com 已于 **2024-09-16** 停用 Basic Auth，不应继续按“账号密码直连 SMTP”的旧教程配置。

## 2. Fork 仓库并配置 Secrets / Variables

在 GitHub 仓库的 `Settings -> Secrets and variables -> Actions` 中配置以下内容。

### 必填 Secrets

| 名称 | 说明 | 示例 |
| --- | --- | --- |
| `ZOTERO_KEY` | Zotero 只读 API Key。程序可在运行时通过 `GET https://api.zotero.org/keys/current` 自动解析 `userID`，因此 `ZOTERO_ID` 可留空。 | `ABCD...` |
| `ARXIV_QUERY` | arXiv 分类查询。 | `cs.AI+cs.CV+cs.LG+cs.CL` |
| `SMTP_SERVER` | 发件 SMTP 主机。 | `smtp.resend.com` |
| `SMTP_PORT` | 发件 SMTP 端口。 | `587` |
| `SENDER` | 发件邮箱。 | `bot@example.com` |
| `SENDER_PASSWORD` | SMTP 密码或授权码。 | `xxxxxxxx` |

### 可选 Secrets

| 名称 | 说明 | 默认 |
| --- | --- | --- |
| `ZOTERO_ID` | 若已知可直接填写；不填时运行时自动解析。 | 自动解析 |
| `RECEIVER` | 收件邮箱。 | `yggcmm@outlook.com` |
| `MAX_PAPER_NUM` | 单次邮件最多推荐论文数。 | `5` |
| `USE_LLM_API` | 是否使用 OpenAI 兼容 API 生成 TLDR。 | `true` |
| `OPENAI_API_KEY` | LLM API Key。`USE_LLM_API=true` 时需要。 | 空 |
| `OPENAI_API_BASE` | LLM API Base URL。 | `https://api.openai.com/v1` |
| `MODEL_NAME` | LLM 模型名。 | `gpt-4o` |

### 可选 Variables

| 名称 | 说明 | 默认 |
| --- | --- | --- |
| `ZOTERO_IGNORE` | 用 gitignore 风格忽略不参与建模的文献集合。 | 空 |
| `REPOSITORY` | 保持为空，或设置为上游仓库名。 | 空 |
| `REF` | 指定运行分支/标签。 | 空 |
| `LANGUAGE` | TLDR 语言。 | `Chinese` |
| `SEND_EMPTY` | 无新论文时是否仍发空邮件。 | `false` |

## 3. 触发与验证

1. 打开 `Actions` 页面。
2. 手动运行 `Test workflow` 验证配置。
3. 成功后保留 `Send emails daily` 的定时任务即可。

## 4. 日志排查

如果任务失败，优先检查：

- `ZOTERO_KEY` 是否可读取文库
- SMTP 服务是否支持你填写的端口与认证方式
- `OPENAI_API_KEY` 是否存在且模型名有效
- GitHub Actions 日志中是否出现 `missing required configuration` 或 `failed to resolve Zotero user ID`

## 5. 推荐最小配置

若只想尽快跑通 MVP，可以只配置下面这些：

```text
ZOTERO_KEY
ARXIV_QUERY
SMTP_SERVER
SMTP_PORT
SENDER
SENDER_PASSWORD
```

其余项将自动采用默认值，其中收件邮箱默认为 `yggcmm@outlook.com`，输出语言默认为中文。
