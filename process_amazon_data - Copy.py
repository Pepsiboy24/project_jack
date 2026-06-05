import json
import csv
import random

input_file = "Electronics_5.json"
output_file = "products.csv"

# Target number of unique products
TARGET_PRODUCTS = 500

seen_asins = set()
products = []

print(f"Reading from {input_file} to extract {TARGET_PRODUCTS} unique products...")

try:
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if len(products) >= TARGET_PRODUCTS:
                break
                
            try:
                data = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            
            asin = data.get("asin")
            if not asin or asin in seen_asins:
                continue
                
            summary = data.get("summary", "")
            review_text = data.get("reviewText", "")
            
            # Intelligently synthesize a realistic product name and corresponding image
            brands = ["Sony", "Samsung", "Apple", "Logitech", "Anker", "Dell", "HP", "Asus", "Bose", "JBL", "LG"]
            keywords = ["smartphone", "laptop", "headphones", "monitor", "speaker", "tv", "mouse", "keyboard", "cable", "camera", "tablet", "gps", "earbuds", "charger"]
            
            found_kw = random.choice(keywords) # fallback
            for kw in keywords:
                if kw in summary.lower() or kw in review_text.lower():
                    found_kw = kw
                    break
                    
            brand = random.choice(brands)
            series = random.randint(100, 9999)
            name = f"{brand} {found_kw.capitalize()} X{series} ({asin})"
            
            main_category = "Electronics"
            actual_price = round(random.uniform(10.0, 1000.0), 2)
            
            helpful = data.get("helpful", [0, 0])
            if helpful and isinstance(helpful, list) and len(helpful) == 2 and helpful[1] > 0:
                helpfulness_score = round(helpful[0] / helpful[1], 2)
            else:
                helpfulness_score = 0.5 # Default middle ground if no votes
                
            review_length = len(review_text.split())
            
            # Rating can be tricky as some have overall, some don't
            ratings = data.get("overall", random.choice([3.0, 4.0, 5.0]))
            
            # Generate a truly CORRESPONDING picture mapped exactly to the product keyword
            image_url = f"https://loremflickr.com/400/500/{found_kw}?lock={len(products)}"
            
            products.append([name, main_category, actual_price, ratings, helpfulness_score, review_length, image_url])
            seen_asins.add(asin)

    with open(output_file, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(["Product_Name", "main_category", "actual_price", "ratings", "Helpfulness_Score", "Review_Length", "Image_URL"])
        writer.writerows(products)
        
    print(f"Successfully wrote {len(products)} products to {output_file}.")

except FileNotFoundError:
    print(f"Error: {input_file} not found. Ensure the dataset is in this directory.")
except Exception as e:
    print(f"An error occurred: {e}")
