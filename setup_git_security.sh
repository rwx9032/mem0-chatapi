#!/bin/bash

# Git安全配置脚本
# 该脚本会为项目设置必要的安全配置

echo "🔧 配置Git安全设置..."

# 1. 设置Git全局配置（推荐）
echo "📝 设置Git全局安全配置..."

# 防止意外提交大文件
git config --global core.bigFileThreshold 10m

# 设置默认的 .gitignore 全局文件
if [ ! -f ~/.gitignore_global ]; then
    echo "📄 创建全局 .gitignore 文件..."
    cat > ~/.gitignore_global << 'EOF'
# 全局忽略的敏感文件
.env
.env.local
.env.*.local
*.key
*.pem
*.p12
*secret*
*password*
*token*
.DS_Store
Thumbs.db
EOF
    git config --global core.excludesfile ~/.gitignore_global
    echo "✅ 全局 .gitignore 文件已创建"
fi

# 2. 为当前项目设置安全hook
echo "🔗 设置项目安全hooks..."

# 确保hooks目录存在
mkdir -p .git/hooks

# 设置pre-commit hook权限
if [ -f ".git/hooks/pre-commit" ]; then
    chmod +x .git/hooks/pre-commit
    echo "✅ Pre-commit hook 已启用"
else
    echo "⚠️  Pre-commit hook 文件不存在"
fi

# 3. 设置安全的Git别名
echo "⚙️  设置有用的Git别名..."

git config --global alias.check-secrets '!bash -c "find . -type f -name \"*.py\" -o -name \"*.js\" -o -name \"*.json\" | xargs grep -l -E \"(AIza|sk-|gsk_|AKIA)\""'
git config --global alias.safe-add '!bash -c "git add \"$@\" && git status"'
git config --global alias.scan-commit '!bash -c "git diff --cached | grep -E \"(AIza|sk-|gsk_|AKIA)\" && echo \"发现敏感信息！\" || echo \"安全检查通过\""'

echo "✅ Git别名已设置:"
echo "  - git check-secrets: 扫描项目中的敏感信息"
echo "  - git safe-add: 安全添加文件并显示状态"
echo "  - git scan-commit: 扫描待提交的更改"

# 4. 验证当前项目安全性
echo ""
echo "🔍 验证当前项目安全性..."

# 检查是否有敏感文件被跟踪
tracked_sensitive=$(git ls-files | grep -E "\.env$|secret|password|key" || true)
if [ -n "$tracked_sensitive" ]; then
    echo "⚠️  发现被跟踪的敏感文件:"
    echo "$tracked_sensitive"
    echo "💡 建议运行: git rm --cached <文件名>"
else
    echo "✅ 没有发现被跟踪的敏感文件"
fi

# 检查.gitignore
if [ -f ".gitignore" ] && grep -q "\.env" .gitignore; then
    echo "✅ .gitignore 配置正确"
else
    echo "⚠️  .gitignore 可能需要更新"
fi

echo ""
echo "🎉 Git安全配置完成！"
echo ""
echo "💡 安全使用建议:"
echo "  1. 提交前运行: ./check_secrets.sh"
echo "  2. 使用: git scan-commit 检查待提交内容"
echo "  3. 定期运行: git check-secrets 扫描项目"
echo "  4. 设置环境变量前先检查 .env.template"
echo ""
