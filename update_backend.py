import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add static files import
content = content.replace(
    'from fastapi.responses import FileResponse, RedirectResponse',
    'from fastapi.responses import FileResponse, RedirectResponse\nfrom fastapi.staticfiles import StaticFiles'
)

content = content.replace(
    'DB_FILE = "ecommerce.db"',
    'if not os.path.exists("images"): os.makedirs("images")\ntry: app.mount("/images", StaticFiles(directory="images"), name="images")\nexcept: pass\n\nDB_FILE = "ecommerce.db"'
)

# Update features and dataset building
old_feature_block = """    fashion_df['Product_Name'] = fashion_df['productDisplayName']
    fashion_df['Category'] = fashion_df['masterCategory']
    import random
    def generate_image(row):
        name = str(row.get('Product_Name', '')).lower()       
        keywords = ["smartphone", "phone", "headphones", "watch", "earbuds", "charger", "speaker", "laptop", "monitor", "tablet", "camera", "tech", "laptop", "cable"]
        found_kw = "gadget"
        for kw in keywords:
            if kw in name:
                found_kw = kw
                break
        
        rand_id = row.get('id', random.randint(1, 100000))
        return f"https://loremflickr.com/400/500/{found_kw}?lock={rand_id}"

    fashion_df['Image_URL'] = fashion_df.apply(generate_image, axis=1)
    
    dataset = fashion_df.copy()
    
    # Dropna to avoid breaking ML models
    dataset = dataset.dropna(subset=['Price_NGN', 'ratings', 'Helpfulness_Score', 'Review_Length', 'Will_Recommend'])
    X = dataset[['Price_NGN', 'ratings', 'Helpfulness_Score', 'Review_Length']]
    y = dataset['Will_Recommend']"""

new_feature_block = """    fashion_df['Product_Name'] = fashion_df['productDisplayName']
    fashion_df['Category'] = fashion_df['masterCategory']
    
    unique_cats = fashion_df['masterCategory'].unique()
    global category_encoder
    category_encoder = {c: i for i, c in enumerate(unique_cats)}
    fashion_df['Category_Encoded'] = fashion_df['masterCategory'].map(category_encoder)
    
    if 'Image_URL' not in fashion_df.columns:
        fashion_df['Image_URL'] = "https://loremflickr.com/400/500/fashion"
    
    dataset = fashion_df.copy()
    
    dataset = dataset.dropna(subset=['Price_NGN', 'ratings', 'Category_Encoded', 'Will_Recommend'])
    X = dataset[['Price_NGN', 'ratings', 'Category_Encoded']]
    y = dataset['Will_Recommend']"""

content = content.replace(old_feature_block, new_feature_block)

# Update get_recommendation mapping
old_rec = """    rec_df = recommended_df.sample(n=min(rec_count, len(recommended_df)))
    res = []
    for i, (_, row) in enumerate(rec_df.iterrows()):
        res.append({
            "id": i,
            "name": str(row['Product_Name']),
            "price": float(row['Price_NGN']),
            "img": str(row['Image_URL']),
            "rating": float(row['ratings']),
            "category": str(row['Category']),
            "helpfulness_score": float(row['Helpfulness_Score']),
            "review_length": float(row['Review_Length'])
        })"""

new_rec = """    rec_df = recommended_df.sample(n=min(rec_count, len(recommended_df)))
    res = []
    for i, (_, row) in enumerate(rec_df.iterrows()):
        res.append({
            "id": i,
            "name": str(row['Product_Name']),
            "price": float(row['Price_NGN']),
            "img": str(row['Image_URL']),
            "rating": float(row['ratings']),
            "category": str(row['Category']),
            "about_product": str(row.get('about_product', 'A stylish premium item.'))
        })"""

content = content.replace(old_rec, new_rec)

old_all = """    sample_df = dataset.sample(n=min(5000, len(dataset)))
    res = []
    for i, (_, row) in enumerate(sample_df.iterrows()):
        res.append({
            "name": str(row['Product_Name']),
            "price": float(row['Price_NGN']),
            "img": str(row['Image_URL']),
            "rating": float(row['ratings']),
            "category": str(row['Category']),
            "helpfulness_score": float(row['Helpfulness_Score']),
            "review_length": float(row['Review_Length'])
        })"""

new_all = """    sample_df = dataset.sample(n=min(5000, len(dataset)))
    res = []
    for i, (_, row) in enumerate(sample_df.iterrows()):
        res.append({
            "name": str(row['Product_Name']),
            "price": float(row['Price_NGN']),
            "img": str(row['Image_URL']),
            "rating": float(row['ratings']),
            "category": str(row['Category']),
            "about_product": str(row.get('about_product', 'A stylish premium item.'))
        })"""

content = content.replace(old_all, new_all)


# Update Explain Request completely
import re
content = re.sub(r'class ExplainRequest\(BaseModel\):[\s\S]*?We take the top influential feature from SHAP/LIME and convert it into \n    # plain, understandable English\. This translates mathematical explanations\n    # into a user-friendly UI without relying on black-box external wrappers\.', 
r'''class ExplainRequest(BaseModel):
    name: str = "product"
    rating: float
    price: float
    category: str
    about_product: str = ""

@app.post("/explain")
def explain_recommendation(req: ExplainRequest):
    global category_encoder
    cat_enc = category_encoder.get(req.category, 0) if category_encoder else 0
    input_df = pd.DataFrame([{
        "Price_NGN": req.price,
        "ratings": req.rating,
        "Category_Encoded": cat_enc
    }])
    
    # SHAP Global Explanation
    shap_values = shap_explainer.shap_values(input_df)
    if isinstance(shap_values, list): impacts = shap_values[1][0] 
    elif len(np.shape(shap_values)) == 3: impacts = shap_values[0, :, 1]
    else: impacts = shap_values[0]
        
    shap_feat = {
        "Price": float(impacts[0]),
        "Rating": float(impacts[1]),
        "Category": float(impacts[2])
    }
    
    # LIME Local Explanation
    data_row = input_df.iloc[0].values
    exp = lime_explainer.explain_instance(
        data_row=data_row, 
        predict_fn=model.predict_proba, 
        num_features=3
    )
    lime_list = exp.as_list()
    lime_feat = {"Price": 0.0, "Rating": 0.0, "Category": 0.0}
    for condition, weight in lime_list:
        if "Price_NGN" in condition: lime_feat["Price"] = float(weight)
        elif "ratings" in condition: lime_feat["Rating"] = float(weight)
        elif "Category" in condition: lime_feat["Category"] = float(weight)
    
    best_shap = max(shap_feat.items(), key=lambda x: abs(x[1]))
    best_lime = max(lime_feat.items(), key=lambda x: abs(x[1]))
    
    # -------------------------------------------------------------------------
    # 5. NATURAL LANGUAGE GENERATION (NLG) LAYER
    # -------------------------------------------------------------------------
    # We take the top influential feature from SHAP/LIME and convert it into 
    # plain, understandable English. This translates mathematical explanations
    # into a user-friendly UI without relying on black-box external wrappers.''', content)

# Replace NLG dictionary
old_nlg = """    user_friendly_reasons = {
        "Price": f"it matches your preferred budget of around ₦{req.price:,.2f}",
        "Rating": "it has outstanding user ratings from the community",
        "Helpfulness": "other verified shoppers found the detailed reviews for this product exceedingly helpful",
        "Review_Length": "customers have provided extensive, detailed positive feedback about their experience"
    }"""
new_nlg = """    user_friendly_reasons = {
        "Price": f"it matches your preferred budget of around ₦{req.price:,.2f}",
        "Rating": "it holds outstanding user ratings from the fashion community",
        "Category": f"it mathematically ranks highly among other {req.category} items"
    }"""
content = content.replace(old_nlg, new_nlg)

# Update explanation response mapping
old_nlg_str = 'explanation = f"We highly recommend the {req.name} because {reason_text}. It carries a positive systemic impact score of {best_shap[1]:.2f} (SHAP) and {best_lime[1]:.2f} (LIME) within our ML ecosystem!"'
new_nlg_str = 'explanation = f"We highly recommend the {req.name} because {reason_text}. \\n\\n**About Product:** {req.about_product}\\n\\n*(It carries a positive systemic impact score of {best_shap[1]:.2f} SHAP and {best_lime[1]:.2f} LIME within our ML ecosystem)*"'
content = content.replace(old_nlg_str, new_nlg_str)

# Save
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated main.py")
