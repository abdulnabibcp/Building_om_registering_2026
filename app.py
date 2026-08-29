import io
import sqlite3
import pandas as pd
import streamlit as st
import pdfkit

# --- 1. إعداد قاعدة البيانات ---
DB_NAME = "omni_realestate_v5.db"

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
            land_area REAL DEFAULT 0,
            built_area REAL DEFAULT 0,
            advertiser_type TEXT NOT NULL,
            advertiser_name TEXT,
            contact_phone TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- 2. دالة توليد تقرير PDF عربي عبر HTML & pdfkit ---
def generate_pdf_html(prop):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            color: #1e293b;
            direction: rtl;
            padding: 20px;
        }}
        .header {{
            background: #0f172a;
            color: #ffffff;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .section-title {{
            font-size: 14pt;
            font-weight: bold;
            color: #0f172a;
            border-right: 4px solid #2563eb;
            padding-right: 8px;
            margin: 15px 0 10px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }}
        th, td {{
            padding: 8px 10px;
            font-size: 10pt;
            text-align: right;
            border: 1px solid #cbd5e1;
        }}
        th {{
            background-color: #1e293b;
            color: #ffffff;
            width: 40%;
        }}
        .highlight {{
            background-color: #eff6ff;
            font-weight: bold;
        }}
    </style>
    </head>
    <body>
        <div class="header">
            <h2>🏢 تقرير تفصيلي للعقار والجدوى الاستثمارية</h2>
            <p>سلطنة عمان - نظام إدارة العقارات والتحليل المالي</p>
        </div>

        <div class="section-title">📌 البيانات الأساسية للمشروع</div>
        <table>
            <tr><th>معرف العقار (ID)</th><td>#{prop[0]}</td></tr>
            <tr><th>عنوان الإعلان / البناية</th><td>{prop[1]}</td></tr>
            <tr><th>المحافظة / المدينة</th><td>{prop[2]}</td></tr>
            <tr><th>المنطقة / الحي</th><td>{prop[3]}</td></tr>
            <tr><th>نوع العقار</th><td>{prop[4]}</td></tr>
            <tr><th>مساحة الأرض (م²)</th><td><strong>{prop[20]:,.2f} م²</strong></td></tr>
            <tr><th>مساحة البناء (م²)</th><td>{prop[21]:,.2f} م²</td></tr>
            <tr><th>عدد الشقق السكنية</th><td>{prop[18]} شقة</td></tr>
            <tr><th>عدد المحلات التجارية</th><td>{prop[19]} محل</td></tr>
            <tr><th>حالة الإعلان</th><td>{prop[17]}</td></tr>
        </table>

        <div class="section-title">💰 التحليل المالي وتفاصيل التكاليف (ر.ع.)</div>
        <table>
            <tr><th>سعر العقار الأساسي</th><td>{prop[5]:,.2f} ر.ع.</td></tr>
            <tr><th>رسوم وزارة الإسكان (3%)</th><td>{prop[6]:,.2f} ر.ع.</td></tr>
            <tr><th>رسوم الوساطة العقارية (1.5%)</th><td>{prop[7]:,.2f} ر.ع.</td></tr>
            <tr class="highlight"><th>إجمالي التكلفة الاستثمارية الشاملة</th><td>{prop[8]:,.2f} ر.ع.</td></tr>
            <tr><th>الدخل الشهري الإجمالي</th><td>{prop[9]:,.2f} ر.ع.</td></tr>
            <tr><th>الدخل السنوي الإجمالي</th><td>{prop[10]:,.2f} ر.ع.</td></tr>
            <tr><th>المصاريف التشغيلية الشهرية</th><td>{prop[11]:,.2f} ر.ع.</td></tr>
            <tr class="highlight"><th>صافي الدخل السنوي</th><td>{prop[13]:,.2f} ر.ع.</td></tr>
        </table>

        <div class="section-title">📊 مؤشرات الجدوى والعائد الاستثماري</div>
        <table>
            <tr><th>العائد الإجمالي (Gross ROI)</th><td>%{prop[14]:.2f}</td></tr>
            <tr class="highlight"><th>العائد الصافي على الاستثمار الشامل (Net ROI)</th><td>%{prop[15]:.2f}</td></tr>
            <tr><th>فترة استرداد رأس المال الصافية</th><td>{prop[16]:.1f} سنة</td></tr>
        </table>

        <div class="section-title">📞 بيانات المعلن والملاحظات</div>
        <table>
            <tr><th>صفة المعلن</th><td>{prop[22]}</td></tr>
            <tr><th>اسم المعلن / المكتب</th><td>{prop[23] if prop[23] else 'غير محدد'}</td></tr>
            <tr><th>رقم التواصل</th><td>{prop[24] if prop[24] else 'غير محدد'}</td></tr>
            <tr><th>ملاحظات إضافية</th><td>{prop[25] if prop[25] else 'لا توجد'}</td></tr>
        </table>
    </body>
    </html>
    """
    options = {
        'encoding': "UTF-8",
        'page-size': 'A4',
        'enable-local-file-access': None
    }
    pdf_bytes = pdfkit.from_string(html_content, False, options=options)
    return pdf_bytes

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
                try:
                    pdf_file = generate_pdf_html(data)
                    st.download_button(
                        label="📥 تحميل تقرير PDF الشامل",
                        data=pdf_file,
                        file_name=f"property_report_{prop_id}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error("يرجى التأكد من إضافة ملف packages.txt وبداخله wkhtmltopdf لتفعيل التصدير لـ PDF.")
            else:
                st.error("لم يتم العثور على عقار بهذا المعرف.")
    else:
        st.info("لا توجد عقارات مسجلة حالياً.")

# --- التبويب الثاني: إضافة عقار جديد ---
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
        monthly_op_cost = st.number_input("المصاريف التشغيلية الشهرية (ر.ع.)", min_value=0.0, step=50.0, value=100.0)

    with col2:
        advertiser_type = st.radio("صفة المعلن", ["المالك مباشرة", "مكتب عقاري / وسيط"], horizontal=True)
        advertiser_name = st.text_input("اسم المعلن / اسم المكتب العقاري")
        contact_phone = st.text_input("رقم التواصل / هاتف الواتساب")
        status = st.selectbox("حالة الإعلان", ["متاح", "تم البيع", "منتهي الإعلان"])
        
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

        c_larea, c_barea = st.columns(2)
        with c_larea:
            land_area = st.number_input("مساحة الأرض (م²)", min_value=0.0, step=10.0, value=600.0)
        with c_barea:
            built_area = st.number_input("مساحة البناء (م²)", min_value=0.0, step=10.0, value=800.0)

    notes = st.text_area("ملاحظات إضافية")

    housing_fee = price * 0.03       
    brokerage_fee = price * 0.015    
    total_investment = price + housing_fee + brokerage_fee

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

    st.subheader("📊 ملخص الجدوى الاستثمارية:")
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
                    land_area, built_area, advertiser_type, advertiser_name, contact_phone, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title, city, district, property_type, price, housing_fee, brokerage_fee, total_investment,
                monthly_rent, annual_rent, monthly_op_cost, annual_op_cost, net_annual_rent,
                gross_roi, net_roi, payback_years, status, apartments_count, shops_count,
                land_area, built_area, advertiser_type, advertiser_name, contact_phone, notes
            ))
            new_id = c.lastrowid
            conn.commit()
            conn.close()

            st.success(f"✅ تم حفظ العقار بنجاح تحت المعرف رقم (#{new_id})!")

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
            new_land_area = st.number_input("تعديل مساحة الأرض (م²):", value=float(prop[20]))
            new_built_area = st.number_input("تعديل مساحة البناء (م²):", value=float(prop[21]))
            new_adv_type = st.radio("تعديل صفة المعلن:", ["المالك مباشرة", "مكتب عقاري / وسيط"], index=0 if prop[22] == "المالك مباشرة" else 1, horizontal=True)
            new_adv_name = st.text_input("تعديل اسم المعلن / المكتب:", value=prop[23] if prop[23] else "")
            new_phone = st.text_input("تعديل رقم التواصل:", value=prop[24] if prop[24] else "")

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
                        apartments_count=?, shops_count=?, land_area=?, built_area=?, advertiser_type=?, advertiser_name=?, contact_phone=? 
                    WHERE id=?
                ''', (new_status, new_price, new_h_fee, new_b_fee, new_tot_inv, new_m_rent, ann_rent, net_ann, g_roi, n_roi, pb_years, new_apps, new_shops, new_land_area, new_built_area, new_adv_type, new_adv_name, new_phone, prop_id_edit))
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
    st.header("📈 حاسبة الجدوى والعائد الاستثماري الشامل")
    
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