# 🌟 PREMIUM UI TRICK: Completely hide the GitHub Fork button and Cat Logo
import streamlit as st
from google import genai
from google.genai import types
import PIL.Image
import io
import os
import re
import json
import asyncio
import datetime
import pandas as pd
import edge_tts
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from st_copy_to_clipboard import st_copy_to_clipboard

from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# 1. 页面基本配置
st.set_page_config(page_title="AI 文件与发票助手", layout="centered")

# ==========================================
# 📱 针对超长屏与移动端的样式优化
# ==========================================
st.markdown(
    """
    <style>
    [data-testid="stHeader"], [data-testid="stAppDeployButton"], header, .stAppHeader, a[href*="github.com"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        padding: 0px !important;
        margin: 0px !important;
    }
    
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

# ================= 📊 Google Sheets 数据库连接层 =================
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def get_user_sheet():
    client = get_gspread_client()
    return client.open_by_url(st.secrets["GSHEET_URL"]).sheet1

def get_all_users():
    try:
        sheet = get_user_sheet()
        records = sheet.get_all_records(value_render_option="FORMATTED_VALUE")
        users_dict = {}
        for idx, r in enumerate(records, start=2):
            raw_u = str(r.get("username", "")).strip()
            raw_p = str(r.get("password", "")).strip()
            
            user_entry = {
                "row": idx,
                "password": raw_p,
                "daily_limit": int(r["daily_limit"]) if str(r.get("daily_limit", "")).isdigit() else 2,
                "used_today": int(r["used_today"]) if str(r.get("used_today", "")).isdigit() else 0,
                "last_date": str(r.get("last_date", "")).strip()
            }
            users_dict[raw_u] = user_entry
            if raw_u.startswith("0"):
                users_dict[raw_u.lstrip("0")] = user_entry
            else:
                users_dict[f"0{raw_u}"] = user_entry
        return users_dict
    except Exception:
        return {}

# ================= 🔒 第一步：用户登录与自主注册系统 =================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = None

if not st.session_state["authenticated"]:
    st.title("🔐 AI 分析器用户通道")
    
    tab_login, tab_register = st.tabs(["🔑 用户登录", "📝 新用户注册"])
    
    with tab_login:
        login_u = st.text_input("📞 手机号 / 用户名：", key="login_username")
        login_p = st.text_input("🔑 密码：", type="password", key="login_password")
        if st.button("立即登录", type="primary", use_container_width=True):
            with st.spinner("正在验证..."):
                users = get_all_users()
                clean_u = login_u.strip()
                clean_p = login_p.strip()
                
                matched_user = None
                if clean_u in users:
                    matched_user = users[clean_u]
                elif clean_u.lstrip("0") in users:
                    matched_user = users[clean_u.lstrip("0")]
                elif f"0{clean_u}" in users:
                    matched_user = users[f"0{clean_u}"]
                
                if matched_user and str(matched_user["password"]).strip() == clean_p:
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = clean_u
                    st.success("✅ 登录成功！")
                    st.rerun()
                else:
                    st.error("❌ 用户名或密码错误！")
                    
    with tab_register:
        st.info("🚧 **系统升级维护中**")
        st.warning("⚠️ 为了提供更优质的发票汇总功能，新用户注册通道暂时关闭升级。")
        st.caption("💡 已有账号的用户可直接切换到【用户登录】正常使用。预计很快恢复注册，敬请期待！")
    st.stop()
# =============================================================

# ================= 🔑 第二步：智能 API Key 初始化 =================
clients = []
if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"].strip():
    clients.append(genai.Client(api_key=st.secrets["GEMINI_API_KEY"].strip()))
if "GEMINI_API_KEY_BACKUP" in st.secrets and st.secrets["GEMINI_API_KEY_BACKUP"].strip():
    clients.append(genai.Client(api_key=st.secrets["GEMINI_API_KEY_BACKUP"].strip()))
if "GEMINI_API_KEY_TRIPLE" in st.secrets and st.secrets["GEMINI_API_KEY_TRIPLE"].strip():
    clients.append(genai.Client(api_key=st.secrets["GEMINI_API_KEY_TRIPLE"].strip()))

if not clients:
    st.warning("⚠️ 请先在 Streamlit Secrets 中配置 GEMINI_API_KEY")
    st.stop()

if "key_index" not in st.session_state:
    st.session_state["key_index"] = 0

def compress_image(image_bytes: bytes, max_dimension: int = 1600, quality: int = 82) -> bytes:
    try:
        img = PIL.Image.open(io.BytesIO(image_bytes))
        if hasattr(img, '_getexif'):
            img = PIL.ImageOps.exif_transpose(img) if hasattr(PIL, 'ImageOps') else img
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((max_dimension, max_dimension), PIL.Image.Resampling.LANCZOS)
        output_io = io.BytesIO()
        img.save(output_io, format="JPEG", quality=quality, optimize=True)
        return output_io.getvalue()
    except Exception:
        return image_bytes

# 🌟 生成包含明细与分类汇总双 Sheet 的财务级 Excel
def create_formatted_excel(df: pd.DataFrame) -> bytes:
    df_export = df.copy()
    
    # 确保数值格式安全
    df_export["税额 (SST)"] = pd.to_numeric(df_export["税额 (SST)"], errors="coerce").fillna(0.0)
    df_export["总金额 (Total)"] = pd.to_numeric(df_export["总金额 (Total)"], errors="coerce").fillna(0.0)
    
    tax_total = df_export["税额 (SST)"].sum()
    amount_total = df_export["总金额 (Total)"].sum()
    
    # 生成分类汇总表
    category_summary = df_export.groupby("分类")["总金额 (Total)"].sum().reset_index()
    category_summary.columns = ["消费类别", "分类汇总金额 (RM)"]
    
    # 明细表追加总计行
    total_row = {
        "日期": "总计 (TOTAL)",
        "商家名称": f"共 {len(df_export)} 张单据",
        "分类": "-",
        "单据号码": "-",
        "税额 (SST)": tax_total,
        "总金额 (Total)": amount_total
    }
    df_detail = pd.concat([df_export, pd.DataFrame([total_row])], ignore_index=True)
    
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df_detail.to_excel(writer, index=False, sheet_name="发票收据明细")
        category_summary.to_excel(writer, index=False, sheet_name="分类统计汇总")
        
        # 样式定义
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(name="微软雅黑", size=11, bold=True, color="FFFFFF")
        total_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        total_font = Font(name="微软雅黑", size=11, bold=True, color="000000")
        regular_font = Font(name="微软雅黑", size=10)
        
        thin_border = Border(
            left=Side(style='thin', color='D3D3D3'),
            right=Side(style='thin', color='D3D3D3'),
            top=Side(style='thin', color='D3D3D3'),
            bottom=Side(style='thin', color='D3D3D3')
        )
        double_bottom_border = Border(
            left=Side(style='thin', color='D3D3D3'),
            right=Side(style='thin', color='D3D3D3'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='double', color='000000')
        )

        # 格式化 Sheet 1：发票收据明细
        ws1 = writer.sheets["发票收据明细"]
        for col in range(1, ws1.max_column + 1):
            cell = ws1.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for row in range(2, ws1.max_row + 1):
            is_total = (row == ws1.max_row)
            for col in range(1, ws1.max_column + 1):
                cell = ws1.cell(row=row, column=col)
                cell.font = total_font if is_total else regular_font
                cell.border = double_bottom_border if is_total else thin_border
                if is_total:
                    cell.fill = total_fill

                if col in (5, 6):
                    cell.number_format = '#,##0.00;(#,##0.00);0.00'
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                elif col in (1, 3, 4):
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

        for col in ws1.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws1.column_dimensions[col_letter].width = max(max_len + 8, 16)

        # 格式化 Sheet 2：分类统计汇总
        ws2 = writer.sheets["分类统计汇总"]
        for col in range(1, ws2.max_column + 1):
            cell = ws2.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for row in range(2, ws2.max_row + 1):
            for col in range(1, ws2.max_column + 1):
                cell = ws2.cell(row=row, column=col)
                cell.font = regular_font
                cell.border = thin_border
                if col == 2:
                    cell.number_format = '#,##0.00;(#,##0.00);0.00'
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="center", vertical="center")

        for col in ws2.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws2.column_dimensions[col_letter].width = max(max_len + 8, 20)

    return excel_buffer.getvalue()

# ================= 📄 第三步：App 核心业务功能 =================
st.title("📄 AI 多功能文件与发票助手")

users = get_all_users()
current_user = st.session_state["current_user"]
user_data = users.get(current_user, None)

today_str = str(datetime.date.today())
remaining_quota = 2

if user_data:
    if user_data["last_date"] != today_str:
        try:
            sheet = get_user_sheet()
            sheet.update_cell(user_data["row"], 4, 0)
            sheet.update_cell(user_data["row"], 5, today_str)
            user_data["used_today"] = 0
            user_data["last_date"] = today_str
        except Exception:
            pass

    remaining_quota = max(0, user_data["daily_limit"] - user_data["used_today"])
    st.caption(f"👤 当前账号：`{current_user}` ｜ 今日剩余可用额度：**{remaining_quota} / {user_data['daily_limit']}** 次")
else:
    st.caption(f"👤 当前账号：`{current_user}` ｜ 今日剩余可用额度：**{remaining_quota}** 次")

st.warning("⚠️ 手机端温馨提示：为防止手机直接拍照导致网页刷新，建议您【先用手机相机拍好文件】，再点击下方按钮前往【相册】选取上传！")

uploaded_files = st.file_uploader(
    "📷 选择单张或多张文件/发票（支持单次多选）", 
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
            compressed_bytes = compress_image(file_bytes)
            ai_contents.append(types.Part.from_bytes(data=compressed_bytes, mime_type="image/jpeg"))
            try:
                preview_img = PIL.Image.open(io.BytesIO(compressed_bytes))
                st.image(preview_img, width=200, caption=f"📷 文件第 {i+1} 页: {uploaded_file.name}")
            except Exception:
                st.info(f"📷 已载入图片: {uploaded_file.name}")

if ai_contents:
    file_mode = st.selectbox(
        "🔮 请选择文件类型：", 
        ["🧾 车辆/商业发票收据 (支持批量导出Excel)", "🏥 肾移植复诊报告", "📄 商业合同与通用文件", "✍️ 自由输入/其他全新文件"]
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
    elif "发票收据" in file_mode:
        default_prompt = (
            "请分析我上传的发票/收据单据（可能包含一张或多张单据）。\n"
            "【任务 1】：输出清晰的人类易读文字总结（包括商户、明细、金额总计）。\n"
            "【任务 2 极为重要】：在回答的最末尾，输出一个用 ```json 与 ``` 包裹的标准 JSON 数组，包含所有单据的结构化数据，字段必须包括：\n"
            "[\n"
            "  {\n"
            "    \"date\": \"单据日期 (YYYY-MM-DD)\",\n"
            "    \"merchant\": \"商家名称\",\n"
            "    \"category\": \"类别 (如: 添油/餐饮/修车/办公/日常)\",\n"
            "    \"invoice_no\": \"单据/发票号码 (无则填 -)\",\n"
            "    \"tax_amount\": 0.00,\n"
            "    \"total_amount\": 0.00\n"
            "  }\n"
            "]"
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
        default_prompt = "请根据我上传的文件，分析核心信息并总结要点\n1."

    user_prompt = st.text_area(
        "💬 您想对 AI 提问什么？（可直接修改或补充）", 
        value=default_prompt,
        height=160
    )

    if st.button("🚀 开始 AI 深度分析", type="primary", use_container_width=True):
        if remaining_quota <= 0:
            st.error("⚠️ 您今日的免费额度已用尽！请明日再来，或联系客服开通无限次通道。")
            st.stop()

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
                    raw_text = response.text
                    st.session_state["analysis_result"] = raw_text
                    
                    # 尝试解析 JSON 发票数据
                    st.session_state["invoice_df"] = None
                    json_match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_text)
                    if json_match:
                        try:
                            json_data = json.loads(json_match.group(1).strip())
                            if isinstance(json_data, list) and len(json_data) > 0:
                                df = pd.DataFrame(json_data)
                                rename_map = {
                                    "date": "日期",
                                    "merchant": "商家名称",
                                    "category": "分类",
                                    "invoice_no": "单据号码",
                                    "tax_amount": "税额 (SST)",
                                    "total_amount": "总金额 (Total)"
                                }
                                df = df.rename(columns=rename_map)
                                df["税额 (SST)"] = pd.to_numeric(df["税额 (SST)"], errors="coerce").fillna(0.0)
                                df["总金额 (Total)"] = pd.to_numeric(df["总金额 (Total)"], errors="coerce").fillna(0.0)
                                st.session_state["invoice_df"] = df
                        except Exception:
                            pass
                    
                    # 语音生成
                    try:
                        clean_voice_text = re.sub(r"```json[\s\S]*?```", "", raw_text)
                        clean_voice_text = clean_voice_text.replace("*", "").replace("#", "").replace("`", "").strip()
                        
                        async def generate_voice_data(text_to_read: str) -> bytes:
                            communicator = edge_tts.Communicate(text_to_read, "zh-CN-YunxiNeural")
                            audio_stream = b""
                            async for chunk in communicator.stream():
                                if chunk["type"] == "audio":
                                    audio_stream += chunk["data"]
                            return audio_stream
                        
                        audio_data = asyncio.run(generate_voice_data(clean_voice_text))
                        if audio_data:
                            st.session_state["audio_bytes"] = audio_data
                    except Exception:
                        pass
                    
                    # 扣减用户额度
                    if user_data and "row" in user_data:
                        try:
                            sheet = get_user_sheet()
                            sheet.update_cell(user_data["row"], 4, user_data["used_today"] + 1)
                        except Exception:
                            pass
                    
                    st.session_state["clear_clipboard_trigger"] = True
                    success = True
                    st.session_state["key_index"] = (st.session_state["key_index"] + attempt) % len(clients)
                    st.rerun()
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

# ================= 🟢 第四步：展示结果与下载 Excel =================
if "analysis_result" in st.session_state and st.session_state["analysis_result"]:
    if st.session_state.get("clear_clipboard_trigger", False):
        st.markdown(
            """
            <script>
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText("");
            }
            </script>
            """,
            unsafe_allow_html=True
        )
        st.session_state["clear_clipboard_trigger"] = False

    st.divider()
    st.subheader("📊 AI 分析与提取结果")
    
    # 🌟 核心亮点：可直接编辑的表格 + 分类汇总看板 + 导出 Excel
    if st.session_state.get("invoice_df") is not None:
        df = st.session_state["invoice_df"]
        
        st.info("💡 **提示**：您可以直接**双击下方表格中的任何单元格**修改金额、店名或分类，下载的 Excel 将自动以您修改后的最新数据为准！")
        
        # 允许用户在线自由编辑
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "税额 (SST)": st.column_config.NumberColumn(format="RM %.2f"),
                "总金额 (Total)": st.column_config.NumberColumn(format="RM %.2f"),
            },
            key="invoice_editor"
        )
        
        # 实时计算用户编辑后的分类汇总
        edited_df["总金额 (Total)"] = pd.to_numeric(edited_df["总金额 (Total)"], errors="coerce").fillna(0.0)
        edited_df["税额 (SST)"] = pd.to_numeric(edited_df["税额 (SST)"], errors="coerce").fillna(0.0)
        
        cat_group = edited_df.groupby("分类")["总金额 (Total)"].sum().reset_index()
        
        # 页面展示轻量化分类看板
        st.write("📈 **分类开销汇总看板**：")
        cols = st.columns(len(cat_group) if len(cat_group) > 0 else 1)
        for idx, row_cat in cat_group.iterrows():
            with cols[idx % len(cols)]:
                st.metric(label=f"🏷️ {row_cat['分类']}", value=f"RM {row_cat['总金额 (Total)']:.2f}")

        # 基于用户修改后的最新数据生成 Excel
        excel_data = create_formatted_excel(edited_df)
        
        def notify_excel_download():
            st.toast("✅ Excel 报表已成功下载！", icon="📥")

        st.download_button(
            label="📥 立即下载 Excel 记账汇总表 (.xlsx)",
            data=excel_data,
            file_name=f"发票报销汇总_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            on_click=notify_excel_download,
            use_container_width=True
        )
        st.caption("💡 文件已保存至您手机/电脑的【下载 (Downloads)】文件夹中。")
        st.write("")

    if "audio_bytes" in st.session_state and st.session_state["audio_bytes"]:
        st.write("🎵 **语音朗读报告**：")
        st.audio(st.session_state["audio_bytes"], format="audio/mp3")
        st.write("")
    
    display_text = re.sub(r"```json[\s\S]*?```", "", st.session_state["analysis_result"]).strip()
    st.markdown(display_text)
    
    st.divider()
    st.subheader("📲 结果快捷分享通道")
    
    share_type = st.radio(
        "📌 请选择您希望分享到 WhatsApp 的内容类型：",
        options=["📝 发送文字报告", "🎵 发送语音报告 (MP3)"],
        horizontal=True,
        key="share_type_radio"
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
            display_text, 
            before_copy_label="📋 点击此处 ➡️ 一键复制 AI 分析文本", 
            after_copy_label="🎉 复制成功！请前往 WhatsApp 粘贴发送！"
        )
        
    elif share_type == "🎵 发送语音报告 (MP3)":
        if "audio_bytes" in st.session_state and st.session_state["audio_bytes"]:
            st.write("💾 **步骤二**：点击下方下载语音文件：")
            
            def notify_voice_download():
                st.toast("✅ 语音文件已下载至 Downloads 文件夹！", icon="🎵")

            st.download_button(
                label="⬇️ 下载语音文件 (voice_report.mp3)",
                data=st.session_state["audio_bytes"],
                file_name="voice_report.mp3",
                mime="audio/mp3",
                on_click=notify_voice_download,
                use_container_width=True
            )
            st.caption("💡 提示：下载后打开 WhatsApp，在聊天框点击 📎 附件选择该 MP3 发送即可。")
        else:
            st.warning("⚠️ 当前暂无语音数据。")

    if "wa_url" in st.session_state and st.session_state["wa_url"]:
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
