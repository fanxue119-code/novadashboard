#!/bin/bash
# Nova 邮件同步定时任务安装脚本

echo "正在安装 Nova 邮件同步定时任务..."

# 加载 launchd 任务
launchctl load ~/Library/LaunchAgents/nova.email.sync.plist

# 检查状态
if launchctl list | grep -q "nova.email.sync"; then
    echo "✅ 安装成功！"
    echo ""
    echo "定时任务信息："
    echo "  - 运行时间：每天 09:00"
    echo "  - 日志位置：/tmp/nova_email_sync.log"
    echo "  - 错误日志：/tmp/nova_email_sync.err"
    echo ""
    echo "手动触发测试："
    echo "  launchctl start nova.email.sync"
    echo ""
    echo "停止定时任务："
    echo "  launchctl unload ~/Library/LaunchAgents/nova.email.sync.plist"
else
    echo "❌ 安装失败，请检查权限"
fi
