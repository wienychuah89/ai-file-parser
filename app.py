# 🌟 PREMIUM UI TRICK: Completely hide the GitHub Fork button and Cat Logo
import streamlit as st
from google import genai
from google.genai import types
import PIL.Image
import io
import os
import asyncio
import edge_tts
from st_copy_to_clipboard import st_copy_to_clipboard

# 1. 页面基本配置
st.set_page_config(page_title="AI 文件分析器", layout="centered")

# ==========================================
# 📱 针对超长屏与移动端的样式优化
# ==========================================
st.markdown(
    """
    <style>
    /* 隐藏顶部组件 */
    [data-testid="stHeader"], [data-testid="stAppDeployButton"], header, .stAppHeader, a[href*="github.com"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        padding: 0px !important;
        margin: 0px !important;
    }
    
    /* 容器自适应 */
    [data-testid="stAppViewBlockContainer"], .main .block-container, div.block-container {
        padding-top: 0.5rem !important;  
        padding-bottom: 1rem !important;
        max-width: 730px !important; 
        padding-left: 8px !important;   
        padding-right: 8px !important;
    }

    p, span, label, .stText, div {
        word-break: break-word !important;
        letter-spacing: 0.02rem !important;
    }
    
    div[data-testid="stTextInput"] input {
        font-size: 16px !important;     
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ================= 🔒 第一步：智能访问密码锁 =================
PASSWORD = st.secrets.get("APP_PASSWORD", "112234455") 

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 系统登录")
    user_password = st.text_input("🔑 请输入访问密码：", type="password")
    if st.button("登录", type="primary", use_container_width=True):
        if user_password == PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("❌ 密码错误，拒绝访问！")
    st.stop()
# =============================================================

# ================= 🔑 第二步：智能 API Key 初始化 =================
clients = []
if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"].strip():
    clients.append(genai.Client(api_key=st.secrets["GEMINI_API_KEY"].strip()))
if "GEMINI_API_KEY_BACKUP" in st.secrets and st.secrets["GEMINI_API_KEY_BACKUP"].strip():
    clients.append(genai.Client(api_key=st.secrets["GEMINI_API_KEY_BACKUP"].strip()))

if not clients:
    st.warning("⚠️ 请先在 Streamlit Secrets 中配置 GEMINI_API_KEY")
    st.stop()

if "key_index" not in st.session_state:
    st.session_state["key_index"] = 0
# ====================================================

# 🖼️ 图片体积优化压缩函数（大幅节省 Token 与上传时间）
def compress_image(image_bytes: bytes, max_dimension: int = 1600, quality: int = 82) -> bytes:
    try:
        img = PIL.Image.open(io.BytesIO(image_bytes))
        # 处理手机拍照 EXIF 旋转
        if hasattr(img, '_getexif'):
            img = PIL.ImageOps.exif_transpose(img) if hasattr(PIL, 'ImageOps') else img

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # 尺寸等比例缩小
        img.thumbnail((max_dimension, max_dimension), PIL.Image.Resampling.LANCZOS)
        
        output_io = io.BytesIO()
        img.save(output_io, format="JPEG", quality=quality, optimize=True)
        return output_io.getvalue()
    except Exception:
        return image_bytes

# ================= 📄 第三步：App 核心业务功能 =================
st.title("📄 AI 多功能文件分析器")

st.warning("⚠️ 手机端温馨提示：为防止手机直接拍照导致网页刷新，建议您【先用手机相机拍好文件】，再点击下方按钮前往【相册】选取上传！")

uploaded_files = st.file_uploader(
    "📷 选择文件（支持单次多选）", 
    type=["jpg", "jpeg", "png", "pdf"], 
    accept_multiple_files=True
)

ai_contents = []

if uploaded_files:
    st.success(f"已成功读取 {len(uploaded_files)} 个文件！")
    for i, uploaded_file in enumerate(uploaded_files):
        file_type = uploaded_file.name.split(".")[-1].lower()
        file_bytes = uploaded_file.read()
        
        if file_type == "pdf":
            ai_contents.append(types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"))
            st.info(f"📁 已载入 PDF: {uploaded_file.name}")
        else:
            # 自动优化压缩图片
            compressed_bytes = compress_image(file_bytes)
            ai_contents.append(types.Part.from_bytes(data=compressed_bytes, mime_type="image/jpeg"))
            try:
                preview_img = PIL.Image.open(io.BytesIO(compressed_bytes))
                st.image(preview_img, width=200, caption=f"📷 文件第 {i+1} 页: {uploaded_file.name}")
            except Exception:
                st.info(f"📷 已载入图片: {uploaded_file.name}")

# 触发 AI 分析
if ai_contents:
    file_mode = st.selectbox(
        "🔮 请选择文件类型：", 
        ["✍️ 自由输入/其他全新文件", "🧾 车辆/商业发票收据", "📄 商业合同与通用文件", "🏥 肾移植复诊报告"]
    )
    
    user_baseline_prompt = ""
    if file_mode == "🏥 肾移植复诊报告":
        baseline_option = st.selectbox(
            "🩸 请选择您个人的【血清肌酐（Creatinine）长期稳定基线值】(以您医生的医嘱为准)：",
            [
                "🟢 正常健康人群或非常优秀的基线 (60 - 110 umol/L)",
                "🟡 相对平稳的轻度基线 (110 - 130 umol/L)",
                "🟠 常见的中度稳定基线 (130 - 160 umol/L)",
                "🟣 偏高的稳定基线 (160 - 210 umol/L)",
                "⚪ 其他基线（可在下方提问框中自行修改具体数值）"
            ],
            index=3
        )
        user_baseline_prompt = f"我是一名肾移植患者，我个人的血清肌酐（Creatinine）长期基础稳定值大约保持在【{baseline_option}】。\n"
        default_prompt = (
            f"{user_baseline_prompt}"
            "请帮我严格提取并整理化验单关键信息：\n"
            "1. 肌酐（Creat）、尿素（Urea）、血红蛋白（Hb）等核心数值，用Markdown表格列出并附参考值。\n"
            "2. 对比我选定的基线，评估当前数值是否平稳？\n"
            "3. 给出水分摄入、饮食及自我监测提示。"
        )
    elif file_mode == "🧾 车辆/商业发票收据":
        default_prompt = (
            "请提取整理发票/收据中的关键信息：\n"
            "1. 商家名称与地址？\n"
            "2. 消费总金额（Total）？\n"
            "3. 核心服务项目或配件明细？\n"
            "4. 日期及联络人？"
        )
    elif file_mode == "📄 商业合同与通用文件":
        default_prompt = (
            "请提取整理文件核心信息：\n"
            "1. 文件主题与核心条款？\n"
            "2. 关键日期（签署/到期）？\n"
            "3. 签约主体及地点？\n"
            "4. 联络方式？"
        )
    else:
        default_prompt = "请根据我上传的文件，分析核心信息并总结要点。"

    user_prompt = st.text_area(
        "💬 您想对 AI 提问什么？（可直接修改或补充）", 
        value=default_prompt,
        height=160
    )

    if st.button("🚀 开始 AI 深度分析", type="primary", use_container_width=True):
        with st.spinner("AI 正在深度分析中，请稍候..."):
            final_inputs = [*ai_contents, user_prompt]
            success = False
            
            for attempt in range(len(clients)):
                current_client = clients[(st.session_state["key_index"] + attempt) % len(clients)]
                try:
                    # 使用标准 flash 模型降低 Quota 消耗
                    response = current_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=final_inputs
                    )
                    st.session_state["analysis_result"] = response.text
                    
                    # 微软 edge-tts 内存流直接生成，无需读写磁盘
                    try:
                        clean_text = response.text.replace("*", "").replace("#", "").replace("`", "").strip()
                        
                        async def generate_voice_data(text_to_read: str) -> bytes:
                            communicator = edge_tts.Communicate(text_to_read, "zh-CN-YunxiNeural")
                            audio_stream = b""
                            async for chunk in communicator.stream():
                                if chunk["type"] == "audio":
                                    audio_stream += chunk["data"]
                            return audio_stream
                        
                        audio_data = asyncio.run(generate_voice_data(clean_text))
                        if audio_data:
                            st.session_state["audio_bytes"] = audio_data
                    except Exception:
                        pass # 避免 TTS 异常阻断文本展示
                    
                    success = True
                    st.session_state["key_index"] = (st.session_state["key_index"] + attempt) % len(clients)
                    break
                    
                except Exception as e:
                    err_msg = str(e)
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                        if attempt < len(clients) - 1:
                            continue
                        else:
                            st.error(f"⚠️ 当前 API Key 频次达到上限。详细信息: {err_msg}")
                    elif "503" in err_msg or "UNAVAILABLE" in err_msg:
                        st.error("⚠️ AI 服务端短暂繁忙，请重新点击提交。")
                    else:
                        st.error(f"分析失败: {err_msg}")
                        break

# ================= 🟢 第四步：一键复制与 WhatsApp 分享 =================
if "analysis_result" in st.session_state:
    st.subheader("📊 AI 分析结果")
    
    if "audio_bytes" in st.session_state:
        st.write("🎵 **语音朗读报告**：")
        st.audio(st.session_state["audio_bytes"], format="audio/mp3")
        st.write("")
    
    st.markdown(st.session_state["analysis_result"])
    
    st.divider()
    st.subheader("📲 结果快捷分享通道")
    
    share_type = st.radio(
        "📌 请选择您希望分享到 WhatsApp 的内容类型：",
        options=["📝 发送文字报告", "🎵 发送语音报告 (MP3)"],
        horizontal=True
    )
    
    with st.form("whatsapp_form", clear_on_submit=False):
        st.info("💡 步骤一：输入接收人电话并锁定：")
        target_phone = st.text_input("📞 接收人电话 (选填，例如: 60123456789，留空则手动选择):", value="")
        lock_button = st.form_submit_button("🔒 锁定号码并生成通道", use_container_width=True)
        
        if lock_button:
            clean_phone = target_phone.strip().replace("+", "").replace(" ", "").replace("\t", "").replace("\n", "")
            if clean_phone:
                st.session_state["wa_url"] = f"https://wa.me/{clean_phone}"
                st.success(f"✅ 号码 {clean_phone} 锁定成功！")
            else:
                st.session_state["wa_url"] = "https://wa.me/"
                st.success("✅ 已锁定为空号模式！")

    st.write("")

    if share_type == "📝 发送文字报告":
        st.write("📋 **步骤二**：点击下方复制文本报告：")
        st_copy_to_clipboard(
            st.session_state["analysis_result"], 
            before_copy_label="📋 点击此处 ➡️ 一键复制 AI 分析文本", 
            after_copy_label="🎉 复制成功！请前往 WhatsApp 粘贴发送！"
        )
        
    elif share_type == "🎵 发送语音报告 (MP3)":
        if "audio_bytes" in st.session_state:
            st.write("💾 **步骤二**：点击下方下载语音文件：")
            st.download_button(
                label="⬇️ 下载语音文件 (voice_report.mp3)",
                data=st.session_state["audio_bytes"],
                file_name="voice_report.mp3",
                mime="audio/mp3",
                use_container_width=True
            )
            st.caption("💡 提示：下载后打开 WhatsApp，在聊天框点击 📎 附件选择该 MP3 发送即可。")
        else:
            st.warning("⚠️ 当前暂无语音数据。")

    if "wa_url" in st.session_state:
        whatsapp_btn_html = f"""
        <a href="{st.session_state['wa_url']}" target="_blank" style="
            display: block; 
            width: 100%; 
            text-align: center; 
            background-color: #25D366; 
            color: white; 
            padding: 14px 0px; 
            font-size: 16px; 
            font-weight: bold; 
            text-decoration: none; 
            border-radius: 8px; 
            margin-top: 20px; 
            box-shadow: 0px 4px 10px rgba(37,211,102,0.3);
        ">🟢 步骤三：点击前往 WhatsApp</a>
        """
        st.markdown(whatsapp_btn_html, unsafe_allow_html=True)
