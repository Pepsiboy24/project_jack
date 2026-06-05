import pandas as pd
import zipfile
import random
import os
import shutil

zip_path = 'archive.zip'
output_dir = 'images'
output_csv = 'products.csv'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print("Opening Myntra dataset zip...")
with zipfile.ZipFile(zip_path, 'r') as z:
    with z.open('styles.csv') as f:
        print("Parsing styles.csv...")
        df = pd.read_csv(f, on_bad_lines='skip')

    # Filter for everyday consumer items like clothing, shoes, and bags
    target_subs = ['Topwear', 'Bottomwear', 'Shoes', 'Bags', 'Sandal', 'Flip Flops', 'Wallets', 'Belts', 'Dress', 'Apparel Set', 'Innerwear', 'Loungewear and Nightwear']
    filtered_df = df[df['subCategory'].isin(target_subs)].copy()
    
    # Shuffle and pick exact 5000
    filtered_df = filtered_df.sample(n=min(5000, len(filtered_df)), random_state=42)
    
    products = []
    extracted_count = 0
    all_files = z.namelist()
    
    print("Synthesizing metadata and exporting 5000 images...")
    for idx, row in filtered_df.iterrows():
        prod_id = row['id']
        name = str(row.get('productDisplayName', f"Fashion Item {prod_id}"))
        sub_cat = str(row.get('subCategory', 'Accessories'))
        if sub_cat in ['Topwear', 'Bottomwear', 'Dress', 'Apparel Set', 'Innerwear', 'Loungewear and Nightwear']:
            category = 'Clothing'
        elif sub_cat in ['Shoes', 'Sandal', 'Flip Flops']:
            category = 'Shoes'
        else:
            category = 'Accessories'
        
        # Determine image path in zip
        # Different Kaggle versions might use 'images/15970.jpg' or 'myntradataset/images/15970.jpg'
        img_name = f"{prod_id}.jpg"
        img_zip_path_1 = f"images/{img_name}"
        img_zip_path_2 = f"myntradataset/images/{img_name}"
        
        target_path = None
        if img_zip_path_1 in all_files:
            target_path = img_zip_path_1
        elif img_zip_path_2 in all_files:
            target_path = img_zip_path_2
            
        if target_path:
            with z.open(target_path) as source, open(os.path.join(output_dir, img_name), "wb") as target:
                shutil.copyfileobj(source, target)
            extracted_count += 1
            
            # Map exactly to local backend
            image_url = f"http://127.0.0.1:8001/images/{img_name}"
        else:
            image_url = f"https://loremflickr.com/400/500/fashion?lock={prod_id}"
            
        # Synthesize about_product
        color = str(row.get('baseColour', 'stylish'))
        article = str(row.get('articleType', 'item'))
        usage = str(row.get('usage', 'everyday'))
        gender = str(row.get('gender', 'Unisex'))
        
        about_product = f"This premium {color.lower()} {article.lower()} is exceptionally designed for {gender}'s {usage.lower()} wear. Perfectly crafted by {name.split()[0]} to combine comfort, high-quality aesthetics, and everyday durability."
        
        actual_price = round(random.uniform(15.0, 300.0), 2)
        conversion_rate = 1500  # 1 USD = 1500 NGN
        price_naira = round(actual_price * conversion_rate, 2)
        ratings = round(random.uniform(3.5, 5.0), 1)
        
        products.append({
            "id": prod_id,
            "productDisplayName": name,
            "masterCategory": category,
            "actual_price": actual_price,
            "price_naira": price_naira,
            "ratings": ratings,
            "Helpfulness_Score": 0,
            "Review_Length": 0,
            "Image_URL": image_url,
            "about_product": about_product
        })
        
    out_df = pd.DataFrame(products)
    out_df.to_csv(output_csv, index=False)
    print(f"Successfully wrote {len(out_df)} products to {output_csv} and extracted {extracted_count} matching images!")
