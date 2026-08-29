import io
import sqlite3
import pandas as pd
import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# --- 1. إعداد قاعدة البيانات ---
DB_NAME = "omni_realestate_v4.db"

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
            housing_fee REAL NOT NULL,
            brokerage_fee REAL NOT NULL,
            total_investment REAL NOT NULL,
            monthly_rent REAL NOT NULL,
            annual_rent REAL NOT NULL,
            monthly_op_cost REAL DEFAULT 0,
            annual_op_cost REAL DEFAULT 0,
            net_annual_rent REAL NOT NULL,
            gross_roi REAL NOT NULL,
            net_roi REAL NOT NULL,
            payback_years REAL NOT NULL,
            status TEXT NOT NULL,
            apartments_count INTEGER DEFAULT 0,
            shops_count INTEGER DEFAULT 0,
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

    p.setFont("Helvetica-Bold", 15)
    p.drawRightString(width - 50, height - 40, format_arabic("تقرير تفصيلي للعقار وحساب التكاليف والجدوى - سلطنة عمان"))
    p.setLineWidth(1)
    p.line(50, height - 48, width - 50, height - 48)

    p.setFont("Helvetica", 10)
    y = height - 70

    fields = [
        ("معرف العقار (ID):", str(property_data[0])),
        ("عنوان الإعلان / البناية:", str(property_data[1])),
        ("المدينة / المحافظة:", str(property_data[2])),
        ("المنطقة / الحي:", str(property_data[3])),
        ("نوع العقار:", str(property_data[4])),
        ("صفة المعلن:", str(property_data[21])),
        ("اسم المعلن / المكتب:", str(property_data[22])),
        ("رقم التواصل:", str(property_data[23])),
        ("سعر العقار الأساسي (ر.ع.):", f"{property_data[5]:,.2f}"),
        ("رسوم وزارة الإسكان (3%):", f"{property_data[6]:,.2f}"),
        ("رسوم الوساطة العقارية (1.5%):", f"{property_data[7]:,.2f}"),
        ("إجمالي تكلفة الاستثمار (ر.ع.):", f"{property_data[8]:,.2f}"),
        ("الدخل الشهري الإجمالي (ر.ع.):", f"{property_data[9]:,.2f}"),
        ("الدخل السنوي الإجمالي (ر.ع.):", f"{property_data[10]:,.2f}"),
        ("المصاريف التشغيلية الشهرية (ر.ع.):", f"{property_data[11]:,.2f}"),
        ("صافي الدخل السنوي (ر.ع.):", f"{property_data[13]:,.2f}"),
        ("العائد الإجمالي (Gross ROI):", f"%{property_data[14]:.2f}"),
        ("العائد الصافي على الاستثمار الإجمالي (Net ROI):", f"%{property_data[15]:.2f}"),
        ("فترة استرداد رأس المال الصافية:", f"{property_data[16]:.1f} سنة"),
        ("حالة الإعلان:", str(property_data[17])),
        ("عدد الشقق السكنية:", str(property_data[18])),
        ("عدد المحلات التجارية:", str(property_data[19])),
        ("مساحة البناء (م²):", str(property_data[20])),
        ("ملاحظات إضافية:", str(property_data[24]))
    ]

    for label, val in fields:
        line_text = f"{format_arabic(val)} : {format_arabic(label)}"
        p.drawRightString(width - 50, y, line_text)
        y -= 19

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. واجهة Streamlit ---
st.set_page_config(page_title="نظام إدارة العقارات - سلطنة عمان", layout="wide")
st.title("🏢 نظام إدارة العقارات والجدوى الاستثمارية (سلطنة عمان)")

tabs = st.tabs(["📋 عرض واستعلام", "➕ إضافة إعلان جديد والجدوى", "✏️ تعديل / حذف / تغيير حالة", "📊 حاسبة الجدوى والرسوم السريعة"])

# --- التبويب الأول: العرض واستخراج PDF ---
with tabs[0]:
    st.header("قائمة العقارات المعروضة")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM properties", conn)
    conn.close()

    if not df.empty:
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
                    label="📥 تحميل تقرير PDF الشامل",
                    data=pdf_file,
                    file_name=f"property_report_{prop_id}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("لم يتم العثور على عقار بهذا المعرف.")
    else:
        st.info("لا توجد عقارات مسجلة حالياً.")

# --- التبويب الثاني: إضافة عقار وتوليد الجدوى التلقائي ---
with tabs[1]:
    st.header("إضافة عقار جديد وحساب التكاليف والرسوم تلقائياً")
    
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("عنوان الإعلان / اسم البناية")
        city = st.selectbox("المحافظة/المدينة", ["مسقط", "ظفار", "صحار", "نزوى", "بركاء", "أخرى"])
        district = st.text_input("المنطقة / الحي")
        
        property_type = st.selectbox(
            "نوع العقار", 
            ["بناية استثمارية (سكنية فقط)", "بناية تجارية (محلات وشقق)", "أرض استثمارية", "مجمع تجاري"]
        )
        
        price = st.number_input("سعر شراء العقار (ر.ع.)", min_value=1.0, step=1000.0, value=100000.0)
        monthly_rent = st.number_input("الدخل الشهري الإجمالي (ر.ع.)", min_value=0.0, step=100.0, value=1000.0)
        monthly_op_cost = st.number_input("المصاريف التشغيلية الشهرية (صيانة/إدارة) (ر.ع.)", min_value=0.0, step=50.0, value=100.0)

    with col2:
        advertiser_type = st.radio("صفة المعلن", ["المالك مباشرة", "مكتب عقاري / وسيط"], horizontal=True)
        advertiser_name = st.text_input("اسم المعلن / اسم المكتب العقاري")
        contact_phone = st.text_input("رقم التواصل / هاتف الواتساب")
        status = st.selectbox("حالة الإعلان", ["متاح", "تم البيع", "منتهي الإعلان"])
        
        # تخصيص حقول الشقق والمحلات حسب نوع البناية
        if property_type == "بناية استثمارية (سكنية فقط)":
            apartments_count = st.number_input("عدد الشقق السكنية", min_value=1, step=1, value=1)
            shops_count = 0
            st.info("ℹ️ البناية الاستثمارية السكنية تحتوي على شقق فقط.")
        elif property_type == "بناية تجارية (محلات وشقق)":
            c_app, c_shop = st.columns(2)
            with c_app:
                apartments_count = st.number_input("عدد الشقق", min_value=0, step=1, value=0)
            with c_shop:
                shops_count = st.number_input("عدد المحلات التجارية", min_value=1, step=1, value=1)
        else:
            apartments_count = st.number_input("عدد الشقق (إن وجد)", min_value=0, step=1, value=0)
            shops_count = st.number_input("عدد المحلات / الوحدات (إن وجد)", min_value=0, step=1, value=0)

        built_area = st.number_input("مساحة البناء (م²)", min_value=0.0, step=10.0)

    notes = st.text_area("ملاحظات إضافية")

    # --- الحسابات التلقائية للرسوم والجدوى الاستثمارية ---
    housing_fee = price * 0.03       # رسوم وزارة الإسكان 3%
    brokerage_fee = price * 0.015    # عمولة مكتب الوساطة 1.5%
    total_investment = price + housing_fee + brokerage_fee  # التكلفة الإجمالية الشاملة

    annual_rent = monthly_rent * 12
    annual_op_cost = monthly_op_cost * 12
    net_annual_rent = annual_rent - annual_op_cost

    gross_roi = (annual_rent / price * 100) if price > 0 else 0
    net_roi = (net_annual_rent / total_investment * 100) if total_investment > 0 else 0
    payback_years = (total_investment / net_annual_rent) if net_annual_rent > 0 else 0

    st.subheader("🏛️ تفاصيل الرسوم الاستثمارية (سلطنة عمان):")
    r1, r2, r3 = st.columns(3)
    r1.metric("رسوم نقل الملكية (الإسكان 3%)", f"{housing_fee:,.2f} ر.ع.")
    r2.metric("عمولة الوساطة العقارية (1.5%)", f"{brokerage_fee:,.2f} ر.ع.")
    r3.metric("إجمالي التكلفة الاستثمارية", f"{total_investment:,.2f} ر.ع.")

    st.subheader("📊 ملخص الجدوى الاستثمارية المحسوب تلقائياً:")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("الدخل السنوي الصافي", f"{net_annual_rent:,.2f} ر.ع.")
    m2.metric("العائد الإجمالي (Gross ROI)", f"{gross_roi:.2f}%")
    m3.metric("العائد الصافي الشامل (Net ROI)", f"{net_roi:.2f}%")
    m4.metric("فترة استرداد رأس المال", f"{payback_years:.1f} سنة")

    if st.button("💾 حفظ العقار في قاعدة البيانات", type="primary"):
        if title:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''
                INSERT INTO properties (
                    title, city, district, property_type, price, housing_fee, brokerage_fee, total_investment,
                    monthly_rent, annual_rent, monthly_op_cost, annual_op_cost, net_annual_rent, 
                    gross_roi, net_roi, payback_years, status, apartments_count, shops_count, 
                    built_area, advertiser_type, advertiser_name, contact_phone, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title, city, district, property_type, price, housing_fee, brokerage_fee, total_investment,
                monthly_rent, annual_rent, monthly_op_cost, annual_op_cost, net_annual_rent,
                gross_roi, net_roi, payback_years, status, apartments_count, shops_count,
                built_area, advertiser_type, advertiser_name, contact_phone, notes
            ))
            new_id = c.lastrowid
            conn.commit()
            conn.close()

            st.success(f"✅ تم حفظ العقار بنجاح تحت المعرف رقم (#{new_id})!")

            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT * FROM properties WHERE id = ?", (new_id,))
            new_prop_data = c.fetchone()
            conn.close()

            pdf_out = generate_pdf(new_prop_data)
            st.download_button(
                label="📥 تحميل تقرير PDF التفصيلي فوراً",
                data=pdf_out,
                file_name=f"property_report_{new_id}.pdf",
                mime="application/pdf"
            )

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
            new_status = st.selectbox("تغيير الحالة السريع:", ["متاح", "تم البيع", "منتهي الإعلان"], index=["متاح", "تم البيع", "منتهي الإعلان"].index(prop[17]))
            new_price = st.number_input("تعديل السعر (ر.ع.):", value=float(prop[5]))
            new_m_rent = st.number_input("تعديل الدخل الشهري (ر.ع.):", value=float(prop[9]))
            new_apps = st.number_input("تعديل عدد الشقق:", value=int(prop[18]))
            new_shops = st.number_input("تعديل عدد المحلات:", value=int(prop[19]))

        with col2:
            new_adv_type = st.radio("تعديل صفة المعلن:", ["المالك مباشرة", "مكتب عقاري / وسيط"], index=0 if prop[21] == "المالك مباشرة" else 1, horizontal=True)
            new_adv_name = st.text_input("تعديل اسم المعلن / المكتب:", value=prop[22] if prop[22] else "")
            new_phone = st.text_input("تعديل رقم التواصل:", value=prop[23] if prop[23] else "")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("💾 تحديث البيانات"):
                new_h_fee = new_price * 0.03
                new_b_fee = new_price * 0.015
                new_tot_inv = new_price + new_h_fee + new_b_fee

                ann_rent = new_m_rent * 12
                n_op = float(prop[11]) * 12
                net_ann = ann_rent - n_op
                g_roi = (ann_rent / new_price * 100) if new_price > 0 else 0
                n_roi = (net_ann / new_tot_inv * 100) if new_tot_inv > 0 else 0
                pb_years = (new_tot_inv / net_ann) if net_ann > 0 else 0

                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute('''
                    UPDATE properties 
                    SET status=?, price=?, housing_fee=?, brokerage_fee=?, total_investment=?,
                        monthly_rent=?, annual_rent=?, net_annual_rent=?, gross_roi=?, net_roi=?, payback_years=?,
                        apartments_count=?, shops_count=?, advertiser_type=?, advertiser_name=?, contact_phone=? 
                    WHERE id=?
                ''', (new_status, new_price, new_h_fee, new_b_fee, new_tot_inv, new_m_rent, ann_rent, net_ann, g_roi, n_roi, pb_years, new_apps, new_shops, new_adv_type, new_adv_name, new_phone, prop_id_edit))
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

# --- التبويب الرابع: حاسبة الجدوى السريعة ---
with tabs[3]:
    st.header("📈 حاسبة الجدوى والعائد الاستثماري الشامل للرسوم")
    
    col_calc1, col_calc2 = st.columns(2)
    with col_calc1:
        calc_price = st.number_input("سعر العقار (ر.ع.)", min_value=1.0, value=150000.0, key="c_price")
        calc_m_rent = st.number_input("الدخل الشهري الإجمالي (ر.ع.)", min_value=0.0, value=1200.0, key="c_m_rent")
        calc_m_op_cost = st.number_input("المصاريف التشغيلية الشهرية (ر.ع.)", min_value=0.0, value=100.0, key="c_m_op")

    with col_calc2:
        c_h_fee = calc_price * 0.03
        c_b_fee = calc_price * 0.015
        c_tot_inv = calc_price + c_h_fee + c_b_fee

        c_ann_rent = calc_m_rent * 12
        c_ann_op = calc_m_op_cost * 12
        c_net_rent = c_ann_rent - c_ann_op

        c_gross_roi = (c_ann_rent / calc_price) * 100
        c_net_roi = (c_net_rent / c_tot_inv) * 100
        c_payback = c_tot_inv / c_net_rent if c_net_rent > 0 else 0

        st.write(f"📌 **رسوم الإسكان (3%):** {c_h_fee:,.2f} ر.ع.")
        st.write(f"📌 **رسوم الوساطة (1.5%):** {c_b_fee:,.2f} ر.ع.")
        st.write(f"💵 **إجمالي التكلفة الحقيقية:** {c_tot_inv:,.2f} ر.ع.")
        st.divider()
        st.metric("صافي الدخل السنوي", f"{c_net_rent:,.2f} ر.ع.")
        st.metric("العائد الإجمالي (Gross ROI)", f"{c_gross_roi:.2f}%")
        st.metric("العائد الصافي على الاستثمار الإجمالي (Net ROI)", f"{c_net_roi:.2f}%")
        st.metric("فترة استرداد رأس المال الحقيقية", f"{c_payback:.1f} سنة")