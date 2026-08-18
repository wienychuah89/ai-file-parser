import streamlit as st
from google import genai
import PIL.Image

# 1. 页面基本配置
st.set_page_config(page_title="AI 文件分析助手", layout="centered")

# ================= 🔒 第一步：密码锁 =================
PASSWORD = "cwnpea6125"  # 👈 在这里修改你自己的手机登录密码

user_password = st.text_input("🔑 请输入访问密码：", type="password")

if user_password != PASSWORD:
    if user_password: 
        st.error("密码错误，拒绝访问！")
    else:
        st.info("请输入密码以解锁 AI 分析功能。")
    st.stop() # 密码不对，代码在这里紧急刹车，别人看不到后面的内容
# ====================================================


# ================= 🔑 第二步：验证 API 密钥 =================
# 密码通过后，才会执行到这里，读取你在本地或云端配置好的免费 Key
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("请先在服务器的 Secrets 或本地的 .streamlit/secrets.toml 中配置您的 GEMINI_API_KEY")
    st.stop()
# ==========================================================


# ================= 📄 第三步：App 核心业务功能 =================
st.title("📄 AI 多功能文件分析器")
st.write("支持手机拍照、上传图片或直接上传 PDF 文档，AI 将自动分析内容。")

# 1. 允许接收图片和 PDF 格式
uploaded_files = st.file_uploader(
    "请拍照、选择图片或 PDF 文件（支持单次多张/多个）", 
    type=["jpg", "jpeg", "png", "pdf"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"已成功读取 {len(uploaded_files)} 个文件！")
    
    # 准备传给 AI 的内容列表
    ai_contents = []
    
    # 循环处理和展示每一个上传的文件
    for i, uploaded_file in enumerate(uploaded_files):
        file_type = uploaded_file.name.split(".")[-1].lower()
        
        if file_type == "pdf":
            # 如果是 PDF 格式，转换为大模型需要的原生字节格式
            pdf_bytes = uploaded_file.read()
            ai_contents.append({
                "mime_type": "application/pdf",
                "data": pdf_bytes
            })
            st.info(f"📁 已载入第 {i+1} 个文件: {uploaded_file.name} (PDF 文档)")
        else:
            # 如果是图片格式（JPG/PNG），用 PIL 打开
            image = PIL.Image.open(uploaded_file)
            ai_contents.append(image)
            # ✨ 修复 Bug：直接在这里单张展示图片预览，避免变量冲突
            st.image(image, width=200, caption=f"📷 照片: {uploaded_file.name}")

    # 让你可以自己输入想问的问题，默认填好你最关心的内容
    user_prompt = st.text_area(
        "💬 想对 AI 提问什么？（可直接使用默认问题）", 
        value="请帮我提取并整理出这几页文件中的关键信息：\n1. 文件的基本主题是什么？\n2. 关键日期（什么时候到期/截止）？\n3. 核心地点或地址？\n4. 联络方式（电话/邮箱/联系人）？"
    )

    # 2. 触发 AI 分析
    if st.button("🚀 开始 AI 深度分析", type="primary"):
        with st.spinner("AI 正在阅读文件内容并进行深度分析，请稍候..."):
            try:
                # 把处理好的文件列表和用户的提示词组合在一起
                final_inputs = [*ai_contents, user_prompt]
                
                # 调用 gemini-3.6-flash
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=final_inputs
                )
                
                st.subheader("📊 AI 分析结果")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"分析失败: {str(e)}")
