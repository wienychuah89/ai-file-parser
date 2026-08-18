import streamlit as st
from google import genai
from google.genai import types  # 2026最新大模型SDK标准数据类型模块
import PIL.Image
import urllib.parse
import os
import asyncio

# 1. 页面基本配置
st.set_page_config(page_title="AI 文件分析器", layout="centered")

# ================= 🔒 第一步：智能防刷新密码锁 =================
PASSWORD = "cwnpea6125"  # 👈 保持你之前的密码不变

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    user_password = st.text_input("🔑 请输入访问密码：", type="password")
    if user_password == PASSWORD:
        st.session_state["authenticated"] = True
        st.rerun()
    elif user_password:
        st.error("密码错误，拒绝访问！")
    st.stop()
# ====================================================


# ================= 🔑 第二步：智能双秘钥自动交替验证 =================
clients = []
if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"].strip():
    clients.append(genai.Client(api_key=st.secrets["GEMINI_API_KEY"].strip()))
if "GEMINI_API_KEY_BACKUP" in st.secrets and st.secrets["GEMINI_API_KEY_BACKUP"].strip():
    clients.append(genai.Client(api_key=st.secrets["GEMINI_API_KEY_BACKUP"].strip()))

if not clients:
    st.warning("请先在服务器高级设置（Advanced settings）中配置您的 GEMINI_API_KEY")
    st.stop()

if "key_index" not in st.session_state:
    st.session_state["key_index"] = 0

client = clients[st.session_state["key_index"] % len(clients)]
# ====================================================


# ================= 📄 第三步：App 核心业务功能 =================
st.title("📄 AI 多功能文件分析器")

st.warning("⚠️ 手机端温馨提示：为防止手机直接拍照导致网页刷新，强烈建议您【先用手机自带相机拍好文件】，再点击下方按钮前往【相册/媒体库】批量勾选上传！")

# 纯净的文件上传器（支持图片和PDF同时多选上传，支持PNG/JPG/PDF最大200MB）
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
            mime_type = "image/png" if file_type == "png" else "image/jpeg"
            ai_contents.append(types.Part.from_bytes(data=file_bytes, mime_type=mime_type))
            try:
                image = PIL.Image.open(uploaded_file)
                st.image(image, width=200, caption=f"📷 文件第 {i+1} 页: {uploaded_file.name}")
            except:
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
        user_baseline_prompt = f"我是一名肾移植患者，我个人的血清肌酐（Creatinine）长期基础稳定值（Baseline）大约保持在【{baseline_option}】。\n"
        default_prompt = (
            f"{user_baseline_prompt}"
            "请帮我严格提取并整理这几页化验单中的关键信息：\n"
            "1. 肌酐（Creat）、尿素（Urea）、血红蛋白（Hb）等核心数值，用Markdown表格整齐列出，并附带参考说明。\n"
            "2. 请对比我上面选择的个人基线，分析我这次的肾功能是否在我的安全稳定范围内？\n"
            "3. 请给出针对我当前指标需要注意的日常水分摄入、饮食注意事项以及自我监测提示。"
        )
    elif file_mode == "🧾 车辆/商业发票收据":
        default_prompt = (
            "请帮我提取并整理出这张发票/收据中的关键结算信息：\n"
            "1. 商家名称或服务中心地址？\n"
            "2. 消费的总开销金额是多少（总计 Total）？\n"
            "3. 核心的服务项目、更换的零件或消费明细是什么？\n"
            "4. 关键日期（开单日期/服务日期）及联络人？"
        )
    elif file_mode == "📄 商业合同与通用文件":
        default_prompt = (
            "请帮我提取并整理出这几页文件中的核心关键信息：\n"
            "1. 文件的基本主题和核心内容是什么？\n"
            "2. 关键日期（什么时候签约/到期/截止）？\n"
            "3. 核心地点、地址或相关利益方？\n"
            "4. 联络方式（电话/邮箱/联系人）全？"
        )
    else:
        default_prompt = "请根据我上传的文件，帮我分析以下具体问题：\n1. "

    # 渲染最终展示框
    user_prompt = st.text_area(
        "💬 您想对 AI 提问什么？（可直接修改或在下方继续补充）", 
        value=default_prompt,
        height=180
    )

    if st.button("🚀 开始 AI 深度分析", type="primary"):
        with st.spinner("AI 正在深度分析中，请稍候..."):
            final_inputs = [*ai_contents, user_prompt]
            success = False
            
            for attempt in range(len(clients)):
                current_client = clients[(st.session_state["key_index"] + attempt) % len(clients)]
                try:
                    response = current_client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=final_inputs
                    )
                    st.session_state["analysis_result"] = response.text
                    
                    # 🌟 微软智能混读音频广播舱：在安全后台，用纯 Python 异步录制完美中英双语混合朗读 MP3 音频
                    try:
                        import edge_tts
                        clean_text = response.text.replace("*", "").replace("#", "").replace("`", "")
                        
                        async def generate_voice_stream():
                            # 选用微软最顶级的云海西混读男声（自然支持中英混合识别朗读）
                            communicate = edge_tts.Communicate(clean_text, "zh-CN-YunxiNeural")
                            await communicate.save("output_report.mp3")
                            
                        # 触发异步引擎静默录制
                        asyncio.run(generate_voice_stream())
                        
                        with open("output_report.mp3", "rb") as f:
                            st.session_state["audio_bytes"] = f.read()
                        if os.path.exists("output_report.mp3"):
                            os.remove("output_report.mp3")
                    except Exception as tts_err:
                        pass # 确保录制网络波动时不干扰前端文字输出
                    
                    success = True
                    st.session_state["key_index"] = (st.session_state["key_index"] + attempt) % len(clients)
                    break
                    
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        if attempt < len(clients) - 1:
                            continue
                        else:
                            st.error("⚠️ 抱歉，共享通道当前请求过于频繁，所有备用钥匙已被临时控流，请在手机前等待 20 秒后再次点击分析即可！")
                    elif "503" in str(e) or "UNAVAILABLE" in str(e):
                        st.error("⚠️ 谷歌 AI 服务器刚才临时繁忙，请您立刻再次点击【🚀 开始 AI 深度分析】按钮重新提交即可！")
                    else:
                        st.error(f"分析failed: {str(e)}")
                        break

# ================= 🟢 第四步：一键复制与 WhatsApp 终极分享 =================
if "analysis_result" in st.session_state:
    st.subheader("📊 AI 分析结果")
    
    # 🌟 终极穿透控制台：完全抛弃会被手机沙盒死锁静音的任何网页 HTML/JS 代码！
    # 直接拉起官方拥有最高驱动特权的标准多媒体音频轨，100% 击穿拦截，绝对出声！
    if "audio_bytes" in st.session_state:
        st.write("🎵 点击下方【▶️ 播放】键，直接收听由微软智能引擎为您录制的「中英双语高保真声音报告」：")
        st.audio(st.session_state["audio_bytes"], format="audio/mp3")
        st.write("")
    
    # 显示漂亮的原生分析结果文字/表格
    st.markdown(st.session_state["analysis_result"])
    
    st.divider()
    st.subheader("📲 结果快捷分享通道")
    
    with st.form("whatsapp_form", clear_on_submit=False):
        st.info("💡 步骤一：请先在下方输入接收人电话，并点击【🔒 锁定号码并生成绿色通道】按钮：")
        target_phone = st.text_input("📞 接收人电话 (选填，例如: 60123456789，留空则手动选择):", value="")
        lock_button = st.form_submit_button("🔒 步骤一：锁定号码并生成绿色通道", use_container_width=True)
        
        if lock_button:
            clean_phone = target_phone.strip().replace("+", "").replace(" ", "").replace("\t", "").replace("\n", "")
            if clean_phone:
                st.session_state["wa_url"] = f"https://wa.me/{clean_phone}"
                st.success(f"✅ 号码 {clean_phone} 锁定成功！请继续完成下方步骤二和步骤三👇")
            else:
                st.session_state["wa_url"] = "https://wa.me/"
                st.success("✅ 已锁定为空号模式！请继续完成下方步骤二和步骤三👇")

    st.write("")
    st.write("📋 步骤二：点击下方按钮，将上方的分析报告真正复制到您的手机剪贴板中：")
    
    from st_copy_to_clipboard import st_copy_to_clipboard
    st_copy_to_clipboard(
        st.session_state["analysis_result"], 
        before_copy_label="📋 步骤二：点击此处 ➡️ 真正一键复制 AI 分析结果", 
        after_copy_label="🎉 真正复制成功！请放心前往下方步骤三粘贴发送！"
    )

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
            margin-top: 25px; 
            box-shadow: 0px 4px 10px rgba(37,211,102,0.3);
        ">🟢 步骤三：点击前往 WhatsApp 软件（进去后长按粘贴）</a>
        """
        st.markdown(whatsapp_btn_html, unsafe_allow_html=True)
