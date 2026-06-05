import json
import random
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    matthews_corrcoef,
    confusion_matrix,
    classification_report
)

def generate_synthetic_products():
    """Generates 100 realistic products to seed manual_products.json"""
    categories = ["Footwear", "Accessories", "Electronics", "Clothing"]
    
    brand_map = {
        "Footwear": ["Adidas", "Nike", "Puma", "Vans", "Reebok", "Converse"],
        "Accessories": ["Titan", "Fossil", "Casio", "Rolex", "Tommy Hilfiger"],
        "Electronics": ["Sony", "JBL", "Anker", "Samsung", "Apple", "Xiaomi"],
        "Clothing": ["Levis", "Zara", "H&M", "Polo", "Tommy Hilfiger", "Calvin Klein"]
    }
    
    item_map = {
        "Footwear": ["Running Shoes", "Sneakers", "Leather Boots", "Loafers", "Slippers", "Sandals"],
        "Accessories": ["Leather Watch", "Sunglasses", "Minimalist Wallet", "Leather Belt", "Backpack"],
        "Electronics": ["Wireless Headphones", "Bluetooth Speaker", "Smart Watch", "Power Bank", "Earbuds"],
        "Clothing": ["Slim Fit Jeans", "Striped Polo Shirt", "Cotton T-Shirt", "Hooded Sweatshirt", "Chino Pants"]
    }
    
    products = []
    
    # Let's seed a deterministic set of 100 products using random seed for reproducibility
    random.seed(42)
    
    for i in range(100):
        cat = random.choice(categories)
        brand = random.choice(brand_map[cat])
        item = random.choice(item_map[cat])
        
        name = f"{brand} {item} X{i+1}"
        price = round(random.uniform(15.0, 250.0), 2)
        rating = round(random.uniform(3.0, 5.0), 1)
        
        desc = f"This premium {brand} {item.lower()} is designed for excellent durability and modern comfort. Perfectly crafted to combine style and function."
        
        # Use loremflickr with category tag for nice visual mockups
        img_url = f"https://loremflickr.com/400/500/fashion,{(item.split()[-1]).lower()}?lock={i}"
        
        products.append({
            "id": f"seed_{i+1}",
            "name": name,
            "price": price,
            "category": cat,
            "about_product": desc,
            "img": img_url,
            "rating": rating
        })
        
    return products

def main():
    print("Step 1: Generating 100 synthetic products...")
    products = generate_synthetic_products()
    
    # Save to manual_products.json
    products_file = "manual_products.json"
    with open(products_file, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=4)
    print(f"[SUCCESS] Wrote {len(products)} products to {products_file}")
    
    print("\nStep 2: Training Random Forest model on the seeded dataset...")
    # Load dataset
    df = pd.DataFrame(products)
    df["price"]  = pd.to_numeric(df["price"],  errors="coerce").fillna(0)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(4.5)
    
    # Label encode categories
    cats = df["category"].fillna("General").unique()
    category_enc = {c: i for i, c in enumerate(cats)}
    df["category_enc"] = df["category"].map(category_enc).fillna(0).astype(int)
    
    # Target label: recommend if rating >= 4.0
    df["will_recommend"] = (df["rating"] >= 4.0).astype(int)
    
    # Introduce 15% label noise to simulate realistic classification limits
    np.random.seed(42)
    noise_mask = np.random.rand(len(df)) < 0.15
    df.loc[noise_mask, "will_recommend"] = 1 - df.loc[noise_mask, "will_recommend"]
    
    FEATURE_COLS = ["price", "rating", "category_enc"]
    X = df[FEATURE_COLS].values
    y = df["will_recommend"].values
    
    # Split training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train Random Forest Classifier
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)
    print("[SUCCESS] Random Forest classifier trained successfully.")
    
    # Perform prediction
    y_pred = clf.predict(X_test)
    
    # Step 3: Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    mcc = matthews_corrcoef(y_test, y_pred)
    
    cm = confusion_matrix(y_test, y_pred)
    class_report = classification_report(y_test, y_pred, zero_division=0)
    
    # 4. Generate clean text report
    report_lines = [
        "============================================================",
        "             CLASSIFICATION MODEL EVALUATION REPORT          ",
        "============================================================",
        "Model Evaluated : Random Forest Classifier (Storefront backend)",
        f"Evaluation Date : {np.datetime64('now')}",
        f"Train Samples   : {len(X_train)}",
        f"Test Samples    : {len(X_test)}",
        "------------------------------------------------------------",
        "METRICS SUMMARY:",
        f"  - Accuracy                     : {accuracy:.4f} ({accuracy * 100:.2f}%)",
        f"  - Precision (Class 1)          : {precision:.4f} ({precision * 100:.2f}%)",
        f"  - Recall (Class 1)             : {recall:.4f} ({recall * 100:.2f}%)",
        f"  - F1-Score                     : {f1:.4f} ({f1 * 100:.2f}%)",
        f"  - Matthews Correlation (MCC)   : {mcc:.4f}",
        "------------------------------------------------------------",
        "CONFUSION MATRIX:",
        f"  True Negative (TN)  : {cm[0][0]:<6} | False Positive (FP) : {cm[0][1]}",
        f"  False Negative (FN) : {cm[1][0]:<6} | True Positive (TP)  : {cm[1][1]}",
        "------------------------------------------------------------",
        "CLASSIFICATION REPORT DETAIL:",
        class_report,
        "============================================================"
    ]
    
    report_text = "\n".join(report_lines)
    
    # Print to console
    print("\n" + report_text)
    
    # Write to report file
    report_path = "evaluation_report.txt"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"\n[SUCCESS] Evaluation report saved to: {os.path.abspath(report_path)}")
    except Exception as e:
        print(f"\n[ERROR] Failed to save evaluation report to {report_path}: {e}")

if __name__ == "__main__":
    main()
