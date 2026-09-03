import libsql_client
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. إعداد واجهة الصفحة
st.set_page_config(page_title="نظام إدارة المعاملات العقارية", layout="wide")


# 2. الاتصال بقاعدة بيانات Turso
@st.cache_resource
def get_db_client():
    return libsql_client.create_client_sync(
        url=st.secrets["TURSO_DATABASE_URL"],
        auth_token=st.secrets["TURSO_AUTH_TOKEN"],
    )


client = get_db_client()


# 3. إنشاء جدول المعاملات المحدد
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

# 4. الواجهة الرئيسية
st.title("🏢 نظام إدارة المكتب العقاري والمعاملات")

tab_add, tab_view, tab_dashboard = st.tabs(
    ["➕ إضافة معاملة جديدة", "📋 سجل المعاملات", "📊 لوحة التحليلات"]
)

# ---------------------------------------------------------
# تبويب 1: إضافة معاملة جديدة (CREATE)
# ---------------------------------------------------------
with tab_add:
    st.subheader("إدخال بيانات عقد / معاملة جديدة")

    with st.form("add_transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            tenant_name = st.text_input("اسم المستأجر / العميل")
            property_type = st.selectbox(
                "نوع العقار",
                ["شقة", "فيلا", "مكتب تجاري", "محل تجاري", "أرض", "مستودع"],
            )
            monthly_rent = st.number_input(
                "الإيجار الشهري ($)", min_value=0.0, step=50.0
            )
            gov_tax = st.number_input(
                "الضريبة / الرسوم الحكومية ($)", min_value=0.0, step=10.0
            )

        with col2:
            bring_emp_fee = st.number_input(
                "عمولة الموظف الجالب ($)", min_value=0.0, step=10.0
            )
            sell_emp_fee = st.number_input(
                "عمولة الموظف البائع ($)", min_value=0.0, step=10.0
            )
            office_fee = st.number_input(
                "عمولة المكتب ($)", min_value=0.0, step=10.0
            )
            status = st.selectbox(
                "حالة العقد", ["Active", "Pending", "Closed", "Cancelled"]
            )

        submit_btn = st.form_submit_button("حفظ المعاملة", type="primary")

        if submit_btn:
            if tenant_name.strip() != "":
                client.execute(
                    """
                    INSERT INTO transactions 
                    (tenant_name, property_type, monthly_rent, gov_tax, bring_emp_fee, sell_emp_fee, office_fee, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        tenant_name,
                        property_type,
                        monthly_rent,
                        gov_tax,
                        bring_emp_fee,
                        sell_emp_fee,
                        office_fee,
                        status,
                    ],
                )
                st.success(f"تمت إضافة معاملة {tenant_name} بنجاح!")
                st.rerun()
            else:
                st.error("يرجى إدخال اسم المستأجر.")

# ---------------------------------------------------------
# تبويب 2: عرض وتصفية المعاملات (READ)
# ---------------------------------------------------------
with tab_view:
    st.subheader("جدول المعاملات المسجلة")

    res = client.execute("SELECT * FROM transactions ORDER BY id DESC")
    if res.rows:
        df = pd.DataFrame(res.rows, columns=res.columns)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("لا توجد معاملات مسجلة حتى الآن.")

# ---------------------------------------------------------
# تبويب 3: لوحة التحليلات والرسوم البيانية (DASHBOARD)
# ---------------------------------------------------------
with tab_dashboard:
    st.subheader("مؤشرات الأداء والإيرادات")

    res = client.execute("SELECT * FROM transactions")
    if res.rows:
        df = pd.DataFrame(res.rows, columns=res.columns)

        # الملاحظات المالية المباشرة
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("إجمالي الإيجارات", f"{df['monthly_rent'].sum():,.2f} $")
        m2.metric("أرباح المكتب", f"{df['office_fee'].sum():,.2f} $")
        m3.metric(
            "عمولات الموظفين",
            f"{(df['bring_emp_fee'].sum() + df['sell_emp_fee'].sum()):,.2f} $",
        )
        m4.metric("الضرائب الحكومية", f"{df['gov_tax'].sum():,.2f} $")

        st.divider()

        # رسم بياني لتوزيع الإيجارات
        fig = px.bar(
            df,
            x="property_type",
            y="monthly_rent",
            color="status",
            title="توزيع الإيجارات حسب نوع العقار وحالة العقد",
            labels={
                "property_type": "نوع العقار",
                "monthly_rent": "الإيجار الشهري",
            },
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("قم بإضافة معاملات أولاً لعرض التحليلات.")