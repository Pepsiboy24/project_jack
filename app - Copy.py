import streamlit as st
import pandas as pd
import shap
import numpy as np
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="XAI Storefront", layout="wide")

if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'selected_product' not in st.session_state:
    st.session_state.selected_product = None

@st.cache_data 
def load_data():
    try:
        df = pd.read_csv("fast_amazon.csv")
    except FileNotFoundError:
        st.warning("fast_amazon.csv not found. Using fallback synthetic dataset.")
        df = pd.DataFrame({
            'overall': np.random.choice([3.0, 4.0, 5.0], size=500),
            'reviewText': ["Loved it!" for _ in range(500)]
        })

    dataset = pd.DataFrame()
    dataset['Product_Rating'] = df['overall'].fillna(4.0)
    
    def count_words(x):
        return len(str(x).split())
        
    dataset['Review_Word_Count'] = df.get('reviewText', pd.Series(["" for _ in range(len(df))])).fillna("").apply(count_words)
    
    np.random.seed(42)
    dataset['Price_USD'] = np.random.uniform(10, 500, size=len(dataset)).round(2)
    dataset['Discount_Percent'] = np.random.choice([0, 5, 10, 15], size=len(dataset))
    
    rec_logic = (dataset['Product_Rating'] >= 4) & (dataset['Discount_Percent'] >= 5)
    dataset['Will_Recommend'] = rec_logic.astype(int)
    
    dataset = dataset.dropna()
    if dataset.empty:
        dataset = pd.DataFrame({
            'Product_Rating': np.random.choice([3.0, 4.0, 5.0], size=20),
            'Review_Word_Count': np.random.randint(5, 100, size=20),
            'Price_USD': np.random.uniform(10, 500, size=20).round(2),
            'Discount_Percent': np.random.choice([0, 5, 10, 15], size=20),
            'Will_Recommend': np.random.choice([0, 1], size=20)
        })

    X = dataset.drop('Will_Recommend', axis=1)
    y = dataset['Will_Recommend']
    
    model = RandomForestClassifier(random_state=42, max_depth=5)
    model.fit(X, y)
    return dataset, model, X

dataset, model, X_train = load_data()

# Safe CSS without long lines
css1 = "<style>.stApp { background-color: #0B1121; color: white; }</style>"
st.markdown(css1, unsafe_allow_html=True)

def draw_shap_bar(name, value, reverse=False):
    is_pos = value > 0
    if reverse:
        is_pos = not is_pos
    color = "#22c55e" if is_pos else "#ef4444"
    width = min(100, max(5, abs(value) * 200))
    
    st.write(f"**{name}**: {value:.2f}")
    h1 = "<div style='width:100%; background:#334155; height:12px; margin-bottom:15px;'>"
    h2 = f"<div style='width:{width}%; background:{color}; height:12px;'></div></div>"
    st.markdown(h1 + h2, unsafe_allow_html=True)

def show_navbar():
    n1 = "<div style='display:flex; justify-content:space-between; margin-bottom:30px;'>"
    n2 = "<div style='font-size:20px; font-weight:bold;'>🧠 XAI Store</div>"
    n3 = "<div style='font-size:20px;'>👤 Profile &nbsp;&nbsp; 🛒 Cart</div></div>"
    st.markdown(n1 + n2 + n3, unsafe_allow_html=True)

def show_login():
    st.write("")
    st.write("")
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>🧠 XAI E-Commerce</h1>", unsafe_allow_html=True)
        with st.form("login"):
            st.text_input("Email", "admin@university.edu")
            st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                st.session_state.page = 'storefront'
                st.rerun()

def show_storefront():
    show_navbar()
    st.markdown("<h3>Recommended For You</h3>", unsafe_allow_html=True)
    
    rec = dataset[dataset['Will_Recommend'] == 1].head(4)
    cols = st.columns(4)
    
    # Tiny URLs that will never get cut off
    imgs = [
        "https://picsum.photos/id/1/400/300",
        "https://picsum.photos/id/2/400/300",
        "https://picsum.photos/id/3/400/300",
        "https://picsum.photos/id/4/400/300"
    ]
    names = ["Sony Headphones", "Tech Backpack", "Smart Watch", "Zoom Pegasus"]
    
    for i, (idx, row) in enumerate(rec.iterrows()):
        with cols[i]:
            st.image(imgs[i], use_container_width=True)
            st.write(f"#### {names[i]}")
            st.write(f"**${row['Price_USD']}**")

    st.write("---")
    st.markdown("<h3>🛒 All Products</h3>", unsafe_allow_html=True)
    
    all_imgs = [
        "https://picsum.photos/id/10/400/300",
        "https://picsum.photos/id/11/400/300",
        "https://picsum.photos/id/12/400/300",
        "https://picsum.photos/id/13/400/300",
        "https://picsum.photos/id/14/400/300",
        "https://picsum.photos/id/15/400/300",
        "https://picsum.photos/id/16/400/300",
        "https://picsum.photos/id/17/400/300"
    ]
    all_n = ["Speaker", "Bottle", "Coffee", "Watch", "Case", "Keybd", "Mouse", "Stand"]
    
    for row in range(2):
        all_cols = st.columns(4)
        for col in range(4):
            idx = row * 4 + col
            with all_cols[col]:
                st.image(all_imgs[idx], use_container_width=True)
                st.write(f"#### {all_n[idx]}")
                st.button("View Product", key=f"all_{idx}")

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
        st.write(f"## ${prod['data']['Price_USD'].values[0]}")

    with c2:
        st.write("### 📈 SHAP / LIME Feature Importance")
        
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(prod['data'])
        if isinstance(shap_values, list): 
            impacts = shap_values[1][0] 
        elif len(np.shape(shap_values)) == 3: 
            impacts = shap_values[0, :, 1]
        else: 
            impacts = shap_values[0]

        draw_shap_bar("Product Rating", impacts[0])
        draw_shap_bar("Discount (%)", impacts[3])
        draw_shap_bar("Price ($)", impacts[2], reverse=True)
        
        st.info("✨ AI Explanation: High reviews and discount drove this recommendation.")

if st.session_state.page == 'login': 
    show_login()
elif st.session_state.page == 'storefront': 
    show_storefront()
elif st.session_state.page == 'analysis': 
    show_analysis()