from fastapi import FastAPI, Query
from typing import Optional
import json
import time
import os
import requests
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from apis.playwright_cookies import test_cookie_getter
from apis.xhs_pc_apis import XHS_Apis
from fastapi.responses import Response
from fastapi.responses import StreamingResponse
from fastapi import Request

# ==============================
# 🚀 应用初始化
# ==============================
app = FastAPI(
    title="小红书API接口",
    description="小红书API的FastAPI实现，支持主页、用户、笔记、搜索、消息等全功能，含无水印资源提取",
    version="1.0.0"
)

# 挂载静态资源
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.css",
        swagger_favicon_url="/static/swagger-ui/favicon-32x32.png",
    )

xhs_api = XHS_Apis()

# ==============================
# 🧰 工具函数
# ==============================
def parse_proxies(proxies_str: Optional[str]) -> Optional[dict]:
    """解析代理参数字符串为 dict"""
    if not proxies_str:
        return None
    try:
        return json.loads(proxies_str)
    except json.JSONDecodeError:
        return {"error": "代理配置格式错误，应为JSON字符串"}

@app.get("/proxy/image", summary="🖼️ 代理小红书图片（绕过 403）")
def proxy_image(url: str = Query(..., description="原始图片 URL")):
    """代理图片请求，添加合法 headers 绕过反爬"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.xiaohongshu.com/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return Response(content=resp.content, media_type="image/jpeg")
    except:
        pass
    return {"success": False, "msg": "Proxy failed"}

@app.get("/proxy/video", summary="🎥 代理小红书视频（支持拖拽）")
async def proxy_video(request: Request, url: str = Query(..., description="原始视频 URL")):
    """支持 Range 请求的视频代理，解决 403 和无法拖拽问题"""
    try:
        # 获取客户端 Range 头（用于拖拽）
        range_header = request.headers.get("range")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.xiaohongshu.com/",
        }
        if range_header:
            headers["Range"] = range_header

        # 发起流式请求（stream=True）
        resp = requests.get(url, headers=headers, stream=True, timeout=10)

        # 构建响应头
        response_headers = {
            "Content-Type": "video/mp4",
            "Accept-Ranges": "bytes",
        }
        if "Content-Length" in resp.headers:
            response_headers["Content-Length"] = resp.headers["Content-Length"]
        if "Content-Range" in resp.headers:
            response_headers["Content-Range"] = resp.headers["Content-Range"]

        # 状态码：206（部分）或 200（完整）
        status_code = 206 if range_header and resp.status_code == 206 else 200

        # ✅ 正确返回流式响应
        return StreamingResponse(
            resp.iter_content(chunk_size=8192),
            media_type="video/mp4",
            status_code=status_code,
            headers=response_headers
        )
    except Exception as e:
        return {"success": False, "msg": f"视频代理异常: {str(e)}"}

# ==============================
# 🎫 游客 Cookies 接口（带缓存）
# ==============================
_guest_cookies_cache = {"value": "", "expires_at": 0}

@app.get(
    "/guestcookies",
    summary="🎫 获取游客 cookies",
    description="返回有效的游客 cookies，用于免登录访问公开内容。内部缓存 5 分钟，避免频繁请求。"
)
@app.get("/guestcookies", summary="获取小红书游客cookies")
def get_guest_cookies():
    """获取小红书游客cookies"""
    global _guest_cookies_cache
    now = time.time()
    # 缓存 5 分钟（300 秒）
    if _guest_cookies_cache["value"] and _guest_cookies_cache["expires_at"] > now:
        return {"success": 200, "data": _guest_cookies_cache["value"]}
    success, data = test_cookie_getter()
    _guest_cookies_cache["value"] = data
    _guest_cookies_cache["expires_at"] = now + 300  # 5分钟缓存
    return {"success": success, "data": data}

@app.get("/guestcookies/refresh", summary="🔄 强制刷新游客 cookies")
def refresh_guest_cookies():
    """强制清除缓存并重新获取游客 cookies"""
    global _guest_cookies_cache
    _guest_cookies_cache["value"] = ""
    _guest_cookies_cache["expires_at"] = 0
    # 立即重新获取
    success, data = test_cookie_getter()
    now = time.time()
    _guest_cookies_cache["value"] = data
    _guest_cookies_cache["expires_at"] = now + 300
    return {"success": success, "data": data}
# ==============================
# 🏠 主页相关接口
# ==============================
@app.get(
    "/homefeed/all-channel",
    summary="📺 获取主页所有频道",
    description="获取小红书首页顶部的所有频道分类（如推荐、穿搭、美食等）"
)
def homefeed_all_channel(
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_homefeed_all_channel(cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/homefeed/recommend",
    summary="✨ 获取主页推荐笔记（分页）",
    description="获取指定频道的推荐笔记列表，需手动传入游标进行分页"
)
def homefeed_recommend(
    category: str = Query(..., description="频道分类，如 'homefeed.recommend'"),
    cursor_score: str = Query("", description="游标分数，用于分页"),
    refresh_type: int = Query(1, description="刷新类型：1-首次加载，3-下拉刷新"),
    note_index: int = Query(0, description="笔记起始索引"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_homefeed_recommend(category, cursor_score, refresh_type, note_index, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/homefeed/recommend/by-num",
    summary="🔢 按数量获取推荐笔记",
    description="自动翻页，按指定数量获取主页推荐笔记"
)
def homefeed_recommend_by_num(
    category: str = Query(..., description="频道分类"),
    require_num: int = Query(..., ge=1, le=100, description="需要获取的笔记数量（1-100）"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_homefeed_recommend_by_num(category, require_num, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

# ==============================
# 👤 用户相关接口
# ==============================
@app.get(
    "/user/info",
    summary="👤 获取用户公开信息",
    description="获取指定用户的公开资料（昵称、头像、粉丝数、简介等）"
)
def user_info(
    user_id: str = Query(..., description="目标用户ID"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_user_info(user_id, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/user/self-info",
    summary="🧍 获取当前用户信息（基础）",
    description="获取当前登录用户的基础信息"
)
def user_self_info(
    cookies_str: str = Query(..., description="当前用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_user_self_info(cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/user/self-info2",
    summary="🧍‍♂️ 获取当前用户信息（详细）",
    description="获取当前登录用户的详细信息（含 UID、等级、成长值等）"
)
def user_self_info2(
    cookies_str: str = Query(..., description="当前用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_user_self_info2(cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/user/notes",
    summary="📓 获取用户所有笔记",
    description="自动翻页，获取用户发布的全部笔记"
)
def user_all_notes(
    user_url: str = Query(..., description="用户主页 URL，含 xsec_token"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_user_all_notes(user_url, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/user/likes",
    summary="❤️ 获取用户所有喜欢的笔记",
    description="自动翻页，获取用户点赞过的全部笔记"
)
def user_all_likes(
    user_url: str = Query(..., description="用户主页 URL，含 xsec_token"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_user_all_like_note_info(user_url, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/user/collections",
    summary="🔖 获取用户所有收藏的笔记",
    description="自动翻页，获取用户收藏的全部笔记"
)
def user_all_collections(
    user_url: str = Query(..., description="用户主页 URL，含 xsec_token"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_user_all_collect_note_info(user_url, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/user/notes/page",
    summary="📄 分页获取用户笔记",
    description="获取用户在指定位置（分页）发布的笔记"
)
def user_notes_page(
    user_id: str = Query(..., description="用户ID"),
    cursor: str = Query("", description="分页游标"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    xsec_token: str = Query("", description="xsec_token（可选）"),
    xsec_source: str = Query("pc_search", description="来源，如 pc_search"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_user_note_info(user_id, cursor, cookies_str, xsec_token, xsec_source, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/user/likes/page",
    summary="❤️ 分页获取用户喜欢的笔记",
    description="获取用户在指定位置（分页）喜欢的笔记"
)
def user_likes_page(
    user_id: str = Query(..., description="用户ID"),
    cursor: str = Query("", description="分页游标"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    xsec_token: str = Query("", description="xsec_token（可选）"),
    xsec_source: str = Query("pc_user", description="来源，如 pc_user"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_user_like_note_info(user_id, cursor, cookies_str, xsec_token, xsec_source, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/user/collections/page",
    summary="🔖 分页获取用户收藏的笔记",
    description="获取用户在指定位置（分页）收藏的笔记"
)
def user_collections_page(
    user_id: str = Query(..., description="用户ID"),
    cursor: str = Query("", description="分页游标"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    xsec_token: str = Query("", description="xsec_token（可选）"),
    xsec_source: str = Query("pc_search", description="来源，如 pc_search"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_user_collect_note_info(user_id, cursor, cookies_str, xsec_token, xsec_source, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

# ==============================
# 📝 笔记相关接口
# ==============================
@app.get(
    "/note/info",
    summary="📄 获取笔记详情",
    description="获取单篇笔记的完整信息（标题、正文、图片、作者、互动数据等）"
)
def note_info(
    url: str = Query(..., description="笔记完整 URL，含 xsec_token"),
    cookies_str: Optional[str] = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_note_info(url, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/note/comments",
    summary="💬 获取笔记全部评论",
    description="自动翻页，获取笔记所有一级和二级评论"
)
def note_all_comments(
    url: str = Query(..., description="笔记完整 URL，含 xsec_token"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_note_all_comment(url, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/note/comments/outer/page",
    summary="🗨️ 分页获取一级评论",
    description="获取笔记的一级评论（分页加载）"
)
def note_outer_comments_page(
    note_id: str = Query(..., description="笔记ID"),
    cursor: str = Query("", description="分页游标"),
    xsec_token: str = Query(..., description="xsec_token（必需）"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_note_out_comment(note_id, cursor, xsec_token, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/note/comments/inner/page",
    summary="↪️ 分页获取二级评论",
    description="获取某条一级评论下的二级回复（分页）"
)
def note_inner_comments_page(
    note_id: str = Query(..., description="笔记ID"),
    root_comment_id: str = Query(..., description="一级评论ID"),
    cursor: str = Query("", description="分页游标"),
    xsec_token: str = Query(..., description="xsec_token（必需）"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    comment_stub = {"note_id": note_id, "id": root_comment_id}
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_note_inner_comment(comment_stub, cursor, xsec_token, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/note/comments/inner/all",
    summary="🔁 获取单条评论所有二级评论",
    description="自动翻页，获取某条评论下的全部二级评论"
)
def note_inner_comments_all(
    note_id: str = Query(..., description="笔记ID"),
    root_comment_id: str = Query(..., description="一级评论ID"),
    sub_comment_has_more: bool = Query(False, description="是否有更多二级评论"),
    sub_comment_cursor: str = Query("", description="二级评论游标"),
    xsec_token: str = Query(..., description="xsec_token（必需）"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    comment = {
        "note_id": note_id,
        "id": root_comment_id,
        "sub_comment_has_more": sub_comment_has_more,
        "sub_comment_cursor": sub_comment_cursor,
        "sub_comments": []
    }
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_note_all_inner_comment(comment, xsec_token, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/note/no-watermark/video",
    summary="🎥 获取无水印视频",
    description="提取笔记中的无水印视频直链（无需 cookies）"
)
def note_no_water_video(
    note_id: str = Query(..., description="笔记ID")
):
    success, msg, data = xhs_api.get_note_no_water_video(note_id)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/note/no-watermark/image",
    summary="🖼️ 获取无水印图片",
    description="将带水印图片 URL 转为高清无水印版本（无需 cookies）"
)
def note_no_water_img(
    img_url: str = Query(..., description="带水印的图片 URL")
):
    success, msg, data = xhs_api.get_note_no_water_img(img_url)
    return {"success": success, "msg": msg, "data": data}

# ==============================
# 🔍 搜索相关接口
# ==============================
@app.get(
    "/search/keyword",
    summary="🔍 获取搜索关键词推荐",
    description="根据输入关键词，返回搜索联想词"
)
def search_keyword(
    word: str = Query(..., description="输入的关键词"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_search_keyword(word, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/search/note",
    summary="🔎 搜索笔记（单页）",
    description="按条件搜索笔记（单页结果），支持排序、时间、类型等筛选"
)
def search_note(
    query: str = Query(..., description="搜索关键词"),
    page: int = Query(1, description="页码"),
    sort_type_choice: int = Query(0, ge=0, le=4, description="排序：0-综合 1-最新 2-最热 3-最多评论 4-最多收藏"),
    note_type: int = Query(0, ge=0, le=2, description="类型：0-不限 1-视频 2-图文"),
    note_time: int = Query(0, ge=0, le=3, description="时间：0-不限 1-1天 2-1周 3-半年"),
    note_range: int = Query(0, ge=0, le=3, description="范围：0-不限 1-已看 2-未看 3-已关注"),
    pos_distance: int = Query(0, ge=0, le=2, description="位置：0-不限 1-同城 2-附近"),
    geo: str = Query("", description="地理位置，JSON 格式如 {\"latitude\":39.9,\"longitude\":116.4}"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    geo_data = json.loads(geo) if geo else None
    success, msg, data = xhs_api.search_note(query, cookies_str, page, sort_type_choice, note_type, note_time, note_range, pos_distance, geo_data, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/search/note/by-num",
    summary="🔢 按数量搜索笔记",
    description="自动翻页，按指定数量获取搜索笔记，支持高级筛选"
)
def search_some_note(
    query: str = Query(..., description="搜索关键词"),
    require_num: int = Query(20, ge=1, le=100, description="需要获取的笔记数量（1-100）"),
    sort_type_choice: int = Query(0, ge=0, le=4, description="排序：0-综合 1-最新 2-最热 3-最多评论 4-最多收藏"),
    note_type: int = Query(0, ge=0, le=2, description="类型：0-不限 1-视频 2-图文"),
    note_time: int = Query(0, ge=0, le=3, description="时间：0-不限 1-1天 2-1周 3-半年"),
    note_range: int = Query(0, ge=0, le=3, description="范围：0-不限 1-已看 2-未看 3-已关注"),
    pos_distance: int = Query(0, ge=0, le=2, description="位置：0-不限 1-同城 2-附近"),
    geo: str = Query("", description="地理位置，JSON 格式如 {\"latitude\":39.9,\"longitude\":116.4}"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    geo_data = json.loads(geo) if geo else None
    success, msg, data = xhs_api.search_some_note(query, require_num, cookies_str, sort_type_choice, note_type, note_time, note_range, pos_distance, geo_data, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/search/user",
    summary="👥 搜索用户（单页）",
    description="按关键词搜索用户（单页）"
)
def search_user(
    query: str = Query(..., description="搜索关键词"),
    page: int = Query(1, description="页码"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.search_user(query, cookies_str, page, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/search/user/by-num",
    summary="🔢 按数量搜索用户",
    description="自动翻页，按指定数量获取搜索用户"
)
def search_some_user(
    query: str = Query(..., description="搜索关键词"),
    require_num: int = Query(..., ge=1, le=100, description="需要获取的用户数量"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.search_some_user(query, require_num, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

# ==============================
# 📩 消息中心接口
# ==============================
@app.get(
    "/message/unread",
    summary="📬 获取未读消息数",
    description="获取未读消息总数（评论、点赞、关注等）"
)
def get_unread_message(
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_unread_message(cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/message/mentions",
    summary="🔔 获取所有@和评论提醒",
    description="自动翻页，获取全部被@和评论提醒"
)
def get_all_metions(
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_all_metions(cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/message/likes-collects",
    summary="🌟 获取所有赞和收藏通知",
    description="自动翻页，获取他人点赞/收藏你内容的通知"
)
def get_all_likes_and_collects(
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_all_likesAndcollects(cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/message/new-connections",
    summary="👥 获取所有新增关注",
    description="自动翻页，获取关注你的新用户列表"
)
def get_all_new_connections(
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_all_new_connections(cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/message/mentions/page",
    summary="🔔 分页获取@和评论提醒",
    description="分页获取评论和@消息"
)
def mentions_page(
    cursor: str = Query("", description="分页游标"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_metions(cursor, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/message/likes-collects/page",
    summary="🌟 分页获取赞和收藏通知",
    description="分页获取他人点赞/收藏你的内容的通知"
)
def likes_collects_page(
    cursor: str = Query("", description="分页游标"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_likesAndcollects(cursor, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

@app.get(
    "/message/new-connections/page",
    summary="👥 分页获取新增关注",
    description="分页获取新增关注你的用户通知"
)
def new_connections_page(
    cursor: str = Query("", description="分页游标"),
    cookies_str: str = Query(..., description="用户的 cookies 字符串"),
    proxies: Optional[str] = Query(None, description="代理配置，JSON 字符串")
):
    proxies_dict = parse_proxies(proxies)
    if isinstance(proxies_dict, dict) and "error" in proxies_dict:
        return {"success": False, "msg": proxies_dict["error"], "data": None}
    success, msg, data = xhs_api.get_new_connections(cursor, cookies_str, proxies_dict)
    return {"success": success, "msg": msg, "data": data}

# ==============================
# 🌐 前端页面入口
# ==============================
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard():
    html_path = os.path.join(os.path.dirname(__file__), "static", "dashboard.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    else:
        return HTMLResponse("<h1>前端页面未找到，请创建 static/dashboard.html</h1>")

# ==============================
# 🚀 启动入口
# ==============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)