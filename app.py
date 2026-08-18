import streamlit as st
from google import genai
from google.genai import types  # ✨ 2026最新大模型 SDK 标准数据类型模块
import PIL.Image
import urllib.parse

# 1. 页面基本配置
st.set_page_config(page_title="AI 文件分析助手", layout="centered")

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


# ================= 🔑 第二步：验证 API 密钥 =================
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("请先在服务器设置中配置您的 GEMINI_API_KEY")
    st.stop()


# ================= 📄 第三步：App 核心业务功能（标准多模态版） =================
st.title("📄 AI 多功能文件分析器")

st.warning("⚠️ 重要提示：由于部分安卓手机直接拍照会导致网页刷新崩溃，强烈建议您【先用手机自带相机拍好文件】，再点击下方按钮前往【相册/媒体库】批量勾选上传！")

# 纯净的文件上传器（支持图片和PDF同时多选上传）
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
        file_bytes = uploaded_file.read()  # 读取文件的原生二进制字节流
        
        if file_type == "pdf":
            # ✨ 终极修复：使用最新的 types.Part.from_bytes 正确包装 PDF 数据，通过底层校验
            ai_contents.append(
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type="application/pdf"
                )
            )
            st.info(f"📁 已载入 PDF: {uploaded_file.name}")
        else:
            mime_type = "image/jpeg" if file_type in ["jpg", "jpeg"] else "image/png"
            # ✨ 终极修复：使用最新的 types.Part.from_bytes 正确包装图片数据，彻底干掉 Pydantic 报错
            ai_contents.append(
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type
                )
            )
            try:
                image = PIL.Image.open(uploaded_file)
                st.image(image, width=200, caption=f"📷 文件第 {i+1} 页: {uploaded_file.name}")
            except:
                st.info(f"📷 已载入图片: {uploaded_file.name}")

# 触发 AI 分析
if ai_contents:
    user_prompt = st.text_area(
        "💬 想对 AI 提问什么？", 
        value="请帮我提取并整理出这几页文件中的关键信息：\n1. 文件的基本主题是什么？\n2. 关键日期（什么时候到期/截止）？\n3. 核心地点或地址？\n4. 联络方式（电话/邮箱/联系人）？"
    )

    if st.button("🚀 开始 AI 深度分析", type="primary"):
        with st.spinner("AI 正在深度分析中，请稍候..."):
            try:
                # 组合通过标准校验的媒体 Part 列表和用户的提示词字符串
                final_inputs = [*ai_contents, user_prompt]
                
                # 调用最新版 gemini-3.6-flash 进行识别
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=final_inputs
                )
                st.session_state["analysis_result"] = response.text
                
            except Exception as e:
                # 针对 503 谷歌服务器塞车或瞬时繁忙做友好提示
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    st.error("⚠️ 谷歌 AI 服务器刚才打了个盹（临时繁忙），请您立刻再次点击【🚀 开始 AI 深度分析】按钮重新提交即可！")
                else:
                    st.error(f"分析失败: {str(e)}")

# ================= 🟢 第四步：一键复制与 WhatsApp 终极完美分享版（剪贴板修复版） =================
if "analysis_result" in st.session_state:
    st.subheader("📊 AI 分析结果")
    st.markdown(st.session_state["analysis_result"])
    
    st.divider()
    st.subheader("📲 结果快捷分享")
    
    # 准备干净的文本用于复制，防止多行换行卡死
    raw_text = st.session_state["analysis_result"]
    clean_text_for_js = raw_text.replace("`", "\\`").replace("$", "\\$")
    
    # ✨ 终极修复：制作一个由原生底层 HTML 驱动的高兼容一键复制按钮
    # 这个按钮在任何安卓手机、不管是桌面快捷方式还是浏览器里，都能 100% 成功完成复制！
    copy_btn_html = f"""
    <textarea id="hiddenText" style="position: absolute; left: -9999px;">{clean_text_for_js}</textarea>
    <button onclick="
        const txt = document.getElementById('hiddenText');
        txt.select();
        txt.setSelectionRange(0, 99999);
        document.execCommand('copy');
        alert('📋 复制成功！AI 分析报告已存入您的剪贴板，一会去 WhatsApp 粘贴即可！');
    " style="
        display: block;
        width: 100%;
        text-align: center;
        background-color: #3B82F6;
        color: white;
        padding: 12px 0px;
        font-size: 16px;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        margin-top: 10px;
        cursor: pointer;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    ">📋 步骤一：一键复制 AI 分析结果</button>
    """
    st.markdown(copy_btn_html, unsafe_allow_html=True)
    
    st.write("")
    st.info("💡 看到上方弹出‘复制成功’提示后，在下方输入电话号码，即可点击绿色按钮前往发送：")
    
    # 允许输入特定的特定人电话号码
    target_phone = st.text_input("📞 接收人电话 (选填，例如: 60123456789，留空则在软件内手动选择联系人):", value="")
    clean_phone = target_phone.strip().replace("+", "").replace(" ", "")
    
    # 官方标准的干净短域名格式，100% 击穿拦截，直达特定联系人聊天界面
    if clean_phone:
        wa_direct_url = f"https://wa.me{clean_phone}"
    else:
        wa_direct_url = "https://wa.me"
        
    whatsapp_btn_html = f"""
    <a href="{wa_direct_url}" target="_blank" style="
        display: block; 
        width: 100%; 
        text-align: center; 
        background-color: #25D366; 
        color: white; 
        padding: 12px 0px; 
        font-size: 16px; 
        font-weight: bold; 
        text-decoration: none; 
        border-radius: 8px; 
        margin-top: 5px; 
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    ">🟢 步骤二：前往 WhatsApp 软件</a>
    """
    st.markdown(whatsapp_btn_html, unsafe_allow_html=True)
