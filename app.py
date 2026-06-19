import streamlit as st
import pandas as pd
import plotly.express as px

from database.db import init_db


from modules.inventory import (
    add_product,
    get_products,
    increase_quantity,
    decrease_quantity,
    delete_product,
    get_inventory_summary,
    get_transaction_table_data,
    get_stock_status,
    get_inventory_health_score,
    get_ai_insights,
    get_stockout_forecasts,
    get_fast_moving_products,
    get_slow_moving_products,
    create_purchase_order,
    get_purchase_orders,
    update_purchase_order_status,
    generate_purchase_order_pdf,
)
from modules.auth import (
    require_role,
    get_current_role,
    logout_user,
)

from modules.gemini import (
    configure_gemini,
    get_inventory_summary as gemini_inventory_summary,
    get_reorder_advice,
    chat_with_inventory,
)
try:
    from modules.inventory import update_product
except ImportError:
    update_product = None

try:
    from modules.inventory import receive_purchase_order
except ImportError:
    receive_purchase_order = None
try:
    from modules.inventory import delete_purchase_order
except ImportError:
    delete_purchase_order = None

# Existing import for mark_purchase_order_sent
try:
    from modules.inventory import mark_purchase_order_sent
except ImportError:
    mark_purchase_order_sent = None

# New import for send_purchase_order_email
try:
    from modules.email_service import send_purchase_order_email
except ImportError:
    send_purchase_order_email = None
# Ensure database schema migrations run before any queries
init_db()
if not st.session_state.get("authenticated", False):
    st.switch_page("pages/login.py")
    st.stop()

st.set_page_config(
    page_title="InventoryIQ",
    page_icon="📦",
    layout="wide"
)
with st.sidebar:
    st.markdown(
        """
        <div style="
        padding:18px;
        border-radius:18px;
        background:linear-gradient(135deg,#08142b,#0f3d91,#00a651);
        color:white;
        margin-bottom:15px;">
        <h2 style="margin:0;">⚡ InventoryIQ Pro</h2>
        <p style="margin:4px 0 0 0;">AI-Powered Inventory Platform</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### 👤 User")

    username = st.session_state.get("username", "Unknown")
    role = get_current_role()

    st.write(f"👤 {username}")
    st.write(f"🏷️ {role}")

    st.divider()
    st.markdown("### 🤖 Gemini AI")
    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password",
        key="gemini_api_key",
    )

    if gemini_api_key:
        configure_gemini(gemini_api_key)
        st.sidebar.success("🟢 Gemini Connected")
    else:
        st.sidebar.warning("🟡 Gemini Not Configured")

    if st.button("🚪 Logout"):
        logout_user()
        st.switch_page("pages/login.py")
        st.stop()
st.markdown(
    """
    <style>
    .hero {
        padding: 40px;
        border-radius: 28px;
        background: linear-gradient(135deg,#08142b 0%, #0b2e6d 25%, #0f3d91 55%, #00a651 100%);
        border: 1px solid rgba(255,255,255,0.12);
        box-shadow: 0 0 50px rgba(31,95,191,0.35);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
        transform: skewX(-20deg);
    }
    .hero-title {
        font-size: 3.4rem;
        font-weight: 900;
        color: white;
        letter-spacing: 1px;
        text-shadow: 0 0 20px rgba(255,255,255,0.25);
    }
    .hero-subtitle {
        color: #dbeafe;
        font-size: 1.1rem;
        margin-top: 10px;
        letter-spacing: 0.5px;
    }
    .kpi-card {
        padding: 22px;
        border-radius: 22px;
        color: white;
        text-align: center;
        margin-bottom: 12px;
        border: 1px solid rgba(255,255,255,0.15);
        backdrop-filter: blur(12px);
        box-shadow: 0 12px 35px rgba(0,0,0,0.22);
        transition: all 0.35s ease;
        background: rgba(255,255,255,0.08);
        -webkit-backdrop-filter: blur(20px);
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow: 0 20px 45px rgba(31,95,191,0.35);
    }
    .kpi-card::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 22px;
        border: 1px solid rgba(255,255,255,0.15);
        pointer-events: none;
    }
    .kpi-title {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        opacity: 0.9;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        margin-top: 8px;
    }
    .kpi-blue {
        background: linear-gradient(135deg,#0b2e6d 0%, #0f3d91 35%, #1f5fbf 100%);
    }
    .kpi-green {
        background: linear-gradient(135deg,#006837 0%, #009245 45%, #00b050 100%);
    }
    .kpi-yellow {
        background: linear-gradient(135deg,#d89b00 0%, #f4b400 45%, #ffd54a 100%);
        color:#1f2937;
    }
    .kpi-red {
        background: linear-gradient(135deg,#b51218 0%, #d71920 45%, #ef4444 100%);
    }
    div[data-testid="stDataFrame"] {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }

    div[data-testid="stExpander"] {
        border-radius: 18px;
        border: 1px solid rgba(31,95,191,0.20);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 14px;
        padding: 10px 18px;
        background: rgba(15,61,145,0.08);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg,#0f3d91,#00a651) !important;
        color: white !important;
    }
    .ai-card {
        padding: 22px;
        border-radius: 22px;
        background: linear-gradient(135deg,#08142b 0%, #0f3d91 55%, #00a651 100%);
        color: white;
        border: 1px solid rgba(255,255,255,0.12);
        box-shadow: 0 12px 35px rgba(31,95,191,0.25);
        margin-top: 12px;
        margin-bottom: 20px;
    }
    .ai-card h3 {
        margin-top: 0;
        margin-bottom: 10px;
    }
    .ai-card ul {
        margin-bottom: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class='hero'>
        <div class='hero-title'>⚡ InventoryIQ</div>
        <div class='hero-subtitle'>Next‑Generation Inventory Intelligence • Analytics • Automation • AI Insights</div>
    </div>
    """,
    unsafe_allow_html=True,
)

products = get_products()
product_lookup = {p.id: p for p in products}
summary = get_inventory_summary()

stock_value = summary["total_value"]
health_score = get_inventory_health_score()

c1, c2, c3, c4 = st.columns(4)

low_stock_color = (
    "kpi-green"
    if summary["low_stock"] == 0
    else "kpi-yellow" if summary["low_stock"] < 5 else "kpi-red"
)

health_color = (
    "kpi-green"
    if health_score >= 90
    else "kpi-yellow" if health_score >= 70 else "kpi-red"
)

with c1:
    st.markdown(
        f"""
        <div class='kpi-card kpi-blue'>
            <div class='kpi-title'>Products</div>
            <div class='kpi-value'>{summary['total_products']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class='kpi-card kpi-green'>
            <div class='kpi-title'>Inventory Value</div>
            <div class='kpi-value'>₹{stock_value:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class='kpi-card {low_stock_color}'>
            <div class='kpi-title'>Low Stock</div>
            <div class='kpi-value'>{summary['low_stock']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        f"""
        <div class='kpi-card {health_color}'>
            <div class='kpi-title'>Health Score</div>
            <div class='kpi-value'>{health_score}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Quick Actions Section
st.markdown("### ⚡ Quick Actions")

qa1, qa2, qa3, qa4 = st.columns(4)

with qa1:
    st.button("➕ Add Product", use_container_width=True)

with qa2:
    st.button("📄 Create PO", use_container_width=True)

with qa3:
    st.button("📥 Export", use_container_width=True)

with qa4:
    st.button("🤖 AI Copilot", use_container_width=True)

# Low Stock Alerts Section
low_stock_products = [
    p for p in products
    if (getattr(p, "quantity", 0) or 0) <= (p.reorder_level or 0)
]

if low_stock_products:
    st.warning(f"⚠️ {len(low_stock_products)} product(s) require attention")

    with st.expander("View Low Stock Alerts", expanded=True):
        alert_rows = []

        for p in low_stock_products:
            alert_rows.append({
                "Product": p.name,
                "SKU": p.sku,
                "Current Stock": getattr(p, "quantity", 0) or 0,
                "Reorder Level": p.reorder_level or 0,
                "Status": get_stock_status(p),
            })

        st.dataframe(
            pd.DataFrame(alert_rows),
            width='stretch',
            hide_index=True
        )

        st.markdown("### 🚚 Supplier Contacts")

        for p in low_stock_products:
            supplier_name = getattr(p, "supplier_name", None)

            with st.container():
                st.markdown(
                    f"**{p.name}** • Supplier: **{supplier_name or 'Not Assigned'}**"
                )

                contact_col1, contact_col2 = st.columns(2)

                with contact_col1:
                    supplier_email = getattr(p, "supplier_email", "") or "Not Provided"
                    st.text_input(
                        f"Email ({p.sku})",
                        value=supplier_email,
                        disabled=True,
                        key=f"email_{p.id}"
                    )

                with contact_col2:
                    supplier_phone = getattr(p, "supplier_phone", "") or "Not Provided"
                    st.text_input(
                        f"Phone ({p.sku})",
                        value=supplier_phone,
                        disabled=True,
                        key=f"phone_{p.id}"
                    )

                action_col1, action_col2, action_col3 = st.columns(3)

                with action_col1:
                    if supplier_email and supplier_email != "Not Provided":
                        st.link_button(
                            "📧 Email Supplier",
                            f"mailto:{supplier_email}",
                            use_container_width=True,
                        )

                with action_col2:
                    if supplier_phone and supplier_phone != "Not Provided":
                        st.link_button(
                            "📞 Call Supplier",
                            f"tel:{supplier_phone}",
                            use_container_width=True,
                        )

                with action_col3:
                    if require_role("Admin", "Manager"):
                        if st.button("📄 Create PO", key=f"create_po_{p.id}"):
                            reorder_qty = max(
                                (p.reorder_level or 1) - (getattr(p, "quantity", 0) or 0),
                                p.reorder_level or 1,
                            )

                            create_purchase_order(
                                product_id=p.id,
                                quantity=reorder_qty,
                            )

                            st.success(f"Purchase Order created for {p.name}")
                            st.rerun()
                    else:
                        st.caption("🔒")

                st.divider()

if products:
    st.success(f"Inventory database active • {len(products)} product(s) loaded")

    insights = get_ai_insights()

    if insights:
        st.markdown(
            f"""
            <div class='ai-card'>
                <h3>🤖 AI Command Center</h3>
                <ul>
                    {''.join(f'<li>{item}</li>' for item in insights)}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

catalog_tab, inventory_tab, history_tab, analytics_tab, purchase_orders_tab, suppliers_tab, ai_tab = st.tabs(
    [
        "📦 Product Catalog",
        "📋 Inventory View",
        "📜 Transaction History",
        "📊 Analytics",
        "📄 Purchase Orders",
        "🚚 Suppliers",
        "🤖 AI Assistant"
    ]
)

with catalog_tab:
    st.subheader("📦 Product Master")
    st.caption("Create inventory SKUs and maintain product records.")

    sku = st.text_input("SKU")
    name = st.text_input("Product Name")

    category = st.selectbox(
        "Category",
        [
            "Paint",
            "Primer",
            "Packaging",
            "Raw Material"
        ]
    )
    
    unit_price = st.number_input(
        "Unit Price",
        min_value=0.0
    )

    reorder_level = st.number_input(
        "Reorder Level",
        min_value=0
    )

    st.markdown("### 🚚 Supplier Information")

    supplier_col1, supplier_col2 = st.columns(2)

    with supplier_col1:
        supplier_name = st.text_input("Supplier Name")
        supplier_email = st.text_input("Supplier Email")

    with supplier_col2:
        supplier_phone = st.text_input("Supplier Phone")
        lead_time_days = st.number_input(
            "Lead Time (Days)",
            min_value=0,
            value=0
        )

    if require_role("Admin", "Manager"):
        if st.button("Add Product"):
            result = add_product(
                sku=sku,
                name=name,
                category=category,
                unit_price=unit_price,
                reorder_level=reorder_level,
                supplier_name=supplier_name,
                supplier_email=supplier_email,
                supplier_phone=supplier_phone,
                lead_time_days=lead_time_days,
            )

            if result:
                st.success("✅ Product Added Successfully")
                st.rerun()
            else:
                st.error("❌ SKU already exists. Please use a unique SKU.")
    else:
        st.info("🔒 Only Admins and Managers can add products.")

with inventory_tab:
    st.subheader("📋 Inventory Registry")

    st.markdown("### 🔍 Search & Filter")

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        search_term = st.text_input(
            "Search Product",
            placeholder="Search by SKU, name, or category"
        )

    with filter_col2:
        category_filter = st.selectbox(
            "Category Filter",
            ["All"] + sorted(list(set(p.category for p in products if p.category)))
        )

    with filter_col3:
        low_stock_only = st.checkbox("Show Low Stock Only")

    filtered_products = products

    if search_term:
        search_lower = search_term.lower()
        filtered_products = [
            p for p in filtered_products
            if search_lower in (p.name or "").lower()
            or search_lower in (p.sku or "").lower()
            or search_lower in (p.category or "").lower()
        ]

    if category_filter != "All":
        filtered_products = [
            p for p in filtered_products
            if p.category == category_filter
        ]

    if low_stock_only:
        filtered_products = [
            p for p in filtered_products
            if (getattr(p, "quantity", 0) or 0) <= (p.reorder_level or 0)
        ]

    rows = []

    for p in filtered_products:
        qty = getattr(p, "quantity", 0) or 0

        rows.append({
            "SKU": p.sku,
            "Name": p.name,
            "Category": p.category,
            "Supplier": getattr(p, "supplier_name", "") or "-",
            "Lead Time": getattr(p, "lead_time_days", 0) or 0,
            "Quantity": qty,
            "Status": get_stock_status(p),
            "Unit Price (₹)": p.unit_price,
            "Stock Value (₹)": qty * (p.unit_price or 0),
            "Reorder Level": p.reorder_level,
        })

    if rows:
        inventory_df = pd.DataFrame(rows)

        st.dataframe(
            inventory_df,
            width='stretch',
            hide_index=True
        )

        st.download_button(
            label="📥 Export Inventory CSV",
            data=inventory_df.to_csv(index=False).encode("utf-8"),
            file_name="inventory_export.csv",
            mime="text/csv",
        )

        st.divider()
        st.subheader("➕➖ Stock Management")

        st.caption("Enter any quantity and add or remove stock instantly.")

        for p in filtered_products:
            qty = getattr(p, "quantity", 0) or 0

            col1, col2, col3, col4, col5, col6, col7 = st.columns([4, 2, 2, 1, 1, 1, 1])

            with col1:
                st.write(f"**{p.name}** ({p.sku})")

            with col2:
                st.write(f"Stock: {qty}")

            with col3:
                custom_qty = st.number_input(
                    "Quantity",
                    min_value=0.01,
                    value=10.0,
                    step=0.01,
                    format="%.2f",
                    key=f"qty_{p.id}"
                ) 

            with col4:
                if require_role("Admin", "Manager"):
                    if st.button("➕ Add", key=f"add_{p.id}"):
                        increase_quantity(p.id, custom_qty)
                        st.rerun()
                else:
                    st.caption("🔒")

            with col5:
                if require_role("Admin", "Manager"):
                    if st.button("➖ Remove", key=f"remove_{p.id}"):
                        decrease_quantity(p.id, custom_qty)
                        st.rerun()
                else:
                    st.caption("🔒")

            with col6:
                if require_role("Admin"):
                    if st.button("🗑️ SKU", key=f"delete_{p.id}"):
                        if qty > 0:
                            st.error("Cannot delete a SKU with stock remaining. Reduce stock to zero first.")
                        else:
                            delete_product(p.id)
                            st.success(f"Deleted SKU: {p.sku}")
                            st.rerun()
                else:
                    st.caption("Admin Only")

            with col7:
                if update_product is None:
                    st.caption("Edit N/A")
                elif require_role("Admin", "Manager"):
                    with st.popover("✏️ Edit", use_container_width=True):
                        edit_name = st.text_input("Product Name", value=p.name, key=f"edit_name_{p.id}")
                        edit_category = st.text_input("Category", value=p.category, key=f"edit_category_{p.id}")
                        edit_price = st.number_input("Unit Price", min_value=0.0, value=float(p.unit_price or 0), key=f"edit_price_{p.id}")
                        edit_reorder = st.number_input("Reorder Level", min_value=0, value=int(p.reorder_level or 0), key=f"edit_reorder_{p.id}")
                        edit_supplier = st.text_input("Supplier Name", value=getattr(p, "supplier_name", "") or "", key=f"edit_supplier_{p.id}")
                        edit_email = st.text_input("Supplier Email", value=getattr(p, "supplier_email", "") or "", key=f"edit_email_{p.id}")
                        edit_phone = st.text_input("Supplier Phone", value=getattr(p, "supplier_phone", "") or "", key=f"edit_phone_{p.id}")
                        edit_lead_time = st.number_input("Lead Time (Days)", min_value=0, value=int(getattr(p, "lead_time_days", 0) or 0), key=f"edit_lead_{p.id}")

                        if st.button("💾 Save", key=f"save_edit_{p.id}"):
                            update_product(
                                product_id=p.id,
                                name=edit_name,
                                category=edit_category,
                                unit_price=edit_price,
                                reorder_level=edit_reorder,
                                supplier_name=edit_supplier,
                                supplier_email=edit_email,
                                supplier_phone=edit_phone,
                                lead_time_days=edit_lead_time,
                            )
                            st.success("Product updated successfully")
                            st.rerun()
                else:
                    st.caption("🔒")
    else:
        st.info("No products added yet.")


with history_tab:
    st.subheader("📜 Transaction History")
    st.caption("Track every inventory movement with a complete audit trail.")

    transactions = get_transaction_table_data(200)

    if transactions:
        transactions_df = pd.DataFrame(transactions)

        st.dataframe(
            transactions_df,
            width='stretch',
            hide_index=True
        )

        st.download_button(
            label="📥 Export Transactions CSV",
            data=transactions_df.to_csv(index=False).encode("utf-8"),
            file_name="transactions_export.csv",
            mime="text/csv",
        )
    else:
        st.info("No transactions recorded yet.")

with analytics_tab:
    st.subheader("📊 Inventory Analytics")
    st.caption("Business intelligence and inventory performance insights.")

    if products:
        total_quantity = sum((getattr(p, "quantity", 0) or 0) for p in products)

        most_valuable_product = max(
            products,
            key=lambda p: ((getattr(p, "quantity", 0) or 0) * (p.unit_price or 0)),
            default=None,
        )

        avg_stock = round(total_quantity / len(products), 2)

        a1, a2, a3 = st.columns(3)

        with a1:
            st.markdown(
                f"""
                <div class='kpi-card kpi-blue'>
                    <div class='kpi-title'>Total Quantity</div>
                    <div class='kpi-value'>{total_quantity:,.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with a2:
            if most_valuable_product:
                inventory_value = (
                    (getattr(most_valuable_product, "quantity", 0) or 0)
                    * (most_valuable_product.unit_price or 0)
                )

                st.markdown(
                    f"""
                    <div class='kpi-card kpi-green'>
                        <div class='kpi-title'>Most Valuable Product</div>
                        <div class='kpi-value' style='font-size:1.4rem'>{most_valuable_product.name}</div>
                        <div style='margin-top:8px'>₹{inventory_value:,.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with a3:
            st.markdown(
                f"""
                <div class='kpi-card kpi-blue'>
                    <div class='kpi-title'>Average Stock</div>
                    <div class='kpi-value'>{avg_stock:,.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        chart_rows = []

        for p in products:
            chart_rows.append({
                "Product": p.name,
                "Inventory Value": (
                    (getattr(p, "quantity", 0) or 0)
                    * (p.unit_price or 0)
                ),
            })

        chart_df = pd.DataFrame(chart_rows)

        if not chart_df.empty:
            st.markdown("### 📈 Product Performance")
            fig_products = px.bar(
                chart_df,
                x="Product",
                y="Inventory Value",
                title="Inventory Value by Product"
            )
            fig_products.update_traces(marker_color="#0f3d91")
            fig_products.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_products, width='stretch')

        category_rows = []

        categories = sorted(set(p.category for p in products if p.category))

        for category in categories:
            category_value = sum(
                ((getattr(p, "quantity", 0) or 0) * (p.unit_price or 0))
                for p in products
                if p.category == category
            )

            category_rows.append({
                "Category": category,
                "Inventory Value": category_value,
            }) 

        category_df = pd.DataFrame(category_rows)

        if not category_df.empty:
            st.markdown("### 📊 Category Analysis")
            fig_categories = px.bar(
                category_df,
                x="Category",
                y="Inventory Value",
                title="Inventory Value by Category"
            )
            fig_categories.update_traces(marker_color="#00a651")
            fig_categories.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_categories, width='stretch')

            st.markdown("### 🥧 Inventory Value Distribution")

            fig_donut = px.pie(
                category_df,
                names="Category",
                values="Inventory Value",
                hole=0.65,
            )

            fig_donut.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(fig_donut, width='stretch')

        top_products = sorted(
            products,
            key=lambda p: (
                (getattr(p, "quantity", 0) or 0)
                * (p.unit_price or 0)
            ),
            reverse=True,
        )[:5]

        if top_products:
            st.markdown("### 🏆 Top Products")

            top_rows = []

            for rank, product in enumerate(top_products, start=1):
                top_rows.append({
                    "Rank": rank,
                    "Product": product.name,
                    "Category": product.category,
                    "Inventory Value": (
                        (getattr(product, "quantity", 0) or 0)
                        * (product.unit_price or 0)
                    ),
                })

            st.dataframe(pd.DataFrame(top_rows), width='stretch', hide_index=True)

        st.markdown("### 🔮 Inventory Forecast")

        forecast_rows = get_stockout_forecasts()

        if forecast_rows:
            forecast_df = pd.DataFrame([
                {
                    "Product": row["product"],
                    "Current Stock": row["current_stock"],
                    "Daily Consumption": row["daily_consumption"],
                    "Days Remaining": (
                        row["days_remaining"]
                        if row["days_remaining"] is not None
                        else None
                    ),
                    "Risk": row["risk"],
                }
                for row in forecast_rows
            ])

            st.dataframe(
                forecast_df,
                width='stretch',
                hide_index=True,
            )

            critical_items = [
                f for f in forecast_rows
                if f["risk"] in ["🔴 Critical", "🟠 High"]
            ]

            if critical_items:
                st.warning(
                    f"⚠️ {len(critical_items)} product(s) are forecasted to reach critical stock levels soon."
                )
            else:
                st.success(
                    "✅ No immediate stockout risks detected based on current consumption patterns."
                )

        st.markdown("### 🔥 Fast Moving Products")

        fast_products = get_fast_moving_products()

        if fast_products:
            st.dataframe(
                pd.DataFrame(fast_products),
                width='stretch',
                hide_index=True,
            )
        else:
            st.info("No outbound inventory movement recorded yet.")

        st.markdown("### 🐢 Slow Moving Products")

        slow_products = get_slow_moving_products()

        if slow_products:
            st.dataframe(
                pd.DataFrame(slow_products),
                width='stretch',
                hide_index=True,
            )

        st.markdown("### 🚚 Reorder Center")

        reorder_rows = []

        for p in products:
            qty = getattr(p, "quantity", 0) or 0
            reorder_level = getattr(p, "reorder_level", 0) or 0

            if qty <= reorder_level:
                reorder_rows.append({
                    "Product": p.name,
                    "Current Stock": qty,
                    "Reorder Level": reorder_level,
                    "Recommended Order Qty": max(reorder_level - qty, reorder_level or 1),
                })

        if reorder_rows:
            st.dataframe(
                pd.DataFrame(reorder_rows),
                width='stretch',
                hide_index=True,
            )
        else:
            st.success("✅ No products currently require reordering.")

        st.markdown("### 📊 ABC Inventory Classification")

        abc_rows = []

        ranked_products = sorted(
            products,
            key=lambda p: ((getattr(p, "quantity", 0) or 0) * (p.unit_price or 0)),
            reverse=True,
        )

        for idx, product in enumerate(ranked_products):
            if idx < max(1, int(len(ranked_products) * 0.2)):
                category = "A"
            elif idx < max(1, int(len(ranked_products) * 0.5)):
                category = "B"
            else:
                category = "C"

            abc_rows.append({
                "Product": product.name,
                "ABC Class": category,
                "Inventory Value": (getattr(product, "quantity", 0) or 0) * (product.unit_price or 0),
            })

        st.dataframe(
            pd.DataFrame(abc_rows),
            width='stretch',
            hide_index=True,
        )


with purchase_orders_tab:
    st.subheader("📄 Purchase Orders")
    st.caption("Track supplier orders and procurement workflow.")

    st.markdown("### ➕ Create Purchase Order")

    if products:
        po_product = st.selectbox(
            "Product",
            products,
            format_func=lambda p: f"{p.name} ({p.sku})",
            key="manual_po_product",
        )

        po_quantity = st.number_input(
            "PO Quantity",
            min_value=1.0,
            value=float(max(getattr(po_product, "reorder_level", 1) or 1, 1)),
            step=1.0,
            key="manual_po_qty",
        )

        if require_role("Admin", "Manager"):
            if st.button("📄 Create Purchase Order", key="manual_create_po"):
                create_purchase_order(
                    product_id=po_product.id,
                    quantity=po_quantity,
                )
                st.success(f"Purchase Order created for {po_product.name}")
                st.rerun()
        else:
            st.info("🔒 Only Admins and Managers can create purchase orders.")

    st.divider()

    purchase_orders = get_purchase_orders()

    total_pos = len(purchase_orders)
    draft_count = sum(1 for po in purchase_orders if po.status == "Draft")
    sent_count = sum(1 for po in purchase_orders if po.status == "Sent")
    delivered_count = sum(1 for po in purchase_orders if po.status == "Delivered")

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("📄 Total POs", total_pos)
    k2.metric("🟡 Draft", draft_count)
    k3.metric("🔵 Sent", sent_count)
    k4.metric("🟢 Delivered", delivered_count)

    if purchase_orders:
        po_rows = []

        for po in purchase_orders:
            product = product_lookup.get(po.product_id)
            product_name = product.name if product else f"Product #{po.product_id}"

            unit_price = getattr(po, "unit_price", 0) or 0
            po_value = (po.quantity or 0) * unit_price

            status_display = {
                "Draft": "🟡 Draft",
                "Sent": "🔵 Sent",
                "Delivered": "🟢 Delivered",
                "Cancelled": "🔴 Cancelled",
            }.get(po.status, po.status)

            created_date = getattr(po, "created_at", None)
            age_days = "-"

            if created_date:
                try:
                    age_days = (pd.Timestamp.now() - pd.Timestamp(created_date)).days
                except Exception:
                    age_days = "-"

            po_rows.append({
                "PO Number": po.po_number,
                "Product": product_name,
                "Supplier": po.supplier_name,
                "Supplier Email": getattr(po, "supplier_email", "-") or "-",
                "Supplier Phone": getattr(po, "supplier_phone", "-") or "-",
                "Lead Time (Days)": getattr(po, "lead_time_days", 0) or 0,
                "Quantity": po.quantity,
                "Unit Price (₹)": unit_price,
                "PO Value (₹)": po_value,
                "Status": status_display,
                "Created": po.created_at,
                "Age (Days)": age_days,
            })

        st.dataframe(
            pd.DataFrame(po_rows),
            width='stretch',
            hide_index=True,
        )

        st.markdown("### 🚚 Supplier Contacts")

        for po in purchase_orders:
            supplier_email = getattr(po, "supplier_email", "") or ""
            supplier_phone = getattr(po, "supplier_phone", "") or ""

            c1, c2, c3 = st.columns([4, 2, 2])

            with c1:
                st.write(f"**{po.po_number}** • {po.supplier_name or 'No Supplier'}")

            with c2:
                if supplier_email:
                    st.link_button(
                        "📧 Email",
                        f"mailto:{supplier_email}",
                        use_container_width=True,
                    )

            with c3:
                if supplier_phone:
                    st.link_button(
                        "📞 Call",
                        f"tel:{supplier_phone}",
                        use_container_width=True,
                    )

        overdue = []

        for po in purchase_orders:
            created_date = getattr(po, "created_at", None)
            if created_date and po.status not in ["Delivered", "Cancelled"]:
                try:
                    age = (pd.Timestamp.now() - pd.Timestamp(created_date)).days
                    if age > 14:
                        overdue.append(po.po_number)
                except Exception:
                    pass

        if overdue:
            st.error(f"🔴 Overdue Purchase Orders: {', '.join(overdue)}")

        st.markdown("### Update Purchase Order Status")

        for po in purchase_orders:
            product = product_lookup.get(po.product_id)
            product_name = product.name if product else f"Product #{po.product_id}"

            col1, col2, col3, col4, col5, col6, col7 = st.columns([4, 3, 2, 2, 2, 2, 2])

            with col1:
                st.write(f"**{po.po_number}** • {product_name}")

            with col2:
                new_status = st.selectbox(
                    "Status",
                    ["Draft", "Sent", "Delivered", "Cancelled"],
                    index=["Draft", "Sent", "Delivered", "Cancelled"].index(po.status)
                    if po.status in ["Draft", "Sent", "Delivered", "Cancelled"] else 0,
                    key=f"po_status_{po.id}",
                )

            with col3:
                if st.button("💾 Update", key=f"update_po_{po.id}"):
                    update_purchase_order_status(po.id, new_status)
                    st.success(f"Updated {po.po_number}")
                    st.rerun()
            with col4:
                if require_role("Admin", "Manager") and receive_purchase_order and po.status == "Sent":
                    if st.button("📦 Receive", key=f"receive_po_{po.id}"):
                        receive_purchase_order(po.id)
                        st.success(f"Inventory received for {po.po_number}")
                        st.rerun()
            with col5:
                if require_role("Admin") and delete_purchase_order and po.status in ["Draft", "Cancelled"]:
                    if st.button("🗑️ Delete", key=f"delete_po_{po.id}"):
                        delete_purchase_order(po.id)
                        st.success(f"Deleted {po.po_number}")
                        st.rerun()
            with col6:
                supplier_email = getattr(po, "supplier_email", "") or ""

                if supplier_email:
                    subject = f"Purchase Order {po.po_number}"

                    body = (
                        f"Dear {po.supplier_name or 'Supplier'},%0D%0A%0D%0A"
                        f"Please process the following purchase order:%0D%0A%0D%0A"
                        f"PO Number: {po.po_number}%0D%0A"
                        f"Quantity: {po.quantity}%0D%0A%0D%0A"
                        f"Regards,%0D%0AInventoryIQ"
                    )

                    if send_purchase_order_email:
                        if st.button("📨 Send Direct", key=f"send_direct_{po.id}"):
                            try:
                                send_purchase_order_email(
                                    recipient_email=supplier_email,
                                    po_number=po.po_number,
                                    supplier_name=po.supplier_name,
                                    quantity=po.quantity,
                                )
                                st.success(f"Purchase Order {po.po_number} sent successfully")
                            except Exception as e:
                                st.error(f"Email failed: {e}")
                    else:
                        st.link_button(
                            "📧 Send PO",
                            f"mailto:{supplier_email}?subject={subject}&body={body}",
                            use_container_width=True,
                        )

                    if mark_purchase_order_sent:
                        if st.button("📨 Mark Sent", key=f"mark_sent_{po.id}"):
                            mark_purchase_order_sent(po.id)
                            st.success(f"{po.po_number} marked as Sent")
                            st.rerun()
            with col7:
                pdf_path = generate_purchase_order_pdf(po.id)

                if pdf_path:
                    try:
                        with open(pdf_path, "rb") as pdf_file:
                            st.download_button(
                                label="📄 PDF",
                                data=pdf_file.read(),
                                file_name=f"{po.po_number}.pdf",
                                mime="application/pdf",
                                key=f"pdf_{po.id}",
                                use_container_width=True,
                            )
                    except Exception:
                        st.caption("PDF Error")
    else:
        st.info("No purchase orders created yet.")


with suppliers_tab:
    st.subheader("🚚 Supplier Directory")
    st.caption("Centralized supplier information across all products.")

    supplier_map = {}

    for p in products:
        supplier_name = getattr(p, "supplier_name", None)

        if not supplier_name:
            continue

        if supplier_name not in supplier_map:
            supplier_map[supplier_name] = {
                "Supplier": supplier_name,
                "Products": [],
                "Email": getattr(p, "supplier_email", "") or "-",
                "Phone": getattr(p, "supplier_phone", "") or "-",
                "Lead Time (Days)": getattr(p, "lead_time_days", 0) or 0,
            }

        supplier_map[supplier_name]["Products"].append(p.name)

    if supplier_map:
        supplier_rows = []

        for supplier in supplier_map.values():
            supplier_rows.append({
                "Supplier": supplier["Supplier"],
                "Products": ", ".join(supplier["Products"]),
                "Email": supplier["Email"],
                "Phone": supplier["Phone"],
                "Lead Time (Days)": supplier["Lead Time (Days)"],
            })

        st.dataframe(
            pd.DataFrame(supplier_rows),
            width='stretch',
            hide_index=True,
        )
    else:
        st.info("No supplier information available yet.")


# AI Assistant Tab
with ai_tab:
    st.subheader("🤖 InventoryIQ AI Copilot")
    st.markdown(
        """ 
        <div class='ai-card'>
        <h2>🤖 InventoryIQ Copilot</h2>
        <p>Ask questions about inventory, suppliers, purchase orders, forecasting and stock risks.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Ask questions about inventory, suppliers, stock risks and replenishment.")

    # --- Persistent Chat History ---
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.markdown("### 💬 Conversation")

    if st.session_state.chat_history:
        for message in st.session_state.chat_history:
            role = message.get("role", "assistant")

            if role == "user":
                st.markdown(
                    f"""
                    <div style='padding:12px;border-radius:14px;background:rgba(15,61,145,0.15);margin-bottom:10px;'>
                    <strong>🧑 You</strong><br>{message['content']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style='padding:12px;border-radius:14px;background:rgba(0,166,81,0.12);margin-bottom:14px;'>
                    <strong>🤖 InventoryIQ</strong><br>{message['content']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

    if not st.session_state.get("gemini_api_key"):
        st.info("Enter a Gemini API key in the sidebar to use AI features.")
    else:
        ai_col1, ai_col2 = st.columns(2)

        with ai_col1:
            if st.button("📊 Inventory Health Summary"):
                with st.spinner("Analyzing inventory..."):
                    summary_text = gemini_inventory_summary(
                        [
                            {
                                "name": p.name,
                                "sku": p.sku,
                                "quantity": getattr(p, "quantity", 0),
                                "reorder_level": p.reorder_level,
                            }
                            for p in products
                        ],
                        get_purchase_orders(),
                    )
                    st.markdown(summary_text)

        with ai_col2:
            if st.button("🚚 Reorder Advice"):
                with st.spinner("Generating recommendations..."):
                    advice = get_reorder_advice(
                        [
                            {
                                "name": p.name,
                                "quantity": getattr(p, "quantity", 0),
                                "reorder_level": p.reorder_level,
                            }
                            for p in products
                        ]
                    )
                    st.markdown(advice)

        st.markdown("### 🤖 Smart Purchase Orders")
        st.caption("AI-assisted reorder recommendations based on current stock and reorder levels.")

        smart_po_candidates = []

        for p in products:
            current_stock = getattr(p, "quantity", 0) or 0
            reorder_level = getattr(p, "reorder_level", 0) or 0

            if current_stock <= reorder_level:
                recommended_qty = max(
                    (reorder_level * 2) - current_stock,
                    reorder_level or 1,
                )

                smart_po_candidates.append(
                    {
                        "product": p,
                        "current_stock": current_stock,
                        "reorder_level": reorder_level,
                        "recommended_qty": recommended_qty,
                    }
                )

        if smart_po_candidates:
            smart_rows = []

            for item in smart_po_candidates:
                smart_rows.append(
                    {
                        "Product": item["product"].name,
                        "Current Stock": item["current_stock"],
                        "Reorder Level": item["reorder_level"],
                        "Recommended PO Qty": item["recommended_qty"],
                    }
                )

            st.dataframe(
                pd.DataFrame(smart_rows),
                width='stretch',
                hide_index=True,
            )

            if require_role("Admin", "Manager"):
                for item in smart_po_candidates:
                    product = item["product"]

                    if st.button(
                        f"🛒 Create Smart PO • {product.name}",
                        key=f"smart_po_{product.id}",
                    ):
                        create_purchase_order(
                            product_id=product.id,
                            quantity=item["recommended_qty"],
                        )
                        st.success(
                            f"Smart Purchase Order created for {product.name}"
                        )
                        st.rerun()
            else:
                st.info("🔒 Only Admins and Managers can create Smart Purchase Orders.")
        else:
            st.success("✅ No products currently require AI-assisted reordering.")

        st.markdown("### 💬 Ask InventoryIQ")

        question = st.text_area(
            "Question",
            placeholder="Which products need reordering? What inventory is at risk?",
        )

        if st.button("Ask AI") and question:
            with st.spinner("Thinking..."):
                inventory_context = {
                    "products": [
                        {
                            "name": p.name,
                            "sku": p.sku,
                            "quantity": getattr(p, "quantity", 0),
                            "reorder_level": p.reorder_level,
                        }
                        for p in products
                    ],
                    "purchase_orders": len(get_purchase_orders()),
                }

                st.session_state.chat_history.append(
                    {
                        "role": "user",
                        "content": question,
                    }
                )
                response = chat_with_inventory(question, inventory_context)
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": response,
                    }
                )
                st.rerun()
