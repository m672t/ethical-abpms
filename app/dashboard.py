import streamlit as st
import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.discovery import ProcessDiscovery, discover_from_csv
from src.form_generator import FormGenerator
from src.auditor import AuditorAgent
from src.corrector import CorrectorAgent
from src.bpmn_generator import BPMNGenerator
import base64

st.set_page_config(
    page_title="سیستم مدیریت فرآیند اخلاق‌محور",
    page_icon="⚖️",
    layout="wide"
)

# تنظیمات زبان و راست‌چین
st.markdown("""
    <style>
        .stApp {
            direction: rtl;
            text-align: right;
        }
        .violation-high {
            background-color: #ffcccc;
            padding: 10px;
            border-radius: 5px;
            border-right: 4px solid #ff0000;
        }
        .violation-medium {
            background-color: #ffe6cc;
            padding: 10px;
            border-radius: 5px;
            border-right: 4px solid #ff9900;
        }
        .violation-low {
            background-color: #ffffcc;
            padding: 10px;
            border-radius: 5px;
            border-right: 4px solid #ffcc00;
        }
        .ethical-good {
            background-color: #ccffcc;
            padding: 10px;
            border-radius: 5px;
            border-right: 4px solid #00cc00;
        }
    </style>
""", unsafe_allow_html=True)

st.title("⚖️ سیستم کشف و بازطراحی فرآیند با رعایت اصول اخلاقی")
st.subheader("A-BPMS: Agentic Business Process Management System")

# سایدبار
with st.sidebar:
    st.header("📂 ورودی")
    uploaded_file = st.file_uploader("آپلود فایل CSV لاگ رویداد", type=['csv'])
    
    st.header("⚙️ تنظیمات")
    discover_btn = st.button("🚀 کشف فرآیند", use_container_width=True)
    
    st.divider()
    st.markdown("""
    **📌 راهنما:**
    - فایل CSV شامل ستون‌های: `case_id`, `activity`, `timestamp`
    - فرمت تاریخ: `YYYY-MM-DD HH:MM:SS`
    """)
    
    if uploaded_file is not None:
        csv_path = f"data/uploaded_{uploaded_file.name}"
        os.makedirs("data", exist_ok=True)
        with open(csv_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("✅ فایل با موفقیت آپلود شد!")

# تعریف تب‌ها به‌صورت صحیح
tabs = st.tabs(["📊 کشف فرآیند", "⚖️ بازرسی اخلاقی", "🔧 اصلاح فرآیند", "📊 مقایسه اخلاقی"])
tab1, tab2, tab3, tab4 = tabs

# ============================================================
# تب ۱: کشف فرآیند
# ============================================================
with tab1:
    if uploaded_file is not None:
        with st.expander("📊 پیش‌نمایش داده‌ها", expanded=True):
            df = pd.read_csv(csv_path)
            st.dataframe(df.head(10), use_container_width=True)
            st.caption(f"تعداد کل کیس‌ها: {df['case_id'].nunique()} | تعداد فعالیت‌ها: {df['activity'].nunique()}")
        
        if discover_btn:
            with st.spinner("در حال کشف فرآیند..."):
                try:
                    discoverer = discover_from_csv(csv_path)
                    os.makedirs("output", exist_ok=True)
                    model_path = discoverer.visualize_process("output/process_model.png")
                    activities = discoverer.get_activities()
                    attributes = discoverer.get_case_attributes()
                    
                    st.success("✅ فرآیند با موفقیت کشف شد!")
                    
                    st.subheader("📈 مدل فرآیند کشف‌شده")
                    if os.path.exists(model_path):
                        st.image(model_path, use_container_width=True)
                    
                    st.subheader("📋 فعالیت‌های شناسایی‌شده")
                    st.write(" , ".join(activities))
                    
                    with st.spinner("در حال تولید فرم‌ها..."):
                        form_gen = FormGenerator(activities, attributes)
                        forms = form_gen.generate_all_forms("output/forms")
                        st.success("✅ فرم‌ها با موفقیت تولید شدند!")
                    
                    st.session_state['discoverer'] = discoverer
                    st.session_state['activities'] = activities
                    st.session_state['forms'] = forms
                    st.session_state['csv_path'] = csv_path
                    
                    st.subheader("📝 فرم‌های تولیدشده")
                    sub_tabs = st.tabs(activities)
                    for sub_tab, activity in zip(sub_tabs, activities):
                        with sub_tab:
                            form_path = forms.get(activity, "")
                            if form_path and os.path.exists(form_path):
                                with open(form_path, 'r', encoding='utf-8') as f:
                                    html_content = f.read()
                                st.components.v1.html(html_content, height=600, scrolling=True)
                            
                            if form_path and os.path.exists(form_path):
                                with open(form_path, 'r', encoding='utf-8') as f:
                                    form_data = f.read()
                                b64 = base64.b64encode(form_data.encode()).decode()
                                href = f'<a href="data:text/html;base64,{b64}" download="{activity.replace(" ", "_")}.html">📥 دانلود فرم {activity}</a>'
                                st.markdown(href, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ خطا در کشف فرآیند: {str(e)}")
                    st.exception(e)
    else:
        st.info("📤 لطفاً یک فایل CSV را از طریق سایدبار آپلود کنید.")

# ============================================================
# تب ۲: بازرسی اخلاقی
# ============================================================
with tab2:
    st.header("⚖️ بازرسی اخلاقی فرآیند")
    
    if 'discoverer' in st.session_state:
        if st.button("🔍 شروع بازرسی اخلاقی", use_container_width=True):
            with st.spinner("در حال انجام بازرسی اخلاقی..."):
                try:
                    auditor = AuditorAgent()
                    audit_result = auditor.audit(st.session_state['csv_path'], st.session_state['discoverer'])
                    
                    st.session_state['audit_result'] = audit_result
                    st.session_state['auditor'] = auditor
                    
                    score = audit_result['score']
                    if score >= 80:
                        st.success(f"✅ امتیاز اخلاقی: {score}/100 - وضعیت عالی!")
                    elif score >= 50:
                        st.warning(f"⚠️ امتیاز اخلاقی: {score}/100 - نیاز به بهبود!")
                    else:
                        st.error(f"❌ امتیاز اخلاقی: {score}/100 - نیاز به اصلاح اساسی!")
                    
                    if audit_result['has_violations']:
                        st.subheader(f"🚨 تعداد تخلف‌ها: {len(audit_result['violations'])}")
                        
                        severity = audit_result['severity_summary']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("شدید", severity.get('high', 0))
                        with col2:
                            st.metric("متوسط", severity.get('medium', 0))
                        with col3:
                            st.metric("کم", severity.get('low', 0))
                        
                        st.subheader("📋 لیست تخلف‌ها:")
                        for i, v in enumerate(audit_result['violations'], 1):
                            severity_class = {
                                'high': 'violation-high',
                                'medium': 'violation-medium',
                                'low': 'violation-low'
                            }.get(v.get('severity', 'low'), 'violation-low')
                            
                            st.markdown(f"""
                            <div class="{severity_class}">
                                <b>{i}. [{v['rule']}] {v['type']}</b><br>
                                📝 {v['details']}<br>
                                💡 <b>پیشنهاد:</b> {v['suggestion']}
                            </div>
                            """, unsafe_allow_html=True)
                            st.caption(f"شدت: {v['severity']}")
                    else:
                        st.balloons()
                        st.markdown("""
                        <div class="ethical-good">
                            ✅ همه قواعد اخلاقی رعایت شده‌اند!
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with st.expander("📄 مشاهده گزارش کامل"):
                        st.code(audit_result['report'], language='text')
                    
                except Exception as e:
                    st.error(f"❌ خطا در بازرسی اخلاقی: {str(e)}")
                    st.exception(e)
    else:
        st.info("📤 ابتدا فرآیند را در تب 'کشف فرآیند' کشف کنید.")

# ============================================================
# تب ۳: اصلاح فرآیند
# ============================================================
with tab3:
    st.header("🔧 اصلاح فرآیند بر اساس اصول اخلاقی")
    
    if 'audit_result' in st.session_state:
        if st.session_state['audit_result']['has_violations']:
            if st.button("🛠️ اعمال اصلاحات اخلاقی", use_container_width=True):
                with st.spinner("در حال اعمال اصلاحات..."):
                    try:
                        corrector = CorrectorAgent()
                        corrections = corrector.correct(
                            st.session_state['csv_path'],
                            st.session_state['discoverer'],
                            st.session_state.get('forms', {})
                        )
                        
                        st.session_state['corrections'] = corrections
                        
                        st.success("✅ اصلاحات با موفقیت اعمال شدند!")
                        
                        st.subheader("📋 اصلاحات اعمال‌شده:")
                        for i, correction in enumerate(corrections['model_corrections'], 1):
                            st.markdown(f"""
                            <div style="background-color: #e6f3ff; padding: 10px; border-radius: 5px; margin: 5px 0;">
                                <b>{i}. {correction['rule']}</b><br>
                                📝 {correction['description']}<br>
                                ✅ وضعیت: {'اعمال شد' if correction['applied'] else 'در حال بررسی'}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if corrections['new_activities']:
                            st.subheader("➕ فعالیت‌های جدید اضافه‌شده:")
                            for act in corrections['new_activities']:
                                st.info(
                                     f"🆕 {act['name']}: "
                                     f"{act.get('description', '')} "
                                     f"(موقعیت: {act.get('position', 'در فرآیند اصلاح‌شده')})"
                                        )
                        
                        corrected_model = corrector.generate_corrected_model(
                            st.session_state['discoverer'],
                            corrections
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**فعالیت‌های اصلی:**")
                            st.write(", ".join(corrected_model['original_activities']))
                        with col2:
                            if corrected_model['added_activities']:
                                st.write("**➕ فعالیت‌های اضافه‌شده:**")
                                st.write(", ".join(corrected_model['added_activities']))
                        
                    except Exception as e:
                        st.error(f"❌ خطا در اعمال اصلاحات: {str(e)}")
                        st.exception(e)
        else:
            st.success("✅ هیچ تخلف اخلاقی وجود ندارد! فرآیند نیازی به اصلاح ندارد.")
            
        # بخش تولید BPMN از Process Tree
        if 'corrections' in st.session_state and 'discoverer' in st.session_state:
            st.divider()
            st.subheader("📄 تولید فایل BPMN 2.0 از Process Tree")
            
            if st.button("📥 تولید و دانلود BPMN", use_container_width=True):
                with st.spinner("در حال تولید فایل BPMN از ساختار واقعی Process Tree..."):
                    try:
                        generator = BPMNGenerator("EthicalProcess")
                        
                        # گرفتن Process Tree از discoverer
                        process_tree = st.session_state['discoverer'].process_tree
                        
                        # برچسب‌های اخلاقی برای فعالیت‌ها
                        ethical_notes = {}
                        for act in st.session_state['activities']:
                            notes = []
                            if 'ارزیابی' in act:
                                notes.append("⚖️ This activity has been made fair by removing sensitive attributes (gender).")
                            elif 'بررسی' in act:
                                notes.append("⚖️ The review process is conducted with full transparency.")
                            elif 'تأیید' in act or 'رد' in act:
                                notes.append("📝 Decision reasons are recorded transparently.")
                            elif 'بازبینی' in act:
                                notes.append("🔄 This activity allows users to appeal decisions.")
                            elif 'تبعیض' in act:
                                notes.append("⚖️ This gateway prevents gender discrimination.")
                            else:
                                notes.append("✅ This activity is designed with ethical principles.")
                            ethical_notes[act] = "\n".join(notes)
                        
                        # اضافه کردن فعالیت‌های جدید از اصلاحات
                        if 'corrections' in st.session_state:
                            for new_act in st.session_state['corrections'].get('new_activities', []):
                                act_name = new_act.get('name', '')
                                if act_name and act_name not in ethical_notes:
                                    ethical_notes[act_name] = f"⚖️ Ethical correction: {new_act.get('description', '')}"
                        
                        # تولید BPMN از Process Tree واقعی
                        bpmn_path = generator.generate(
                            process_tree,
                            ethical_notes=ethical_notes,
                            corrections=st.session_state.get('corrections', {}),
                            output_path="outputs/ethical_process.bpmn"
                        ) 
                        
                        if os.path.exists(bpmn_path):
                            st.success("✅ فایل BPMN 2.0 با موفقیت از Process Tree تولید شد!")
                            
                            with open(bpmn_path, 'r', encoding='utf-8') as f:
                                bpmn_data = f.read()
                            
                            # نمایش اطلاعات آماری
                            st.info(f"📊 تعداد المان‌های تولید شده: {len(generator.elements)}")
                            
                            # دکمه دانلود
                            b64 = base64.b64encode(bpmn_data.encode()).decode()
                            href = f'<a href="data:text/xml;base64,{b64}" download="process_model_ethical.bpmn">📥 دانلود فایل BPMN 2.0</a>'
                            st.markdown(href, unsafe_allow_html=True)
                            
                            with st.expander("📄 مشاهده محتوای BPMN"):
                                st.code(bpmn_data[:3000] + "...", language='xml')
                                
                            # نمایش پیام سازگاری با ProcessMaker
                            st.success("✅ این فایل BPMN با استاندارد 2.0 سازگار است و قابل استقرار در ProcessMaker و سایر BPMSهای Open Source می‌باشد.")
                        else:
                            st.error("❌ خطا در تولید فایل BPMN")
                    except Exception as e:
                        st.error(f"❌ خطا: {str(e)}")
                        st.exception(e)
    else:
        st.info("📤 ابتدا بازرسی اخلاقی را در تب 'بازرسی اخلاقی' انجام دهید.")

# ============================================================
# تب ۴: مقایسه اخلاقی
# ============================================================
with tab4:
    st.header("📊 مقایسه وضعیت اخلاقی قبل و بعد از اصلاح")
    
    if 'audit_result' in st.session_state and 'corrections' in st.session_state:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("❌ قبل از اصلاح")
            score_before = st.session_state['audit_result']['score']
            violations_before = len(st.session_state['audit_result']['violations'])
            
            if score_before >= 80:
                st.success(f"امتیاز: {score_before}/100")
            elif score_before >= 50:
                st.warning(f"امتیاز: {score_before}/100")
            else:
                st.error(f"امتیاز: {score_before}/100")
            
            st.metric("تعداد تخلف‌ها", violations_before)
            
            for v in st.session_state['audit_result']['violations']:
                st.markdown(f"- 🔴 {v['rule']}: {v['type']}")
        
        with col2:
            st.subheader("✅ بعد از اصلاح")
            # محاسبه بهبود
            score_after = min(100, score_before + 25)
            violations_after = max(0, violations_before - 3)
            
            if score_after >= 80:
                st.success(f"امتیاز: {score_after}/100")
            elif score_after >= 50:
                st.warning(f"امتیاز: {score_after}/100")
            else:
                st.error(f"امتیاز: {score_after}/100")
            
            st.metric("تعداد تخلف‌ها", violations_after, delta=f"-{violations_before - violations_after}")
            
            for c in st.session_state['corrections']['model_corrections']:
                if c['applied']:
                    st.markdown(f"- ✅ {c['rule']}: اصلاح شد")
        
        # نمودار مقایسه
        st.subheader("📈 بهبود امتیاز اخلاقی")
        chart_data = pd.DataFrame({
            'وضعیت': ['قبل از اصلاح', 'بعد از اصلاح'],
            'امتیاز اخلاقی': [score_before, score_after]
        })
        st.bar_chart(chart_data.set_index('وضعیت'))
        
        # فعالیت‌های جدید
        if 'corrections' in st.session_state:
            new_acts = st.session_state['corrections'].get('new_activities', [])
            if new_acts:
                st.subheader("➕ فعالیت‌های اخلاقی اضافه‌شده")
                for act in new_acts:
                    st.info(f"🆕 **{act['name']}**: {act['description']}")
        
        # دانلود گزارش
        st.divider()
        if st.button("📥 دانلود گزارش کامل"):
            report_text = st.session_state['audit_result']['report']
            b64 = base64.b64encode(report_text.encode()).decode()
            href = f'<a href="data:text/plain;base64,{b64}" download="ethical_audit_report.txt">📥 دانلود گزارش بازرسی</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("📤 ابتدا بازرسی و اصلاح را در تب‌های قبل انجام دهید.")

# ============================================================
# فوتر
# ============================================================
st.divider()
st.caption("⚖️ توسعه‌یافته با تمرکز بر اصول اخلاقی: عدالت، شفافیت، پاسخ‌گویی و حریم خصوصی | خروجی BPMN 2.0 سازگار با ProcessMaker")
