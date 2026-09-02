import streamlit as st
import sqlite3
import pandas as pd

# 1. إعداد قاعدة البيانات
def init_db():
    conn = sqlite3.connect('real_estate.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            type TEXT,
            category TEXT,
            price REAL,
            address TEXT,
            owner_name TEXT,
            owner_phone TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 2. إعداد واجهة Streamlit
st.set_page_config(page_title="إدارة المكتب العقاري", layout="wide")
st.title("🏢 نظام إدارة المكتب العقاري")

menu = ["🔍 عرض وبحث العقارات", "➕ إضافة عقار جديد", "📊 ملخص عقارات المكتب"]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

# --- 1. إضافة عقار جديد ---
if choice == "➕ إضافة عقار جديد":
    st.subheader("إدخال بيانات عقار جديد")
    
    with st.form("property_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("عنوان العقار (مثال: شقة للبيع في حي الصفا)")
            type_opt = st.selectbox("نوع العملية", ["بيع", "تأجير", "شراء"])
            category_opt = st.selectbox("نوع العقار", ["شقة", "مبنى", "محل", "أرض", "فيلا"])
            price = st.number_input("السعر / الإيجار (بالريال/العملة المحلية)", min_value=0.0, step=1000.0)
        
        with col2:
            address = st.text_input("الموقع / العنوان")
            owner_name = st.text_input("اسم المالك / العميل")
            owner_phone = st.text_input("رقم هاتف المالك")
            notes = st.text_area("ملاحظات إضافية (المساحة، عدد الغرف، إلخ)")
            
        submit = st.form_submit_button("حفظ العقار")
        
        if submit:
            if title and owner_name:
                conn = sqlite3.connect('real_estate.db')
                c = conn.cursor()
                c.execute('''
                    INSERT INTO properties (title, type, category, price, address, owner_name, owner_phone, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (title, type_opt, category_opt, price, address, owner_name, owner_phone, notes))
                conn.commit()
                conn.close()
                st.success("✅ تم حفظ العقار بنجاح!")
            else:
                st.error("⚠️ يرجى تعبئة عنوان العقار واسم المالك على الأقل.")

# --- 2. عرض وبحث العقارات ---
elif choice == "🔍 عرض وبحث العقارات":
    st.subheader("قائمة العقارات والبحث السريع")
    
    conn = sqlite3.connect('real_estate.db')
    df = pd.read_sql_query("SELECT * FROM properties", conn)
    conn.close()
    
    if not df.empty:
        # شريط البحث والفلترة
        col1, col2, col3 = st.columns(3)
        with col1:
            search_term = st.text_input("🔎 بحث (بالعنوان، المالك، الملاحظات):")
        with col2:
            filter_type = st.multiselect("فلترة حسب العملية:", options=df["type"].unique(), default=df["type"].unique())
        with col3:
            filter_cat = st.multiselect("فلترة حسب النوع:", options=df["category"].unique(), default=df["category"].unique())
            
        # تطبيق الفلاتر
        filtered_df = df[(df["type"].isin(filter_type)) & (df["category"].isin(filter_cat))]
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df['title'].str.contains(search_term, case=False, na=False) |
                filtered_df['owner_name'].str.contains(search_term, case=False, na=False) |
                filtered_df['address'].str.contains(search_term, case=False, na=False) |
                filtered_df['notes'].str.contains(search_term, case=False, na=False)
            ]
            
        # تغيير أسماء الأعمدة للعرض بالعربية
        display_df = filtered_df.rename(columns={
            "id": "المعرف",
            "title": "العنوان",
            "type": "العملية",
            "category": "النوع",
            "price": "السعر",
            "address": "الموقع",
            "owner_name": "المالك",
            "owner_phone": "الهاتف",
            "notes": "الملاحظات"
        })
        
        st.dataframe(display_df, use_container_width=True)
        st.caption(f"عدد النتائج: {len(display_df)}")
    else:
        st.info("لا توجد عقارات مسجلة حتى الآن.")

# --- 3. ملخص أحصائي ---
elif choice == "📊 ملخص عقارات المكتب":
    st.subheader("إحصائيات العقارات المسجلة")
    conn = sqlite3.connect('real_estate.db')
    df = pd.read_sql_query("SELECT * FROM properties", conn)
    conn.close()
    
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("إجمالي العقارات", len(df))
        col2.metric("عقارات للبيع", len(df[df['type'] == 'بيع']))
        col3.metric("عقارات للتأجير", len(df[df['type'] == 'تأجير']))
    else:
        st.info("لا توجد بيانات كافية لإنشاء الملخص.")