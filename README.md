# LLM 使用量查询工具

一个 Streamlit 应用，用于查询多个大模型平台的使用量/余额。

## 支持的平台

| 平台 | 查询内容 |
|------|----------|
| 移动云 | Coding Plan 使用量（日/周/月） |
| 百度千帆 | Coding Plan 使用量/余额 |

## 功能特点

- 统一界面查询多个平台
- 支持日/周/月使用量统计
- 本地保存配置，无需重复登录

## 安装

```bash
pip install requests streamlit
```

## 配置

1. 复制配置模板：
```bash
cp config.example.json config.json
```

2. 编辑 `config.json`，填入你的凭证：

```json
{
  "ecloud_token": "你的移动云CMECLOUDTOKEN",
  "qianfan_cookie": "你的百度千帆Cookie"
}
```

### 如何获取凭证

**移动云 Token**：
1. 登录 [移动云控制台](https://ecloud.10086.cn/)
2. 打开浏览器开发者工具 (F12)
3. 在 Network 标签页找到任意请求
4. 复制请求头中的 `CMECLOUDTOKEN` 值

**百度千帆 Cookie**：
1. 登录 [百度智能云](https://console.bce.baidu.com/qianfan/)
2. 打开浏览器开发者工具 (F12)
3. 在 Network 标签页找到任意请求
4. 复制请求头中的完整 `Cookie` 值

## 使用

### Streamlit Web 界面

```bash
streamlit run app.py
```

### 命令行（移动云）

```bash
python ecloud_usage.py
```

## 安全提示

- `config.json` 包含敏感凭证，已加入 `.gitignore`
- 不要将 `config.json` 提交到公开仓库
- Token 和 Cookie 可能会过期，需要定期更新

## 许可证

MIT
