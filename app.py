import streamlit as st
from urllib.parse import quote_plus
import pandas as pd
import shap
import lime
import lime.lime_tabular
import numpy as np
import os
import requests
from sklearn.ensemble import RandomForestClassifier
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

st.set_page_config(page_title="XAI Storefront", layout="wide")

# ─── MongoDB Connection ───────────────────────────────────────────────────────
MONGO_URI = (
    "mongodb+srv://Jack:" + quote_plus("Jack0@")
    + "@cluster0.pnqkj3b.mongodb.net/?appName=Cluster0"
)

@st.cache_resource
def get_collection():
    client = MongoClient(MONGO_URI)
    return client["xai_store"]["products"]

collection = get_collection()

def load_manual_products():
    try:
        products = list(collection.find({}, {"_id": 1, "name": 1, "price": 1,
                                             "image": 1, "description": 1}))
        for p in products:
            p["_id"] = str(p["_id"])
        return products
    except Exception as e:
        st.error(f"Could not load products: {e}")
        return []

def save_product(name, price, image, description):
    try:
        collection.insert_one({
            "name":        name,
            "price":       price,
            "image":       image,
            "description": description,
            "created_at":  datetime.utcnow()
        })
        return True
    except Exception as e:
        st.error(f"Could not save product: {e}")
        return False

# ─── Session state defaults ───────────────────────────────────────────────────
for key, val in [('page', 'login'), ('selected_product', None), ('xai_enabled', False)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ─── ML data & model ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(os.path.join(BASE_DIR, "fast_amazon.csv"))
    except FileNotFoundError:
        st.warning("fast_amazon.csv not found. Using fallback synthetic dataset.")
        df = pd.DataFrame({
            'overall':    np.random.choice([3.0, 4.0, 5.0], size=500),
            'reviewText': ["Loved it!" for _ in range(500)]
        })

    dataset = pd.DataFrame()
    dataset['Product_Rating']    = df['overall'].fillna(4.0)
    dataset['Review_Word_Count'] = (
        df.get('reviewText', pd.Series([""] * len(df)))
        .fillna("").apply(lambda x: len(str(x).split()))
    )
    np.random.seed(42)
    dataset['Price_USD']        = np.random.uniform(10, 500, size=len(dataset)).round(2)
    dataset['Discount_Percent'] = np.random.choice([0, 5, 10, 15], size=len(dataset))
    rec_logic = (dataset['Product_Rating'] >= 4) & (dataset['Discount_Percent'] >= 5)
    dataset['Will_Recommend']   = rec_logic.astype(int)
    dataset = dataset.dropna()

    if dataset.empty:
        dataset = pd.DataFrame({
            'Product_Rating':    np.random.choice([3.0, 4.0, 5.0], size=20),
            'Review_Word_Count': np.random.randint(5, 100, size=20),
            'Price_USD':         np.random.uniform(10, 500, size=20).round(2),
            'Discount_Percent':  np.random.choice([0, 5, 10, 15], size=20),
            'Will_Recommend':    np.random.choice([0, 1], size=20)
        })

    X = dataset.drop('Will_Recommend', axis=1)
    y = dataset['Will_Recommend']
    model = RandomForestClassifier(random_state=42, max_depth=5)
    model.fit(X, y)
    return dataset, model, X

dataset, model, X_train = load_data()


# ═══════════════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM — Single source of truth for all styling
# ═══════════════════════════════════════════════════════════════════════════════

def inject_design_system():
    """Inject the complete, centralized CSS design system. Called once at render."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {
        --bg-primary:       #060b16;
        --bg-surface:       #0d1527;
        --bg-surface-alt:   #111c34;
        --bg-elevated:      #172646;
        --accent:           #2563eb;
        --accent-light:     #3b82f6;
        --accent-cyan:      #0891b2;
        --accent-emerald:   #059669;
        --text-primary:     #f8fafc;
        --text-secondary:   #cbd5e1;
        --text-muted:       #64748b;
        --border-subtle:    rgba(255,255,255,0.06);
        --border-accent:    rgba(59,130,246,0.3);
        --shadow-card:      0 8px 30px rgba(0,0,0,0.4);
        --shadow-hover:     0 20px 40px rgba(37,99,235,0.25);
        --gap-section:      30px;
        --radius-card:      16px;
        --radius-badge:     30px;
        --ease:             0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }

    /* ── Global Styles ─────────────────────────────────────────────────── */
    .stApp {
        background: var(--bg-primary);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, sans-serif;
    }
    html, body, [class*="css"],
    .stTextInput input, .stNumberInput input, .stSelectbox select,
    .stMarkdown, .stMetric, .stRadio label, .stCheckbox label,
    button, textarea {
        font-family: 'Inter', -apple-system, sans-serif !important;
    }
    
    .block-container { 
        padding-top: 2.5rem !important; 
        padding-bottom: 3rem !important;
        max-width: 1200px !important;
    }

    /* ── Custom Spacing ───────────────────────────────────────────────── */
    .section-spacer { 
        height: var(--gap-section); 
        margin: 0;
        padding: 0;
    }

    /* ── Navbar ───────────────────────────────────────────────────────── */
    .navbar-brand {
        font-size: 26px; 
        font-weight: 800; 
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, var(--accent-light), var(--accent-cyan));
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
    }
    .navbar-divider {
        border: none;
        border-top: 1px solid var(--border-subtle);
        margin: 15px 0 var(--gap-section) 0;
    }

    /* ── Mode Badge ──────────────────────────────────────────────────── */
    .mode-badge {
        display: inline-block; 
        font-size: 11px; 
        font-weight: 700;
        letter-spacing: 1.2px; 
        text-transform: uppercase;
        padding: 6px 18px; 
        border-radius: 20px;
    }
    .text-center { text-align: center; }
    .mode-badge.experimental {
        background: rgba(5, 150, 105, 0.15); 
        color: #34d399;
        border: 1px solid rgba(5, 150, 105, 0.3);
    }
    .mode-badge.control {
        background: rgba(100, 116, 139, 0.15); 
        color: #94a3b8;
        border: 1px solid rgba(100, 116, 139, 0.3);
    }

    /* ── Section Headers ─────────────────────────────────────────────── */
    .section-header {
        font-size: 22px; 
        font-weight: 700;
        border-left: 4px solid var(--accent-light);
        padding: 6px 0 6px 16px;
        margin-bottom: 20px;
        letter-spacing: -0.3px;
        color: var(--text-primary);
        background: linear-gradient(90deg, rgba(59,130,246,0.08) 0%, transparent 80%);
        border-radius: 0 8px 8px 0;
    }
    .section-header .header-chip {
        font-size: 10px; 
        font-weight: 700; 
        letter-spacing: 1px;
        text-transform: uppercase; 
        padding: 3px 12px;
        border-radius: 12px; 
        margin-left: 12px; 
        vertical-align: middle;
        background: rgba(59,130,246,0.15); 
        color: var(--accent-light);
        border: 1px solid rgba(59,130,246,0.2);
    }

    /* ── Custom Cards (Self-Contained) ────────────────────────────────── */
    .styled-card {
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-card);
        padding: 20px;
        transition: transform var(--ease), box-shadow var(--ease), border-color var(--ease);
        display: flex;
        flex-direction: column;
        height: 380px;
        justify-content: space-between;
        box-shadow: var(--shadow-card);
        margin-bottom: 15px;
    }
    .styled-card:hover {
        transform: translateY(-6px);
        box-shadow: var(--shadow-hover);
        border-color: var(--border-accent);
    }
    .card-img-container {
        width: 100%;
        height: 180px;
        border-radius: 10px;
        overflow: hidden;
        background: #020617;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .card-img-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform var(--ease);
    }
    .styled-card:hover .card-img-container img {
        transform: scale(1.05);
    }
    .card-info {
        margin-top: 12px;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
    .card-title {
        font-size: 17px; 
        font-weight: 700; 
        color: var(--text-primary);
        margin: 0 0 6px 0; 
        line-height: 1.3;
    }
    .price-badge {
        display: inline-block;
        align-self: flex-start;
        background: rgba(59, 130, 246, 0.1);
        color: var(--accent-light);
        padding: 4px 12px;
        border-radius: var(--radius-badge);
        font-weight: 700; 
        font-size: 14px;
        margin-bottom: 8px;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    .card-desc {
        font-size: 13px; 
        color: var(--text-secondary);
        line-height: 1.45;
        margin: 0;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    /* ── Recommended Section Style ───────────────────────────────────── */
    .rec-section-wrapper {
        background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(8,145,178,0.03) 100%);
        border: 1px solid rgba(59,130,246,0.12);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: var(--gap-section);
    }

    /* ── Buttons Customization ────────────────────────────────────────── */
    .stButton > button {
        border-radius: 10px; 
        font-weight: 600;
        font-family: 'Inter', sans-serif !important;
        transition: all var(--ease) !important;
        background-color: var(--bg-surface-alt);
        color: var(--text-primary);
        border: 1px solid var(--border-subtle);
    }
    .stButton > button:hover {
        background: var(--accent-light) !important;
        color: white !important;
        border-color: var(--accent-light) !important;
        box-shadow: 0 4px 12px rgba(59,130,246,0.3);
        transform: translateY(-1px);
    }

    /* Primary actions / views */
    div[data-testid="column"] button {
        margin-top: 5px;
    }

    /* ── Login Styling ────────────────────────────────────────────────── */
    .login-container {
        max-width: 420px;
        margin: 0 auto;
        padding: 40px;
        background: rgba(13, 21, 39, 0.7);
        border-radius: 24px;
        border: 1px solid var(--border-subtle);
        backdrop-filter: blur(20px);
        box-shadow: var(--shadow-card);
    }
    .login-title {
        font-size: 30px; 
        font-weight: 800;
        text-align: center;
        background: linear-gradient(135deg, var(--accent-light), var(--accent-cyan));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    .login-subtitle {
        font-size: 14px;
        color: var(--text-muted);
        text-align: center;
        margin-bottom: 30px;
    }

    /* ── SHAP Feature Importance Bars ────────────────────────────────── */
    .shap-bar-wrap { margin-bottom: 18px; }
    .shap-label {
        font-size: 13px; 
        font-weight: 600; 
        color: var(--text-secondary);
        margin-bottom: 6px; 
        display: flex; 
        justify-content: space-between;
    }
    .shap-label .val { color: var(--text-primary); font-weight: 700; }
    .shap-track {
        width: 100%; 
        background: #0f172a; 
        height: 10px;
        border-radius: 6px; 
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .shap-fill {
        height: 100%; 
        border-radius: 6px; 
        transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* ── LIME Feature Importance Bars ────────────────────────────────── */
    .lime-bar-wrap { margin-bottom: 18px; }
    .lime-label {
        font-size: 13px; 
        font-weight: 600; 
        color: var(--text-secondary);
        margin-bottom: 6px; 
        display: flex; 
        justify-content: space-between;
    }
    .lime-label .val { color: var(--text-primary); font-weight: 700; }
    .lime-track {
        width: 100%; 
        background: #0f172a; 
        height: 10px;
        border-radius: 6px; 
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .lime-fill {
        height: 100%; 
        border-radius: 6px; 
        transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* ── Expander ────────────────────────────────────────────────────── */
    details[data-testid="stExpander"] {
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-card) !important;
        box-shadow: var(--shadow-card);
    }

    /* ── Analysis Page ───────────────────────────────────────────────── */
    .analysis-container {
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: 20px;
        padding: 30px;
        box-shadow: var(--shadow-card);
    }
    .analysis-product-title {
        font-size: 26px;
        font-weight: 800;
        margin-bottom: 12px;
    }

    /* ── Footer ──────────────────────────────────────────────────────── */
    .site-footer {
        text-align: center; 
        padding: 40px 0 20px 0;
        margin-top: 50px;
        border-top: 1px solid var(--border-subtle);
        color: var(--text-muted); 
        font-size: 13px;
    }
    .site-footer a { 
        color: var(--accent-light); 
        text-decoration: none; 
        font-weight: 500;
    }
    .site-footer a:hover { 
        text-decoration: underline; 
    }

    </style>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  UI COMPONENTS — Small, focused, reusable
# ═══════════════════════════════════════════════════════════════════════════════

def section_header(icon, title, chip=None):
    """Render a styled section header with accent left-border and optional chip."""
    chip_html = f"<span class='header-chip'>{chip}</span>" if chip else ""
    st.markdown(
        f"<div class='section-header'>{icon}&ensp;{title}{chip_html}</div>",
        unsafe_allow_html=True
    )

def section_spacer():
    """Insert consistent vertical spacing between sections."""
    st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True)


def show_navbar():
    """Top navigation bar with brand, XAI toggle, and functional Profile/Cart buttons."""
    nav_left, nav_mid, nav_right = st.columns([1, 2, 1])

    with nav_left:
        st.markdown(
            "<div class='navbar-brand'>🧠 XAI Store</div>",
            unsafe_allow_html=True
        )

    with nav_mid:
        mode_label = "Experimental" if st.session_state.xai_enabled else "Control"
        mode_class = "experimental" if st.session_state.xai_enabled else "control"
        st.markdown(
            f"<div class='text-center'>"
            f"<span class='mode-badge {mode_class}'>{mode_label} Mode</span>"
            f"</div>",
            unsafe_allow_html=True
        )
        xai_toggle = st.toggle(
            "Enable XAI Explanations",
            value=st.session_state.xai_enabled,
            key="xai_toggle"
        )
        if xai_toggle != st.session_state.xai_enabled:
            st.session_state.xai_enabled = xai_toggle
            st.rerun()

    with nav_right:
        btn_cols = st.columns(3)
        with btn_cols[0]:
            if st.button("📊 Stats", key="nav_stats", use_container_width=True):
                st.session_state.page = 'system_stats'
                st.rerun()
        with btn_cols[1]:
            if st.button("👤 Profile", key="nav_profile", use_container_width=True):
                st.toast("Profile page coming soon!", icon="👤")
        with btn_cols[2]:
            if st.button("🛒 Cart", key="nav_cart", use_container_width=True):
                st.toast("Cart functionality coming soon!", icon="🛒")

    st.markdown("<hr class='navbar-divider'>", unsafe_allow_html=True)


def styled_card(img, name, price, description="", btn_key=None):
    """Render a product inside a styled card with consistent border, shadow, and hover."""
    short_desc = ""
    if description:
        short = (description[:80] + "…") if len(description) > 80 else description
        short_desc = f"<div class='card-desc'>{short}</div>"

    html_content = (
        f"<div class='styled-card'>"
        f"<div class='card-img-container'><img src='{img}' alt='{name}'></div>"
        f"<div class='card-info'>"
        f"<div class='card-title'>{name}</div>"
        f"<span class='price-badge'>${price}</span>"
        f"{short_desc}"
        f"</div>"
        f"</div>"
    )
    st.markdown(html_content, unsafe_allow_html=True)

    if btn_key:
        if st.button("View Product →", key=btn_key, use_container_width=True):
            sample = dataset.sample(1)
            st.session_state.selected_product = {
                'name': name,
                'image': img,
                'data': sample
            }
            st.session_state.page = 'analysis'
            st.rerun()


def draw_shap_bar(name, value, reverse=False):
    """Render a single SHAP feature-importance bar (logic preserved, CSS centralized)."""
    is_pos = value > 0
    if reverse:
        is_pos = not is_pos
    color = "#22c55e" if is_pos else "#ef4444"
    width = min(100, max(5, abs(value) * 200))
    sign = "+" if value >= 0 else ""
    st.markdown(
        f"<div class='shap-bar-wrap'>"
        f"<div class='shap-label'><span>{name}</span><span class='val'>{sign}{value:.2f}</span></div>"
        f"<div class='shap-track'>"
        f"<div class='shap-fill' style='width:{width}%;background:{color};'></div>"
        f"</div></div>",
        unsafe_allow_html=True
    )


def draw_lime_bar(name, value, reverse=False):
    """Render a single LIME feature-importance bar (mirrors draw_shap_bar styling)."""
    is_pos = value > 0
    if reverse:
        is_pos = not is_pos
    color = "#22c55e" if is_pos else "#ef4444"
    width = min(100, max(5, abs(value) * 200))
    sign = "+" if value >= 0 else ""
    st.markdown(
        f"<div class='lime-bar-wrap'>"
        f"<div class='lime-label'><span>{name}</span><span class='val'>{sign}{value:.2f}</span></div>"
        f"<div class='lime-track'>"
        f"<div class='lime-fill' style='width:{width}%;background:{color};'></div>"
        f"</div></div>",
        unsafe_allow_html=True
    )


@st.cache_resource
def get_lime_explainer(X_train_values, feature_names):
    # Ensure categorical_features is None, or explicitly pass indices if needed
    # We set discretize_continuous=True to handle the scaling automatically
    return lime.lime_tabular.LimeTabularExplainer(
        training_data=X_train_values,
        feature_names=feature_names,
        class_names=["Not Recommended", "Recommended"],
        mode="classification",
        discretize_continuous=True
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  STOREFRONT SECTIONS — Each section is its own function
# ═══════════════════════════════════════════════════════════════════════════════

def recommended_section():
    """Render the 'Recommended For You' section with a distinct tinted container."""
    rec = dataset[dataset['Will_Recommend'] == 1].head(4)
    imgs = [
        "https://picsum.photos/seed/headphones/400/300",
        "https://picsum.photos/seed/backpack/400/300",
        "https://picsum.photos/seed/smartwatch/400/300",
        "https://picsum.photos/seed/sneakers/400/300",
    ]
    names = ["Sony Headphones", "Tech Backpack", "Smart Watch", "Zoom Pegasus"]

    cards_html = ""
    for i, (idx, row) in enumerate(rec.iterrows()):
        img_url = imgs[i]
        name = names[i]
        price = f"{row['Price_USD']:.2f}"
        cards_html += (
            f"<div class='styled-card' style='margin-bottom:0;height:320px;'>"
            f"<div class='card-img-container' style='height:140px;'><img src='{img_url}' alt='{name}'></div>"
            f"<div class='card-info'>"
            f"<div class='card-title' style='font-size:15px;'>{name}</div>"
            f"<span class='price-badge' style='font-size:13px;'>${price}</span>"
            f"</div>"
            f"</div>"
        )

    html_content = (
        f"<div class='rec-section-wrapper'>"
        f"<div class='section-header' style='margin-bottom:20px;border-left-color:var(--accent-cyan);background:linear-gradient(90deg,rgba(8,145,178,0.08) 0%,transparent 80%);'>"
        f"⭐&ensp;Recommended For You <span class='header-chip' style='background:rgba(8,145,178,0.15);color:#22d3ee;border-color:rgba(8,145,178,0.2);'>AI Curated</span>"
        f"</div>"
        f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;'>"
        f"{cards_html}"
        f"</div>"
        f"</div>"
    )
    st.markdown(html_content, unsafe_allow_html=True)


def all_products_section():
    """Render the 'All Products' grid."""
    section_header("🛒", "All Products")

    all_n    = ["Speaker", "Bottle", "Coffee", "Watch", "Case", "Keyboard", "Mouse", "Stand"]
    all_imgs = [f"https://picsum.photos/seed/{name}/400/300" for name in all_n]
    np.random.seed(99)
    all_prices = np.random.randint(20, 201, size=len(all_n)).tolist()

    for row in range(2):
        cols = st.columns(4, gap="medium")
        for col in range(4):
            idx = row * 4 + col
            with cols[col]:
                styled_card(
                    all_imgs[idx],
                    all_n[idx],
                    f"{all_prices[idx]:.2f}",
                    btn_key=f"all_{idx}"
                )
        if row == 0:
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)


def mongodb_products_section():
    """Render products loaded from MongoDB, if any exist."""
    manual_products = load_manual_products()
    if not manual_products:
        return

    section_header("➕", "Added Products")
    for row_start in range(0, len(manual_products), 4):
        batch = manual_products[row_start:row_start + 4]
        cols  = st.columns(4, gap="medium")
        for col_idx, product in enumerate(batch):
            with cols[col_idx]:
                styled_card(
                    product.get("image",
                        f"https://picsum.photos/seed/{product['name']}/400/300"),
                    product["name"],
                    product["price"],
                    product.get("description", ""),
                    btn_key=f"view_{product['_id']}"
                )
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)


def add_product_form():
    """Expandable form to add a new product to MongoDB."""
    with st.expander("➕ Add New Product", expanded=False):
        with st.form("add_product_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                new_name  = st.text_input("Product Name *", placeholder="e.g. Wireless Earbuds")
                new_price = st.number_input("Price (USD) *", min_value=0.01, value=29.99, step=0.01)
            with col_b:
                new_img  = st.text_input("Image URL (optional)",
                                         placeholder="https://... (leave blank for auto)")
                new_desc = st.text_input("Short Description (optional)",
                                         placeholder="One-line product description")

            submitted = st.form_submit_button("💾 Save Product", use_container_width=True)
            if submitted:
                if not new_name.strip():
                    st.error("Product name is required.")
                else:
                    image_url = new_img.strip() or \
                                f"https://picsum.photos/seed/{new_name.strip()}/400/300"
                    ok = save_product(new_name.strip(), round(new_price, 2),
                                      image_url, new_desc.strip())
                    if ok:
                        st.success(f"✅ '{new_name.strip()}' saved to MongoDB!")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGES
# ═══════════════════════════════════════════════════════════════════════════════

def show_login():
    """Login page with glassmorphism card."""
    inject_design_system()

    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)

    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        # Self-contained header element constructed as single line
        login_header = (
            f"<div class='login-container'>"
            f"<div class='login-title'>🧠 XAI E-Commerce</div>"
            f"<div class='login-subtitle'>Sign in to explore AI-powered product insights</div>"
            f"</div>"
        )
        st.markdown(login_header, unsafe_allow_html=True)

        with st.form("login"):
            st.text_input("Email", "admin@university.edu")
            st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True):
                st.session_state.page = 'storefront'
                st.rerun()


def show_storefront():
    """Main storefront page — composed from modular section components."""
    inject_design_system()
    show_navbar()

    recommended_section()
    section_spacer()

    all_products_section()
    section_spacer()

    mongodb_products_section()
    section_spacer()

    add_product_form()
    show_footer()


def show_analysis():
    """Product analysis page with SHAP/LIME insights (XAI logic untouched)."""
    inject_design_system()
    show_navbar()

    # Breadcrumb and Back Action
    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("← Back to Store", key="back_to_store", use_container_width=True):
            st.session_state.page = 'storefront'
            st.rerun()

    st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True)

    prod = st.session_state.selected_product
    c1, c2 = st.columns([1, 1.5], gap="large")

    with c1:
        price_val = prod['data']['Price_USD'].values[0]
        c1_content = (
            f"<div class='analysis-container'>"
            f"<div class='card-img-container' style='height: 280px;'>"
            f"<img src='{prod['image']}' alt='{prod['name']}'>"
            f"</div>"
            f"<div style='margin-top: 20px;'>"
            f"<div class='analysis-product-title'>{prod['name']}</div>"
            f"<span class='price-badge' style='font-size: 16px; padding: 6px 16px;'>${price_val:.2f}</span>"
            f"</div>"
            f"</div>"
        )
        st.markdown(c1_content, unsafe_allow_html=True)

    with c2:
        if st.session_state.xai_enabled:
            header_content = (
                f"<div class='analysis-container' style='margin-bottom: 20px;'>"
                f"<h3 style='margin: 0 0 15px 0;'>📈 SHAP / LIME Feature Importance</h3>"
                f"</div>"
            )
            st.markdown(header_content, unsafe_allow_html=True)
            
            explainer   = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(prod['data'])

            if isinstance(shap_values, list):
                impacts = shap_values[1][0]
            elif len(np.shape(shap_values)) == 3:
                impacts = shap_values[0, :, 1]
            else:
                impacts = shap_values[0]

            # LIME Calculation
            lime_explainer = get_lime_explainer(X_train.values, list(X_train.columns))
            data_row = prod['data'].drop(columns=['Will_Recommend'], errors='ignore').iloc[0].values

            exp = lime_explainer.explain_instance(
                data_row=data_row,
                predict_fn=model.predict_proba,
                num_features=3  # You have 3-4 features; do not ask for more features than exist
            )
            lime_feat = {"Product Rating": 0.0, "Discount (%)": 0.0, "Price ($)": 0.0}
            for condition, weight in exp.as_list():
                lc = condition.lower()
                if "rating" in lc:
                    lime_feat["Product Rating"] = float(weight)
                elif "discount" in lc:
                    lime_feat["Discount (%)"] = float(weight)
                elif "price" in lc:
                    lime_feat["Price ($)"] = float(weight)

            col_shap, col_lime = st.columns(2, gap="medium")
            with col_shap:
                st.markdown("#### SHAP Explanation")
                draw_shap_bar("Product Rating", impacts[0])
                draw_shap_bar("Discount (%)",   impacts[3])
                draw_shap_bar("Price ($)",      impacts[2], reverse=True)
            with col_lime:
                st.markdown("#### LIME Explanation")
                draw_lime_bar("Product Rating", lime_feat["Product Rating"])
                draw_lime_bar("Discount (%)",   lime_feat["Discount (%)"])
                draw_lime_bar("Price ($)",      lime_feat["Price ($)"], reverse=True)

            st.info("✨ AI Explanation: High reviews and discount drove this recommendation.")
        else:
            header_content = (
                f"<div class='analysis-container' style='margin-bottom: 20px;'>"
                f"<h3 style='margin: 0 0 15px 0;'>📦 Product Details</h3>"
                f"</div>"
            )
            st.markdown(header_content, unsafe_allow_html=True)
            
            data = prod['data']
            st.metric("Rating",   f"{data['Product_Rating'].values[0]} ⭐")
            st.metric("Price",    f"${data['Price_USD'].values[0]:.2f}")
            st.metric("Discount", f"{data['Discount_Percent'].values[0]}%")
            st.caption("🔒 XAI explanations are hidden in Control mode. "
                       "Enable the toggle in the header to view SHAP/LIME insights.")


# ═══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

def show_footer():
    """Render a simple site footer."""
    st.markdown("""
    <div class='site-footer'>
        <div style='margin-bottom: 8px; font-weight: 700; font-size: 15px; background: linear-gradient(135deg, var(--accent-light), var(--accent-cyan)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🧠 XAI Store</div>
        <div>&copy; 2026 XAI Store &middot; Built with Streamlit &middot; <a href='#'>Privacy</a> &middot; <a href='#'>Terms</a></div>
    </div>
    """, unsafe_allow_html=True)


def show_system_stats():
    """System Stats page displaying accuracy, precision, and F1-score dashboard and bar chart."""
    inject_design_system()
    show_navbar()

    # Breadcrumb and Back Action
    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("← Back to Store", key="stats_back_to_store", use_container_width=True):
            st.session_state.page = 'storefront'
            st.rerun()

    st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True)
    section_header("📊", "System Stats")

    # Fetch trust metrics from backend
    try:
        response = requests.get("http://127.0.0.1:8001/trust_metrics", timeout=5)
        if response.status_code != 200:
            st.error(f"Error fetching metrics: Server returned status {response.status_code}")
            return
        
        data = response.json()
    except Exception as e:
        st.error("Could not connect to the backend server. Please make sure the backend is running.")
        st.info("Tip: Run `python main.py` in your terminal to start the FastAPI server.")
        return

    # Check if model is not trained yet
    if "message" in data:
        st.warning(data["message"])
        st.info("Showing baseline/fallback simulation values below:")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Accuracy (Baseline)", value="85.0%")
        with col2:
            st.metric(label="Precision (Baseline)", value="83.0%")
        with col3:
            st.metric(label="F1-Score (Baseline)", value="85.0%")
            
        st.markdown("### Metrics Visualization")
        chart_data = pd.DataFrame({
            "Metric": ["Accuracy", "Precision", "Recall", "F1-Score"],
            "Value": [0.85, 0.83, 0.88, 0.85]
        }).set_index("Metric")
        st.bar_chart(chart_data)
        
        show_footer()
        return

    # If model is trained, extract metrics
    accuracy = data.get("accuracy", 0.0)
    precision = data.get("precision", 0.0)
    recall = data.get("recall", 0.0)
    f1 = data.get("f1", 0.0)
    training_samples = data.get("training_samples", 0)
    test_samples = data.get("test_samples", 0)
    total_products = data.get("total_products", 0)
    features = data.get("features", [])

    # Display metrics in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Accuracy", value=f"{accuracy:.2%}")
    with col2:
        st.metric(label="Precision", value=f"{precision:.2%}")
    with col3:
        st.metric(label="F1-Score", value=f"{f1:.2%}")

    section_spacer()
    
    # Bar chart
    st.markdown("### Metrics Visualization")
    chart_data = pd.DataFrame({
        "Metric": ["Accuracy", "Precision", "Recall", "F1-Score"],
        "Value": [accuracy, precision, recall, f1]
    }).set_index("Metric")
    st.bar_chart(chart_data)

    section_spacer()

    # Metadata card/table
    st.markdown("### Model Details")
    metadata_df = pd.DataFrame({
        "Parameter": ["Total Products", "Training Samples", "Test Samples", "Features Used"],
        "Value": [total_products, training_samples, test_samples, ", ".join(features)]
    })
    st.dataframe(metadata_df, hide_index=True, use_container_width=True)

    show_footer()


# ─── Router ───────────────────────────────────────────────────────────────────
if st.session_state.page == 'login':
    show_login()
elif st.session_state.page == 'storefront':
    show_storefront()
elif st.session_state.page == 'analysis':
    show_analysis()
elif st.session_state.page == 'system_stats':
    show_system_stats()