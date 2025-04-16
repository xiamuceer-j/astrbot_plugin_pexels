from random import randint, choice
import aiohttp
import logging
from astrbot.api.all import *
import asyncio
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
        self.llm_client = self.context.get_using_provider()  # 获取 LLM 客户端
        # 你可以在这里从配置加载 API 密钥：
        self.api_key = self.config.get("pexels_api_key", "")
        self.base_url = self.config.get("pexels_base_url", "https://api.pexels.com/v1")
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

    async def _fetch_pexels_data(self, per_page=1) -> dict | None:
        """
        内部辅助方法，用于从 Pexels API 获取精选图片。

        Args:
            per_page (int): 每页的图片数量。

        Returns:
            dict or None: Pexels API 的 JSON 响应，如果发生错误则返回 None。
        """
        page = randint(1, 100)
        params = {
            "page": page,
            "per_page": per_page
        }
        curated_url = self.base_url + '/curated'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(curated_url, headers=self.headers, params=params, timeout=10) as response:
                    response.raise_for_status()
                    logger.debug(f"Pexels API 请求成功。状态码: {response.status}")
                    return await response.json()
        except asyncio.TimeoutError:
            logger.error("Pexels API 请求超时。")
            return None
        except aiohttp.ClientResponseError as http_err:
            logger.error(f"Pexels API 发生 HTTP 错误: {http_err} - 状态码: {http_err.status}")
            return None
        except aiohttp.ClientError as req_err:
            logger.error(f"Pexels API 请求发生错误: {req_err}")
            return None
        except Exception as e:
            logger.error(f"Pexels API 调用期间发生意外错误: {e}", exc_info=True)
            return None

    @staticmethod
    def _is_chinese(text):
        """判断字符串是否包含中文字符"""
        for char in text:
            if '\u4e00' <= char <= '\u9fa5':
                return True
        return False

    async def _search_pexels_data(self, query: str, per_page=1) -> dict | None:
        """
        内部辅助方法，用于从 Pexels API 搜索图片。

        Args:
            query (str): 搜索关键词。
            per_page (int): 每页的图片数量。

        Returns:
            dict or None: Pexels API 的 JSON 响应，如果发生错误则返回 None。
        """
        params = {
            "query": query,
            "per_page": per_page
        }
        search_url = self.base_url + '/search'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers, params=params, timeout=10) as response:
                    response.raise_for_status()
                    logger.debug(f"Pexels Search API 请求成功。状态码: {response.status}")
                    return await response.json()
        except asyncio.TimeoutError:
            logger.error("Pexels Search API 请求超时。")
            return None
        except aiohttp.ClientResponseError as http_err:
            logger.error(f"Pexels Search API 发生 HTTP 错误: {http_err} - 状态码: {http_err.status}")
            return None
        except aiohttp.ClientError as req_err:
            logger.error(f"Pexels Search API 请求发生错误: {req_err}")
            return None
        except Exception as e:
            logger.error(f"Pexels Search API 调用期间发生意外错误: {e}", exc_info=True)
            return None

    # --- 命令处理函数 ---
    @command("pexel")
    async def get_pexels_photos(self, event: AstrMessageEvent):
        """
        处理 /pexel 命令，从 Pexels 获取并显示精选图片。
        """
        logger.info(f"收到来自用户 {event.get_sender_id()} 的 /pexel 命令")

        # 使用辅助方法获取数据
        data = await self._fetch_pexels_data(per_page=self._pexels_num)

        if data and 'photos' in data and data['photos']:
            yield event.plain_result("以下是从 Pexels 获取的一些精选图片：")
            for i, photo in enumerate(data['photos']):
                photographer = photo.get('photographer', 'N/A')
                photographer_url = photo.get('photographer_url', '#')
                alt_text = photo.get('alt', 'N/A')
                original_url = photo.get('src', {}).get('large2x')

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

    @command("pexel_s")
    async def search_pexels_photos(self, event: AstrMessageEvent):
        """
        处理 /pexel_s 命令，根据关键词从 Pexels 搜索图片，并随机返回一张。
        """
        logger.info(f"收到来自用户 {event.get_sender_id()} 的 /pexel_s 命令")
        query_parts = event.message_str.split(maxsplit=1)
        if len(query_parts) > 1:
            search_term = query_parts[1]
            logger.info(f"用户 {event.get_sender_id()} 正在搜索 Pexels 图片，关键词: {search_term}")

            final_search_term = search_term
            if self._is_chinese(search_term):
                try:
                    # 获取当前对话 ID
                    curr_cid = await self.context.conversation_manager.get_curr_conversation_id(
                        event.unified_msg_origin)
                    context = []

                    if curr_cid:
                        # 如果当前对话 ID 存在，获取对话对象
                        conversation = await self.context.conversation_manager.get_conversation(
                            event.unified_msg_origin, curr_cid)
                        if conversation and conversation.history:
                            context = json.loads(conversation.history)
                    else:
                        # 如果当前对话 ID 不存在，创建一个新的对话
                        curr_cid = await self.context.conversation_manager.new_conversation(event.unified_msg_origin)
                        await self.context.conversation_manager.get_conversation(event.unified_msg_origin, curr_cid)

                    translation_prompt = f"Translate the following Chinese text to English and output only the translation: '{search_term}'"
                    llm_response = await self.context.get_using_provider().text_chat(
                        prompt=translation_prompt,
                        contexts=context,
                        image_urls=[],
                        system_prompt=self.context.provider_manager.selected_default_persona.get("prompt", "")
                    )
                    final_search_term = llm_response.completion_text.replace("\n", "")
                    if final_search_term:
                        final_search_term = final_search_term
                        logger.info(f"将中文关键词 '{search_term}' 翻译为英文: '{final_search_term}'")
                    else:
                        logger.warning(f"中文关键词 '{search_term}' 翻译失败或返回为空，将使用原始中文关键词进行搜索。")
                except Exception as e:
                    logger.error(f"翻译中文关键词时发生错误: {e}")
                    logger.warning(f"无法翻译中文关键词 '{search_term}'，将使用原始中文关键词进行搜索。")

            data = await self._search_pexels_data(final_search_term, per_page=50)

            if data and 'photos' in data and data['photos']:
                photos = data['photos']
                random_photo = choice(photos)

                photographer = random_photo.get('photographer', 'N/A')
                photographer_url = random_photo.get('photographer_url', '#')
                alt_text = random_photo.get('alt', 'N/A')
                original_url = random_photo.get('src', {}).get('large2x')

                photo_info = (
                    f"--- 搜索结果 ---\n"
                    f"关键词: {search_term}"
                )
                if search_term != final_search_term:
                    photo_info += f" (翻译后: {final_search_term})"
                photo_info += f"\n摄影师: {photographer}\n摄影师主页: {photographer_url}\n描述：{alt_text}\n"

                yield event.plain_result(photo_info)

                # 使用 yield event.image_result 发送图片
                if original_url:
                    yield event.image_result(original_url)
                else:
                    yield event.plain_result("抱歉，无法获取该图片的原始链接。")
                logger.info(f"已向用户 {event.get_sender_id()} 发送关于 '{search_term}' (实际搜索: '{final_search_term}') 的随机 Pexels 图片")

            else:
                error_message = f"抱歉，找不到关于 '{search_term}'"
                if search_term != final_search_term:
                    error_message += f" (或翻译后的 '{final_search_term}')"
                error_message += " 的图片。请尝试其他关键词。"
                logger.warning(f"为 /pexel_s 命令搜索图片失败，关键词: {search_term} (实际搜索: {final_search_term})，API 返回数据为: {data}")
                yield event.plain_result(error_message)
        else:
            yield event.plain_result("请提供您想要搜索的关键词。例如：/pexel_s nature")

    @command("pexel_help")
    async def pexel_help(self, event: AstrMessageEvent):
        """显示 Pexels 插件的帮助信息。"""
        help_msg = """
Pexels 插件帮助：

/pexel - 从 Pexels 获取最新的精选图片，并先发送每张图片的信息，接着发送对应的图片。获取的图片数量从配置中读取。
/pexel_s <关键词> - 根据提供的关键词在 Pexels 上搜索图片，并随机返回一张搜索结果。例如：/pexel_s cat
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