# Nova 看板部署说明

## 1. 登录腾讯云

```bash
tcb login
```

浏览器会弹出授权页面，用你的腾讯云账号扫码登录。

---

## 2. 初始化 CloudBase 环境

```bash
cd "/Users/xuefan/Documents/文稿 - XUE的MacBook Pro/文档/小丘代运营/技术/大雪的脚本/nova_email_archive"
tcb init
```

按提示选择或创建：
- 环境 ID（如果已有则选择，没有则创建）
- 地域（建议：上海/广州）
- 支付方式（免费额度够用）

---

## 3. 启用静态网站托管

```bash
tcb hosting create
```

选择：
- 默认域名：自动生成（如：xxx.tcb.qcloud.la）
- 自定义域名：可绑定（需要备案）

---

## 4. 部署看板

```bash
tcb hosting deploy
```

选择要部署的目录：
- 本地路径：`./`（当前目录）
- 云端路径：`/`（根目录）

---

## 5. 访问看板

部署完成后会显示访问 URL，如：
```
https://xxx-xxx.tcb.qcloud.la/
```

---

## 6. 更新看板

修改 `index.html` 或数据文件后，重新部署：

```bash
tcb hosting deploy
```

---

## 备用方案：手动上传

如果遇到权限问题，可以手动操作：

1. 打开腾讯云控制台：https://console.cloud.tencent.com/tcb
2. 选择你的环境 → 静态网站托管 → 文件管理
3. 点击「上传文件」
   - `index.html`
   - `teachers.json`（后续生成）
