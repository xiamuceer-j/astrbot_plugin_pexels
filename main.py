from random import randint

import requests
import logging
from pathlib import Path
import json # 如果需要缓存等功能，可能会用到，所以保留导入

from PIL.ImagePalette import random

# 导入必要的 AstrBot 组件
from astrbot.api.all import (
    register,        # 注册插件类的装饰器
    Star,            # 插件的基类
    Context,         # 传递给 __init__ 的上下文对象
    AstrBotConfig,   # 传递给 __init__ 的配置对象
    command,         # 注册命令的装饰器
    AstrMessageEvent # 传递给命令处理函数的事件对象
)
# 根据具体需求，您可能还需要从 astrbot.api.all 导入其他组件

# 设置日志记录 (与示例保持一致)
logger = logging.getLogger(__name__)

# --- 插件注册和类定义 ---

@register("astrbot_plugin_pexels", "xiamuceer-j", "Pexels 精选图片", "1.0.0", "https://github.com/xiamuceer-j/astrbot_plugin_pexels")
class PexelsPlugin(Star):

    def __init__(self, context: Context, config: AstrBotConfig):
        """
        初始化 PexelsPlugin。

        Args:
            context: AstrBot 上下文对象。
            config: AstrBot 配置对象。
        """
        super().__init__(context)
        self.config = config
        # 你可以在这里从配置加载 API 密钥：
        self.api_key = self.config.get("pexels_api_key", "")
        self.base_url = self.config.get("pexels_base_url", "https://api.pexels.com/v1/curated")
        self.pexels_num = self.config.get("pexels_num", "3")
        try:
            self._pexels_num = int(self.pexels_num)
        except ValueError:
            logger.error(f"配置中的 pexels_num 值 '{self.pexels_num}' 无效，将使用默认值 3。")
            self._pexels_num = 3
        # 检查 API 密钥是否已配置（如果 schema 中 default 为 ""）
        if not self.api_key:
            logger.error("Pexels API 密钥未在配置中设置！插件可能无法正常工作。请在配置文件中设置 'pexels_api_key'。")
            # 可以选择抛出异常或仅记录错误
            # raise ValueError("Pexels API 密钥未配置")
            self.headers = {}  # 设置为空 headers，避免后续出错
        else:
            # 根据加载的 API 密钥构建 Headers
            self.headers = {
                "Authorization": self.api_key
            }

        logger.info("PexelsPlugin 已初始化。")
        # 可以选择性地记录加载的配置（但不建议记录完整的 API Key）
        logger.debug(f"Pexels Base URL: {self.base_url}")
        logger.debug(f"Pexels API Key Loaded: {'Yes' if self.api_key else 'No'}")
        logger.debug(f"Pexels Number to Fetch: {self._pexels_num}")

    # --- 辅助方法 ---

    def _fetch_pexels_data(self, per_page=1) -> dict | None:
        """
        内部辅助方法，用于从 Pexels API 获取精选图片。

        Args:
            page (int): 要获取的页码。
            per_page (int): 每页的图片数量。

        Returns:
            dict or None: Pexels API 的 JSON 响应，如果发生错误则返回 None。
        """
        page = randint(1,100)
        params = {
            "page": page,
            "per_page": per_page
        }
        try:
            # 使用实例属性 self.base_url 和 self.headers
            response = requests.get(self.base_url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            logger.debug(f"Pexels API 请求成功。状态码: {response.status_code}")
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("Pexels API 请求超时。")
            return None
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"Pexels API 发生 HTTP 错误: {http_err} - 状态码: {http_err.response.status_code}")
            # 如果可能且需要，记录响应体以供调试
            try:
                logger.error(f"Pexels API 响应内容: {http_err.response.text}")
            except Exception:
                pass # 如果响应体不可读则忽略
            return None
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Pexels API 请求发生错误: {req_err}")
            return None
        except Exception as e:
            # 记录堆栈信息以帮助调试意外错误
            logger.error(f"Pexels API 调用期间发生意外错误: {e}", exc_info=True)
            return None

    # --- 命令处理函数 ---

    @command("pexel")
    async def get_pexels_photos(self, event: AstrMessageEvent):
        """
        处理 /pexel 命令，从 Pexels 获取并显示精选图片。
        """
        logger.info(f"收到来自用户 {event.get_sender_id()} 的 /pexel 命令")

        # 使用辅助方法获取数据
        data = self._fetch_pexels_data(per_page=self._pexels_num)

        if data and 'photos' in data and data['photos']:
            yield event.plain_result("以下是从 Pexels 获取的一些精选图片：")
            for i, photo in enumerate(data['photos']):
                photographer = photo.get('photographer', 'N/A')
                photographer_url = photo.get('photographer_url', '#')
                alt_text = photo.get('alt', 'N/A')
                original_url = photo.get('src', {}).get('original')

                photo_info = (
                    f"--- 图片 {i+1} ---\n"
                    f"摄影师: {photographer}\n"
                    f"摄影师主页: {photographer_url}\n"
                    f"描述：{alt_text}\n"
                )
                yield event.plain_result(photo_info)

                # 使用 yield event.image_result 发送图片
                if original_url:
                    yield event.image_result(original_url)
                else:
                    yield event.plain_result("抱歉，无法获取该图片的原始链接。")

            logger.info(f"已向用户 {event.get_sender_id()} 发送 Pexels 图片信息")

        else:
            # 处理 API 调用失败或未返回图片的情况
            error_message = "抱歉，我现在无法从 Pexels 获取图片。请稍后再试。"
            logger.warning(f"为 /pexel 命令获取图片失败。API 返回数据为: {data}")
            yield event.plain_result(error_message)

    @command("pexel_help")
    async def pexel_help(self, event: AstrMessageEvent):
        """显示 Pexels 插件的帮助信息。"""
        help_msg = """
Pexels 插件帮助：

/pexel - 从 Pexels 获取最新的精选图片，并先发送每张图片的信息，接着发送对应的图片。获取的图片数量从配置中读取。
/pexelhelp - 显示此帮助信息。
        """
        # 移除首尾的空白字符
        yield event.plain_result(help_msg.strip())

# --- 可选：插件生命周期钩子 (如果需要) ---
#    async def on_load(self):
#        """插件加载时执行的操作"""
#        logger.info("PexelsPlugin 已加载。")
#
#    async def on_unload(self):
#        """插件卸载时执行的操作"""
#        logger.info("PexelsPlugin 已卸载。")