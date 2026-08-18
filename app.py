import streamlit as st
from google import genai
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


# ================= 📄 第三步：App 核心业务功能 =================
st.title("📄 AI 多功能文件分析器")

st.warning("⚠️ 重要提示：由于部分安卓手机直接拍照会导致网页刷新崩溃，强烈建议您【先用手机自带相机拍好文件】，再点击下方按钮前往【相册/媒体库】批量勾选上传！")

# 允许图片和PDF格式同时上传
uploaded_files = st.file_uploader(
    "📂 前往相册选择照片或 PDF 文件（支持单次多选）", 
    type=["jpg", "jpeg", "png", "pdf"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"已成功读取 {len(uploaded_files)} 个文件！")
    
    ai_contents = []
    
    # 循环处理和展示每一个上传的文件
    for i, uploaded_file in enumerate(uploaded_files):
        file_type = uploaded_file.name.split(".")[-1].lower()
        file_bytes = uploaded_file.read()  # 💡 核心改良：直接读取文件的原始二进制字节流
        
        if file_type == "pdf":
            # 统一封装为大模型标准的字典格式
            ai_contents.append({
                "mime_type": "application/pdf",
                "data": file_bytes
            })
            st.info(f"📁 已载入 PDF: {uploaded_file.name}")
        else:
            # 判断图片的具体 MIME 类型
            mime_type = "image/jpeg" if file_type in ["jpg", "jpeg"] else "image/png"
            
            # ✨ 终极修复：不再传输 PIL 对象，而是直接将图片封装为原生的字节流传递给最新 SDK
            ai_contents.append({
                "mime_type": mime_type,
                "data": file_bytes
            })
            
            # 仅在网页前端做预览展示
            try:
                image = PIL.Image.open(uploaded_file)
                st.image(image, width=200, caption=f"📷 文件第 {i+1} 页: {uploaded_file.name}")
            except:
                st.info(f"📷 已载入图片: {uploaded_file.name}")

    user_prompt = st.text_area(
        "💬 想对 AI 提问什么？", 
        value="请帮我提取并整理出这几页文件中的关键信息：\n1. 文件的基本主题是什么？\n2. 关键日期（什么时候到期/截止）？\n3. 核心地点或地址？\n4. 联络方式（电话/邮箱/联系人）？"
    )

    # 触发 AI 分析
    if st.button("🚀 开始 AI 深度分析", type="primary"):
        with st.spinner("AI 正在深度分析中，请稍候..."):
            try:
                # 组合二进制流数据和用户的提示词
                final_inputs = [*ai_contents, user_prompt]
                
                # 调用 2026 最新版的 gemini-3.6-flash 进行超强兼容性识别
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=final_inputs
                )
                st.session_state["analysis_result"] = response.text
                
            except Exception as e:
                st.error(f"分析失败: {str(e)}")

# ================= 🟢 第四步：一键分享到 WhatsApp =================
if "analysis_result" in st.session_state:
    st.subheader("📊 AI 分析结果")
    st.markdown(st.session_state["analysis_result"])
    
    st.divider()
    st.subheader("📲 结果转发分享")
    
    target_phone = st.text_input("📞 接收人电话 (选填，例如: 60123456789，留空则手动选择联系人):", value="")
    encoded_text = urllib.parse.quote(st.session_state["analysis_result"])
    
    if target_phone.strip():
        whatsapp_url = f"https://whatsapp.com{target_phone.strip()}&text={encoded_text}"
    else:
        whatsapp_url = f"https://whatsapp.com{encoded_text}"
        
    st.link_button("🟢 一键发送到 WhatsApp", whatsapp_url, use_container_width=True)
