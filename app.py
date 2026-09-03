import libsql_client
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. إعداد واجهة الصفحة
st.set_page_config(page_title="نظام إدارة المعاملات العقارية", layout="wide")

# 2. الاتصال بقاعدة البيانات عبر بروتوكول HTTP الصريح
@st.cache_resource
def get_db_client():
    url = st.secrets["TURSO_DATABASE_URL"]
    
    # تحويل الرابط إلى https إذا كان يبدأ بـ libsql:// لضمان التوافق مع السحاب
    if url.startswith("libsql://"):
        url = url.replace("libsql://", "https://")
        
    return libsql_client.create_client_sync(
        url=url,
        auth_token=st.secrets["TURSO_AUTH_TOKEN"]
    )

client = get_db_client()

# 3. إنشاء جدول المعاملات
def init_db():
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_name TEXT NOT NULL,
        property_type TEXT NOT NULL,
        monthly_rent REAL NOT NULL,
        gov_tax REAL NOT NULL,
        bring_emp_fee REAL NOT NULL,
        sell_emp_fee REAL NOT NULL,
        office_fee REAL NOT NULL,
        status TEXT DEFAULT 'Active'
    );
    """
    client.execute(create_table_sql)

init_db()

# باقي كود app.py كما هو...