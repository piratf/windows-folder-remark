"""
基础接口定义
"""

from abc import ABC, abstractmethod


class CommentHandler(ABC):
    """备注处理器基类"""

    @abstractmethod
    def set_comment(self, path, comment):
        """设置备注"""
        pass

    @abstractmethod
    def get_comment(self, path):
        """获取备注"""
        pass

    @abstractmethod
    def delete_comment(self, path):
        """删除备注"""
        pass

    @abstractmethod
    def supports(self, path):
        """检查是否支持该路径类型"""
        pass
