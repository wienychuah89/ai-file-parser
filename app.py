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
            final_inputs = [*ai_contents, user_prompt]
            success = False
            
            # ✨ 终极黑科技：直接在后台使用平滑循环，一口气轮流测试你配好的所有钥匙！
            # 无论哪把钥匙卡住，绝对不会刷新网页，保证你上传的文件100%安全留着！
            for attempt in range(len(clients)):
                # 动态挑选出当前轮次要尝试的钥匙
                current_client = clients[(st.session_state["key_index"] + attempt) % len(clients)]
                try:
                    response = current_client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=final_inputs
                    )
                    st.session_state["analysis_result"] = response.text
                    success = True
                    
                    # 💡 如果这把钥匙成功了，顺手更新一下全局指针，让下次默认就用这把好用的钥匙
                    st.session_state["key_index"] = (st.session_state["key_index"] + attempt) % len(clients)
                    break  # 成功拿到报告，立刻跳出循环，去第四步渲染界面
                    
                except Exception as e:
                    # 如果撞到了 429 频率超限，默默在后台记录，并直接允许循环进入下一把钥匙尝试！
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        if attempt < len(clients) - 1:
                            continue  # 后面还有备用钥匙，不报错，直接去试下一把！
                        else:
                            st.error("⚠️ 抱歉，您配好的所有备用钥匙在这一分钟内都按得太频繁被限流了，请您在手机前静静等待 20 秒后再次点击分析即可！")
                    elif "503" in str(e) or "UNAVAILABLE" in str(e):
                        st.error("⚠️ 谷歌 AI 服务器刚才临时繁忙，请您立刻再次点击【🚀 开始 AI 深度分析】按钮重新提交即可！")
                    else:
                        st.error(f"分析失败: {str(e)}")
                        break

# ================= 🟢 第四步：一键复制与 WhatsApp 终极完美分享版（表单穿透修复版） =================
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
    
    # 🌟 终极修复：使用原生的表单来安全锁定电话号码输入框，防止打字太快同步滞后
    with st.form("whatsapp_form", clear_on_submit=False):
        st.info("💡 步骤二：在下方输入接收人电话，并点击【🔒 锁定号码并生成通道】按钮：")
        target_phone = st.text_input("📞 接收人电话 (选填，例如: 60123456789，留空则手动选择):", value="")
        
        # 1. 提交表单的确认键
        lock_button = st.form_submit_button("🔒 步骤二：锁定号码并生成通道", use_container_width=True)
        
        if lock_button:
            # 当用户点击锁定时，强力清洗号码，确保没有隐藏空格
            clean_phone = target_phone.strip().replace("+", "").replace(" ", "").replace("\t", "").replace("\n", "")
            
            if clean_phone:
                st.session_state["wa_url"] = f"https://wa.me/{clean_phone}"
                st.success(f"✅ 号码 {clean_phone} 锁定成功！直达链接已在下方为您为您准备就绪👇")
            else:
                st.session_state["wa_url"] = "https://wa.me/"
                st.success("✅ 已锁定为空号模式！直达链接已在下方为您为您准备就绪👇")

    # 🌟 2. 极其巧妙地把真正的绿色跳转大按钮【拿到表单外面来渲染】！
    # 这样既享受了表单对打字滞后的完美保护，又 100% 击穿了表单对跳转动作的安全拦截！
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
            margin-top: 15px; 
            box-shadow: 0px 4px 10px rgba(37,211,102,0.3);
        ">🟢 步骤三：点击前往 WhatsApp 软件（进去后长按粘贴）</a>
        """
        st.markdown(whatsapp_btn_html, unsafe_allow_html=True)
