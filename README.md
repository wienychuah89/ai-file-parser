# 📄 AI 多功能文件分析器 (AI Multi-Functional File Parser)

一款基于 **Streamlit** 与 **Google Gemini 多模态大模型** 构建的智能文件深度分析工具。支持图片与 PDF 批量解析、针对性业务模板提取、中英双语语音报告生成（TTS），并提供一键 WhatsApp 快捷分享通道。

---

## ✨ 核心特性

- 🔒 **访问安全控制**：内置前端密码锁验证机制，密码由环境变量托管，防止公开部署时被他人滥用。
- 🔑 **多 API Key 故障转移与轮询**：支持配置多个独立的 Gemini API Key，自动处理 `429 (Resource Exhausted)` 限流与故障切换，成倍扩充每日免费配额。
- 🖼️ **智能多模态与体积压缩**：支持单次批量上传 JPG、PNG、PDF 文件；内置图片自动降噪压缩算法，大幅降低 Token 消耗并提升上传速度。
- 🎯 **场景化分析模板**：
  - ✍️ **自由提问模式**：支持针对任意上传文件的自定义 Prompt 问答。
  - 🧾 **车辆 / 商业发票收据**：精准提取商家信息、明细项目、结算总金额与日期。
  - 📄 **商业合同与通用文件**：快速归纳文件主题、关键履约日期、主体及联系方式。
  - 🏥 **肾移植复诊报告**：针对血清肌酐（Creatinine）、尿素（Urea）、血红蛋白等指标对比个人基线进行深度解读与饮食健康提醒。
- 🎵 **高保真语音朗读报告**：利用 `edge-tts` 内存流异步生成中英双语自然语音播报（`zh-CN-YunxiNeural`），无需本地磁盘读写。
- 📲 **WhatsApp 快捷联动**：
  - **文本模式**：一键复制分析结果，配合安全脚本自动清空旧剪贴板残留，直达 WhatsApp 粘贴。
  - **语音模式**：支持一键下载高保真 MP3 报告并通过 WhatsApp 附件快速发送。

---

## 🛠️ 技术栈

- **前端 / 部署框架**：[Streamlit](https://streamlit.io/)
- **AI 大模型推理**：[Google GenAI SDK](https://github.com/google-gemini/generative-ai-python) (`gemini-3.6-flash`)
- **图像处理**：Pillow (PIL)
- **语音合成 (TTS)**：[edge-tts](https://github.com/rany2/edge-tts)
- **剪贴板组件**：`st-copy-to-clipboard`

---

## 📦 依赖环境 (`requirements.txt`)

在部署前，请确保项目根目录下包含 `requirements.txt`：

```text
streamlit
google-genai
pillow
edge-tts
st-copy-to-clipboard


## ⚙️ 配置说明 (secrets.toml)

1.在项目根目录创建 .streamlit/secrets.toml 文件, 为了保护敏感密钥安全，切勿将 API Key 和密码硬编码在代码中。
2.Streamlit Cloud 部署配置, 登录 share.streamlit.io 并部署应用。

## 💡 使用小贴士

移动端拍照上传：为避免移动端浏览器直接调用相机拍照导致网页自动刷新，建议先使用手机自带相机拍好文件，再通过上传组件前往系统相册勾选。
多 Key 额度叠加规则：Google AI Studio 免费额度（Free Tier）是按独立项目（Project）计算的。若要获得翻倍额度（例如 20 + 20 + 20 次/天），各 Key 必须在不同的 Project 下创建。

