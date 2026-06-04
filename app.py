import streamlit as st
import pandas as pd
import shap
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

st.set_page_config(page_title="XAI Storefront", layout="wide")

# ─── MongoDB Connection ───────────────────────────────────────────────────────
MONGO_URI = "mongodb+srv://Jack:Jack0@@cluster0.pnqkj3b.mongodb.net/?appName=Cluster0"

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
for key, val in [('page', 'login'), ('selected_product', None)]:
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

# ─── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #0B1121; color: white; }

/* Card hover effect */
div[data-testid="column"] { transition: transform 0.2s; }
div[data-testid="column"]:hover { transform: translateY(-3px); }

/* Price badge */
.price-badge {
    display: inline-block;
    background: linear-gradient(135deg, #1e40af, #3b82f6);
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 15px;
    margin: 4px 0 8px 0;
}

/* Section headers */
.section-header {
    font-size: 22px;
    font-weight: 700;
    border-left: 4px solid #3b82f6;
    padding-left: 12px;
    margin: 20px 0 16px 0;
}

/* Success toast */
.success-box {
    background: #064e3b;
    border: 1px solid #10b981;
    border-radius: 8px;
    padding: 10px 16px;
    color: #6ee7b7;
}
</style>
""", unsafe_allow_html=True)

# ─── Helpers ──────────────────────────────────────────────────────────────────
def draw_shap_bar(name, value, reverse=False):
    is_pos = value > 0
    if reverse:
        is_pos = not is_pos
    color = "#22c55e" if is_pos else "#ef4444"
    width = min(100, max(5, abs(value) * 200))
    st.write(f"**{name}**: {value:.2f}")
    st.markdown(
        f"<div style='width:100%;background:#334155;height:12px;margin-bottom:15px;border-radius:6px;'>"
        f"<div style='width:{width}%;background:{color};height:12px;border-radius:6px;'></div></div>",
        unsafe_allow_html=True
    )

def show_navbar():
    st.markdown(
        "<div style='display:flex;justify-content:space-between;align-items:center;"
        "margin-bottom:30px;padding:12px 0;border-bottom:1px solid #1e293b;'>"
        "<div style='font-size:22px;font-weight:bold;'>🧠 XAI Store</div>"
        "<div style='font-size:18px;'>👤 Profile &nbsp;&nbsp; 🛒 Cart</div></div>",
        unsafe_allow_html=True
    )

def product_card(img, name, price, description="", btn_key=None):
    """Reusable product card. Products are permanent — no deletion allowed."""
    st.image(img, use_container_width=True)
    st.write(f"#### {name}")
    st.markdown(f"<span class='price-badge'>${price}</span>", unsafe_allow_html=True)
    if description:
        st.caption(description)
    if btn_key:
        st.button("View Product", key=btn_key)

# ─── Pages ────────────────────────────────────────────────────────────────────
def show_login():
    st.write("")
    st.write("")
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>🧠 XAI E-Commerce</h1>",
                    unsafe_allow_html=True)
        with st.form("login"):
            st.text_input("Email", "admin@university.edu")
            st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True):
                st.session_state.page = 'storefront'
                st.rerun()


def show_storefront():
    show_navbar()

    # ── Recommended ─────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>⭐ Recommended For You</div>",
                unsafe_allow_html=True)
    rec   = dataset[dataset['Will_Recommend'] == 1].head(4)
    imgs  = [f"https://picsum.photos/id/{i}/400/300" for i in [1, 2, 3, 4]]
    names = ["Sony Headphones", "Tech Backpack", "Smart Watch", "Zoom Pegasus"]
    cols  = st.columns(4)
    for i, (idx, row) in enumerate(rec.iterrows()):
        with cols[i]:
            st.image(imgs[i], use_container_width=True)
            st.write(f"#### {names[i]}")
            st.markdown(f"<span class='price-badge'>${row['Price_USD']}</span>",
                        unsafe_allow_html=True)

    st.write("---")

    # ── All Products (hardcoded) ─────────────────────────────────────────────
    st.markdown("<div class='section-header'>🛒 All Products</div>",
                unsafe_allow_html=True)
    all_imgs = [f"https://picsum.photos/id/{i}/400/300" for i in range(10, 18)]
    all_n    = ["Speaker", "Bottle", "Coffee", "Watch", "Case", "Keybd", "Mouse", "Stand"]
    for row in range(2):
        all_cols = st.columns(4)
        for col in range(4):
            idx = row * 4 + col
            with all_cols[col]:
                product_card(all_imgs[idx], all_n[idx], "—", btn_key=f"all_{idx}")

    st.write("---")

    # ── MongoDB Products (permanent — loaded from cloud) ─────────────────────
    manual_products = load_manual_products()
    if manual_products:
        st.markdown("<div class='section-header'>➕ Added Products</div>",
                    unsafe_allow_html=True)
        for row_start in range(0, len(manual_products), 4):
            batch = manual_products[row_start:row_start + 4]
            cols  = st.columns(4)
            for col_idx, product in enumerate(batch):
                with cols[col_idx]:
                    product_card(
                        product.get("image",
                            f"https://picsum.photos/seed/{product['name']}/400/300"),
                        product["name"],
                        product["price"],
                        product.get("description", ""),
                        btn_key=f"view_{product['_id']}"
                    )
        st.write("---")

    # ── Add New Product Form ─────────────────────────────────────────────────
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


def show_analysis():
    show_navbar()
    if st.button("← Back to Store"):
        st.session_state.page = 'storefront'
        st.rerun()

    prod = st.session_state.selected_product
    c1, c2 = st.columns([1, 1.5])

    with c1:
        st.image(prod['image'], use_container_width=True)
        st.write(f"### {prod['name']}")
        st.markdown(
            f"<span class='price-badge'>${prod['data']['Price_USD'].values[0]}</span>",
            unsafe_allow_html=True
        )

    with c2:
        st.write("### 📈 SHAP / LIME Feature Importance")
        explainer   = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(prod['data'])

        if isinstance(shap_values, list):
            impacts = shap_values[1][0]
        elif len(np.shape(shap_values)) == 3:
            impacts = shap_values[0, :, 1]
        else:
            impacts = shap_values[0]

        draw_shap_bar("Product Rating", impacts[0])
        draw_shap_bar("Discount (%)",   impacts[3])
        draw_shap_bar("Price ($)",      impacts[2], reverse=True)
        st.info("✨ AI Explanation: High reviews and discount drove this recommendation.")


# ─── Router ───────────────────────────────────────────────────────────────────
if st.session_state.page == 'login':
    show_login()
elif st.session_state.page == 'storefront':
    show_storefront()
elif st.session_state.page == 'analysis':
    show_analysis()