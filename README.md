<p align="center">
  <a href="https://github.com/cv-cat/Spider_XHS" target="_blank" align="center" alt="Go to XHS_Spider Website">
    <picture>
      <img width="220" src="https://github.com/user-attachments/assets/b817a5d2-4ca6-49e9-b7b1-efb07a4fb325" alt="Spider_XHS logo">
    </picture>
  </a>
</p>


<div align="center">
    <a href="https://www.python.org/">
        <img src="https://img.shields.io/badge/python-3.7%2B-blue" alt="Python 3.7+">
    </a>
    <a href="https://nodejs.org/zh-cn/">
        <img src="https://img.shields.io/badge/nodejs-18%2B-blue" alt="NodeJS 18+">
    </a>
    <a href="https://fastapi.tiangolo.com/">
        <img src="https://img.shields.io/badge/fastapi-0.100%2B-green" alt="FastAPI 0.100+">
    </a>
</div>

# Spider_XHS_Fastapi重构版

## ⭐功能列表

**⚠️ 任何涉及数据注入的操作都是不被允许的，本项目仅供学习交流使用，如有违反，后果自负**

| 模块           | 已实现                                                                             |
|---------------|---------------------------------------------------------------------------------|
| 小红书创作者平台 | ✅ 二维码登录<br/>✅ 手机验证码登录<br/>✅ 上传（图集、视频）作品<br/>✅查看自己上传的作品      |
|    小红书PC    | ✅ 二维码登录<br/> ✅ 手机验证码登录<br/> ✅ 获取无水印图片<br/> ✅ 获取无水印视频<br/> ✅ 获取主页的所有频道<br/>✅ 获取主页推荐笔记<br/>✅ 获取某个用户的信息<br/>✅ 用户自己的信息<br/>✅ 获取某个用户上传的笔记<br/>✅ 获取某个用户所有的喜欢笔记<br/>✅ 获取某个用户所有的收藏笔记<br/>✅ 获取某个笔记的详细内容<br/>✅ 搜索笔记内容<br/>✅ 搜索用户内容<br/>✅ 获取某个笔记的评论<br/>✅ 获取未读消息信息<br/>✅ 获取收到的评论和@提醒信息<br/>✅ 获取收到的点赞和收藏信息<br/>✅ 获取新增关注信息<br/>✅ 获取游客cookies（用于访问笔记详情）|
|    接口服务    | ✅ FastAPI重构（全GET方法调用）<br/>✅ 基础静态快速看板（支持搜索关键词详情提取）<br/>✅ 自动生成API文档 |


## 🌟 功能特性

- ✅ **多维度数据采集**
  - 用户主页信息
  - 笔记详细内容
  - 智能搜索结果抓取
- 🚀 **高性能架构**
  - 自动重试机制
  - FastAPI异步处理支持
- 🔒 **安全稳定**
  - 小红书最新API适配
  - 异常处理机制
  - proxy代理
  - 游客cookies获取机制（降低登录依赖）
- 🎨 **便捷管理**
  - 结构化目录存储
  - 格式化输出（JSON/EXCEL/MEDIA）
  - 基础静态看板（支持二次开发扩展）
  
## 🛠️ 快速开始
### ⛳运行环境
- Python 3.7+
- Node.js 18+
- FastAPI 0.100+

### 🎯安装依赖
pip install -r requirements.txt # 包含 FastAPI 及相关依赖

### 🎨配置文件
配置文件在项目根目录.env文件中，将下图自己的登录cookie放入其中，cookie获取➡️在浏览器f12打开控制台，点击网络，点击fetch，找一个接口点开
![image](https://github.com/user-attachments/assets/6a7e4ecb-0432-4581-890a-577e0eae463d)

复制cookie到.env文件中（注意！登录小红书后的cookie才是有效的，不登陆没有用）
![image](https://github.com/user-attachments/assets/5e62bc35-d758-463e-817c-7dcaacbee13c)

### 🚀运行项目
python fastapi_xhs.py
- 访问 `http://localhost:10000` 进入基础静态快速看板页面
- 访问 `http://localhost:10000/docs` 进入API交互文档页面

### 🗝️注意事项
- fastapi_xhs.py中的代码是接口服务入口，基于FastAPI实现，所有接口均通过GET方法调用
- apis/xhs_pc_apis.py 中的代码包含了所有的api接口，可以根据自己的需求进行修改
- apis/xhs_creator_apis.py 中的代码包含了小红书创作者平台的api接口，可以根据自己的需求进行修改
- 基础静态看板支持搜索关键词详情提取，其余功能可基于现有架构进行二次开发


## 🍥日志
   
| 日期       | 说明                                        |
|----------|-------------------------------------------|
| 23/08/09 | - 首次提交                                    |
| 23/09/13 | - api更改params增加两个字段，修复图片无法下载，有些页面无法访问导致报错 |
| 23/09/16 | - 较大视频出现编码问题，修复视频编码问题，加入异常处理              |
| 23/09/18 | - 代码重构，加入失败重试                             |
| 23/09/19 | - 新增下载搜索结果功能                              |
| 23/10/05 | - 新增跳过已下载功能，获取更详细的笔记和用户信息                 |
| 23/10/08 | - 上传代码☞Pypi，可通过pip install安装本项目           |
| 23/10/17 | - 搜索下载新增排序方式选项（1、综合排序 2、热门排序 3、最新排序）      |
| 23/10/21 | - 新增图形化界面,上传至release v2.1.0               |
| 23/10/28 | - Fix Bug 修复搜索功能出现的隐藏问题                   |
| 25/03/18 | - 更新API，修复部分问题                            |
| 25/06/07 | - 更新search接口，区分视频和图集下载，增加小红书创作者api        |
| 25/07/15 | - 更新 xs version56 & 小红书创作者接口              |
| 25/10/14 | - 使用FastAPI重构（全GET方法调用）；新增获取游客cookies方法；搭建基础静态快速看板；入口文件调整为fastapi_xhs.py |

## 🧸额外说明
1. 感谢star⭐和follow📰！不时更新
2. 感谢原作者<a href="https://github.com/cv-cat/Spider_XHS">cv-cat/Spider_XHS</a>的项目，本项目基于其代码进行重构

## 📈 Star 趋势
<a href="https://www.star-history.com/#bbbbbbbin/Spider_XHS_Fastapi&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=bbbbbbbin/Spider_XHS_Fastapi&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=bbbbbbbin/Spider_XHS_Fastapi&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=bbbbbbbin/Spider_XHS_Fastapi&type=Date" />
 </picture>
</a>