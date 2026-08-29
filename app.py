import io
import sqlite3
import pandas as pd
import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# --- 1. إعداد قاعدة البيانات ---
DB_NAME = "omni_realestate.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            city TEXT NOT NULL,
            district TEXT NOT NULL,
            property_type TEXT NOT NULL,
            price REAL NOT NULL,
            annual_rent REAL NOT NULL,
            status TEXT NOT NULL,
            units_count INTEGER,
            built_area REAL,
            advertiser_type TEXT NOT NULL,
            advertiser_name TEXT,
            contact_phone TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- 2. دالة معالجة النصوص العربية وتوليد PDF ---
def format_arabic(text):
    if not text:
        return ""
    reshaped_text = arabic_reshaper.reshape(str(text))
    return get_display(reshaped_text)

def generate_pdf(property_data):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawRightString(width - 50, height - 50, format_arabic("تقرير تفصيلي للعقار الاستثماري"))
    p.setLineWidth(1)
    p.line(50, height - 60, width - 50, height - 60)

    p.setFont("Helvetica", 11)
    y = height - 90
    
    # حساب الجدوى
    price = property_data[5]
    annual_rent = property_data[6]
    roi = (annual_rent / price * 100) if price > 0 else 0
    payback = (price / annual_rent) if annual_rent > 0 else 0

    fields = [
        ("معرف العقار (ID):", str(property_data[0])),
        ("عنوان الإعلان:", str(property_data[1])),
        ("المدينة / المحافظة:", str(property_data[2])),
        ("المنطقة / الحي:", str(property_data[3])),
        ("نوع العقار:", str(property_data[4])),
        ("صفة المعلن:", str(property_data[10])),
        ("اسم المعلن / المكتب:", str(property_data[11])),
        ("رقم التواصل:", str(property_data[12])),
        ("السعر المطلوب (ر.ع.):", f"{property_data[5]:,.2f}"),
        ("الدخل السنوي المتوقع (ر.ع.):", f"{property_data[6]:,.2f}"),
        ("العائد الاستثماري السنوي (ROI):", f"%{roi:.2f}"),
        ("فترة استرداد رأس المال:", f"{payback:.1f} سنة"),
        ("حالة الإعلان:", str(property_data[7])),
        ("عدد الوحدات / المحلات:", str(property_data[8])),
        ("مساحة البناء (م²):", str(property_data[9])),
        ("ملاحظات إضافية:", str(property_data[13]))
    ]

    for label, val in fields:
        line_text = f"{format_arabic(val)} : {format_arabic(label)}"
        p.drawRightString(width - 50, y, line_text)
        y -= 22

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. واجهة Streamlit ---
st.set_page_config(page_title="إدارة العقارات - السوق العماني", layout="wide")
st.title("🏢 نظام إدارة وتعديل العقارات الاستثمارية (عُمان)")

tabs = st.tabs(["📋 عرض واستعلام", "➕ إضافة إعلان جديد", "✏️ تعديل / حذف / تغيير حالة", "📊 حاسبة الجدوى"])

# --- التبويب الأول: العرض واستخراج PDF ---
with tabs[0]:
    st.header("قائمة العقارات المعروضة")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM properties", conn)
    conn.close()

    if not df.empty:
        # فلاتر البحث
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            status_filter = st.selectbox("تصفية حسب الحالة:", ["الكل"] + list(df['status'].unique()))
        with col_f2:
            adv_filter = st.selectbox("تصفية حسب صفة المعلن:", ["الكل"] + list(df['advertiser_type'].unique()))

        df_display = df.copy()
        if status_filter != "الكل":
            df_display = df_display[df_display['status'] == status_filter]
        if adv_filter != "الكل":
            df_display = df_display[df_display['advertiser_type'] == adv_filter]

        st.dataframe(df_display, use_container_width=True)

        st.subheader("📄 طباعة تقرير PDF لعقار محدد")
        prop_id = st.number_input("أدخل رقم معرف العقار (ID) لطباعة التقرير:", min_value=1, step=1)
        if st.button("توليد تقرير PDF"):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT * FROM properties WHERE id = ?", (prop_id,))
            data = c.fetchone()
            conn.close()

            if data:
                pdf_file = generate_pdf(data)
                st.download_button(
                    label="📥 تحميل تقرير PDF",
                    data=pdf_file,
                    file_name=f"property_report_{prop_id}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("لم يتم العثور على عقار بهذا المعرف.")
    else:
        st.info("لا توجد عقارات مسجلة حالياً.")

# --- التبويب الثاني: إضافة إعلان جديد ---
with tabs[1]:
    st.header("إضافة عقار جديد")
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("عنوان الإعلان / اسم البناية")
            city = st.selectbox("المحافظة/المدينة", ["مسقط", "ظفار", "صحار", "نزوى", "بركاء", "أخرى"])
            district = st.text_input("المنطقة / الحي")
            property_type = st.selectbox("نوع العقار", ["بناية تجارية", "بناية سكنية تجارية", "أرض استثمارية", "مجمع تجاري"])
            price = st.number_input("السعر المطلوب (ر.ع.)", min_value=0.0, step=1000.0)
            annual_rent = st.number_input("الدخل السنوي المتوقع (ر.ع.)", min_value=0.0, step=100.0)

        with col2:
            advertiser_type = st.radio("صفة المعلن", ["المالك مباشرة", "مكتب عقاري / وسيط"], horizontal=True)
            advertiser_name = st.text_input("اسم المعلن / اسم المكتب العقاري")
            contact_phone = st.text_input("رقم التواصل / هاتف الواتساب")
            status = st.selectbox("حالة الإعلان", ["متاح", "تم البيع", "منتهي الإعلان"])
            units_count = st.number_input("عدد المحلات / الشقق", min_value=0, step=1)
            built_area = st.number_input("مساحة البناء (م²)", min_value=0.0, step=10.0)
        
        notes = st.text_area("ملاحظات إضافية")

        submitted = st.form_submit_button("حفظ العقار")
        if submitted and title:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''
                INSERT INTO properties (
                    title, city, district, property_type, price, annual_rent, status, 
                    units_count, built_area, advertiser_type, advertiser_name, contact_phone, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title, city, district, property_type, price, annual_rent, status, 
                units_count, built_area, advertiser_type, advertiser_name, contact_phone, notes
            ))
            conn.commit()
            conn.close()
            st.success("تم حفظ العقار بنجاح!")
            st.rerun()

# --- التبويب الثالث: التعديل والحذف وتغيير الحالة ---
with tabs[2]:
    st.header("تعديل أو مسح إعلان")
    prop_id_edit = st.number_input("أدخل رقم (ID) العقار للتعديل أو الحذف:", min_value=1, step=1, key="edit_id")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM properties WHERE id = ?", (prop_id_edit,))
    prop = c.fetchone()
    conn.close()

    if prop:
        st.write(f"**العقار المحدد:** {prop[1]} ({prop[2]} - {prop[3]})")
        
        col1, col2 = st.columns(2)
        with col1:
            new_status = st.selectbox("تغيير الحالة السريع:", ["متاح", "تم البيع", "منتهي الإعلان"], index=["متاح", "تم البيع", "منتهي الإعلان"].index(prop[7]))
            new_price = st.number_input("تعديل السعر (ر.ع.):", value=float(prop[5]))
            new_rent = st.number_input("تعديل الدخل السنوي (ر.ع.):", value=float(prop[6]))

        with col2:
            new_adv_type = st.radio("تعديل صفة المعلن:", ["المالك مباشرة", "مكتب عقاري / وسيط"], index=0 if prop[10] == "المالك مباشرة" else 1, horizontal=True)
            new_adv_name = st.text_input("تعديل اسم المعلن / المكتب:", value=prop[11] if prop[11] else "")
            new_phone = st.text_input("تعديل رقم التواصل:", value=prop[12] if prop[12] else "")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("💾 تحديث البيانات"):
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute('''
                    UPDATE properties 
                    SET status=?, price=?, annual_rent=?, advertiser_type=?, advertiser_name=?, contact_phone=? 
                    WHERE id=?
                ''', (new_status, new_price, new_rent, new_adv_type, new_adv_name, new_phone, prop_id_edit))
                conn.commit()
                conn.close()
                st.success("تم تحديث البيانات بنجاح!")
                st.rerun()

        with col_b2:
            if st.button("🗑️ حذف الإعلان نهائياً", type="primary"):
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("DELETE FROM properties WHERE id=?", (prop_id_edit,))
                conn.commit()
                conn.close()
                st.warning("تم حذف العقار من قاعدة البيانات.")
                st.rerun()
    else:
        st.info("أدخل رقم ID صحيح لفتح خيارات التعديل.")

# --- التبويب الرابع: حاسبة الجدوى الاستثمارية ---
with tabs[3]:
    st.header("📈 حاسبة الجدوى والعائد الاستثماري للبنايات")
    
    col_calc1, col_calc2 = st.columns(2)
    with col_calc1:
        calc_price = st.number_input("سعر الشراء الإجمالي (ر.ع.)", min_value=1.0, value=150000.0)
        calc_rent = st.number_input("إجمالي الدخل السنوي (ر.ع.)", min_value=0.0, value=13500.0)
        calc_op_cost = st.number_input("المصاريف التشغيلية السنوية (صيانة، إدارة) (ر.ع.)", min_value=0.0, value=1000.0)

    with col_calc2:
        net_rent = calc_rent - calc_op_cost
        gross_roi = (calc_rent / calc_price) * 100
        net_roi = (net_rent / calc_price) * 100
        payback_period = calc_price / net_rent if net_rent > 0 else 0

        st.metric("العائد الإجمالي (Gross ROI)", f"{gross_roi:.2f}%")
        st.metric("العائد الصافي (Net ROI)", f"{net_roi:.2f}%")
        st.metric("فترة استرداد رأس المال الصافية", f"{payback_period:.1f} سنة")