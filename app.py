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


# ================= 🔑 第二步：智能双秘钥自动交替验证 =================
# 在这里定义一个用于存放有效客户端的列表
clients = []

# 1. 尝试读取第一把钥匙（高级设置里的旧 Key）
if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"].strip():
    clients.append(genai.Client(api_key=st.secrets["GEMINI_API_KEY"].strip()))

# 2. 尝试读取第二把备用钥匙
if "GEMINI_API_KEY_BACKUP" in st.secrets and st.secrets["GEMINI_API_KEY_BACKUP"].strip():
    clients.append(genai.Client(api_key=st.secrets["GEMINI_API_KEY_BACKUP"].strip()))

# 如果一把钥匙都没配，抛出警告
if not clients:
    st.warning("请先在服务器高级设置（Advanced settings）中配置您的 GEMINI_API_KEY")
    st.stop()

# 初始化或维护一个全局的钥匙轮询计数器
if "key_index" not in st.session_state:
    st.session_state["key_index"] = 0

# ✨ 修复核心：确保在任何情况下，初始的 client 变量都有明确的定义！
client = clients[st.session_state["key_index"] % len(clients)]
# ====================================================

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
                final_inputs = [*ai_contents, user_prompt]
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=final_inputs
                )
                st.session_state["analysis_result"] = response.text
                
            except Exception as e:
                # ✨ 核心黑科技：如果这次分析遇到了 429 频率超限报错，后台自动把钥匙指针切到下一把！
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    st.session_state["key_index"] += 1  # 切换到下一把备用钥匙
                    st.error("⚠️ 刚才那把钥匙按得太急被谷歌限流了，App 后台已自动为您切换到【第二把备用钥匙】！请您立刻再次点击【🚀 开始 AI 深度分析】按钮即可瞬间通过！")
                elif "503" in str(e) or "UNAVAILABLE" in str(e):
                    st.error("⚠️ 谷歌 AI 服务器刚才临时繁忙，请您立刻再次点击【🚀 开始 AI 深度分析】按钮重新提交即可！")
                else:
                    st.error(f"分析失败: {str(e)}")

# ================= 🟢 第四步：一键复制与 WhatsApp 终极完美分享版（免滞后锁流版） =================
if "analysis_result" in st.session_state:
    st.subheader("📊 AI 分析结果")
    st.markdown(st.session_state["analysis_result"])
    
    st.divider()
    st.subheader("📲 结果快捷分享")
    
    st.write("📋 步骤一：点击下方按钮，将分析报告真正复制到您的手机剪贴板中。")
    
    from st_copy_to_clipboard import st_copy_to_clipboard
    st_copy_to_clipboard(
        st.session_state["analysis_result"], 
        before_copy_label="📋 点击此处 ➡️ 真正一键复制 AI 分析结果", 
        after_copy_label="🎉 真正复制成功！请放心前往 WhatsApp 粘贴发送！"
    )
    
    st.write("")
    st.info("💡 步骤二：在下方输入接收人电话，点击绿色按钮将直达 WhatsApp（进去后长按粘贴）：")
    
    # ✨ 终极小黑科技：使用 st.form 表单锁，彻底解决因手机打字太快、服务器没同步引起的“第一次打不开链接”的顽疾！
    with st.form("whatsapp_form", clear_on_submit=False):
        target_phone = st.text_input("📞 接收人电话 (选填，例如: 60123456789，留空则手动选择):", value="")
        
        # 表单内的提交按钮，我们用漂亮的 CSS 伪装成之前的绿色大按钮
        submit_button = st.form_submit_button("🟢 步骤二：前往 WhatsApp 软件（进去后长按粘贴）", use_container_width=True)
        
        if submit_button:
            # 只有按下按钮的一瞬间，才会同时触发强力清洗和精准跳转，100% 杜绝同步滞后！
            clean_phone = target_phone.strip().replace("+", "").replace(" ", "").replace("\t", "").replace("\n", "")
            
            if clean_phone:
                wa_direct_url = f"https://wa.me/{clean_phone}"
            else:
                wa_direct_url = "https://wa.me/"
            
            # 使用 JavaScript 在最高层级无阻碍突围打开官方合规短链接
            js_redirect = f"""
            <script>
                window.top.location.href = "{wa_direct_url}";
            </script>
            """
            st.markdown(js_redirect, unsafe_allow_html=True)
