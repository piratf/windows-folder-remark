"""
常量定义
"""

MAX_COMMENT_LENGTH = 260

# GitHub 仓库配置
GITHUB_REPO = "piratf/windows-folder-remark"
GITHUB_API_RELEASES = "https://api.github.com/repos/piratf/windows-folder-remark/releases/latest"

# 更新配置
UPDATE_CHECK_INTERVAL = 86400  # 检查间隔（秒），默认 24 小时
UPDATE_CACHE_FILE = "update_check_cache.txt"  # 缓存下次检查时间
