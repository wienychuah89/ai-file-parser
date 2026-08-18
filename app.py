import streamlit as st
from google import genai
import PIL.Image
import urllib.parse  # 用于将 AI 文本编码为 WhatsApp 链接

# 1. 页面基本配置
st.set_page_config(page_title="AI 文件分析助手", layout="centered")

# ================= 🔒 第一步：密码锁 =================
PASSWORD = "你的自定义密码123"  # 👈 保持你之前的密码不变

user_password = st.text_input("🔑 请输入访问密码：", type="password")

if user_password != PASSWORD:
    if user_password: 
        st.error("密码错误，拒绝访问！")
    else:
        st.info("请输入密码以解锁 AI 分析功能。")
    st.stop()


# ================= 🔑 第二步：验证 API 密钥 =================
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("请先在服务器设置中配置您的 GEMINI_API_KEY")
    st.stop()


# ================= 📄 第三步：App 核心业务功能 =================
st.title("📄 AI 多功能文件分析器")
st.write("支持手机防崩溃拍照、上传多图或 PDF 文档。")

# ✨ 新增：拍照模式切换，彻底解决安卓直接拍照无反应的问题
upload_mode = st.radio("📸 请选择输入方式：", ["从相册选择照片/PDF (支持多选)", "手机直接拍照 (防崩溃单张模式)"])

ai_contents = []

if upload_mode == "从相册选择照片/PDF (支持多选)":
    uploaded_files = st.file_uploader(
        "选择图片或 PDF 文件", 
        type=["jpg", "jpeg", "png", "pdf"], 
        accept_multiple_files=True
    )
    if uploaded_files:
        for i, uploaded_file in enumerate(uploaded_files):
            file_type = uploaded_file.name.split(".")[-1].lower()
            if file_type == "pdf":
                ai_contents.append({"mime_type": "application/pdf", "data": uploaded_file.read()})
                st.info(f"📁 已载入 PDF: {uploaded_file.name}")
            else:
                image = PIL.Image.open(uploaded_file)
                ai_contents.append(image)
                st.image(image, width=200, caption=f"📷 照片: {uploaded_file.name}")

else:
    # ✨ 专为安卓直接拍照优化的组件
    camera_file = st.camera_input("请对准文件拍照")
    if camera_file:
        image = PIL.Image.open(camera_file)
        ai_contents.append(image)
        st.success("📷 照片拍摄成功！")

# 只有当有内容输入时，才显示提问框和分析按钮
if ai_contents:
    user_prompt = st.text_area(
        "💬 想对 AI 提问什么？", 
        value="请帮我提取并整理出这几页文件中的关键信息：\n1. 文件的基本主题是什么？\n2. 关键日期（什么时候到期/截止）？\n3. 核心地点或地址？\n4. 联络方式（电话/邮箱/联系人）？"
    )

    # 触发 AI 分析
    if st.button("🚀 开始 AI 深度分析", type="primary"):
        with st.spinner("AI 正在深度分析中，请稍候..."):
            try:
                final_inputs = [*ai_contents, user_prompt]
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=final_inputs
                )
                
                # 将结果存入 Session 状态，方便发送按钮读取
                st.session_state["analysis_result"] = response.text
                
            except Exception as e:
                st.error(f"分析失败: {str(e)}")

# ================= 🟢 第四步：新增一键分享到 WhatsApp =================
if "analysis_result" in st.session_state:
    st.subheader("📊 AI 分析结果")
    st.markdown(st.session_state["analysis_result"])
    
    st.divider()
    st.subheader("📲 结果转发分享")
    
    # 允许输入特定的特定人电话号码（国际格式，例如马来西亚 60123456789）
    # 如果留空，跳转到 WhatsApp 后可以手动选择任何人
    target_phone = st.text_input("📞 接收人电话 (选填，例如: 60123456789，留空则手动选择联系人):", value="")
    
    # 将 AI 文本进行网页编码
    encoded_text = urllib.parse.quote(st.session_state["analysis_result"])
    
    # 构造 WhatsApp 转发链接
    if target_phone.strip():
        whatsapp_url = f"https://whatsapp.com{target_phone.strip()}&text={encoded_text}"
    else:
        whatsapp_url = f"https://whatsapp.com{encoded_text}"
        
    # 在界面渲染一个漂亮的绿色 WhatsApp 按钮
    st.link_button("🟢 一键发送到 WhatsApp", whatsapp_url, use_container_width=True)
