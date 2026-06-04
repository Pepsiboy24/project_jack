with open('script.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Update payload structure in showAnalysis
old_payload = """        const payload = {
            name: prod.name,
            rating: prod.rating,
            price: prod.price,
            helpfulness_score: prod.helpfulness_score,
            review_length: prod.review_length
        };"""

new_payload = """        const payload = {
            name: prod.name,
            rating: prod.rating,
            price: prod.price,
            category: prod.category || 'Accessories',
            about_product: prod.about_product || 'Premium fashion item.'
        };"""

js = js.replace(old_payload, new_payload)

# Update offline mock array bounds to 5000 and categories!
old_offline_brands = 'const brands = ["Amazon Basic", "Anker", "Sony", "Samsung", "Apple", "Premium", "Smart"];'
new_offline_brands = 'const brands = ["Puma", "Titan", "Adidas", "Nike", "Vans", "Premium", "Levis"];'
js = js.replace(old_offline_brands, new_offline_brands)

old_offline_types = 'const genericTypes = ["Smartphone", "Headphones", "Watch", "Earbuds", "Charger", "Speaker", "Monitor", "Laptop"];'
new_offline_types = 'const genericTypes = ["Shoes", "Bags", "Accessories", "Sandal", "Flip Flops", "Wallets", "Belts", "Handbag"];'
js = js.replace(old_offline_types, new_offline_types)

old_offline_categories = 'const categories = ["Electronics", "Smart Home", "Accessories", "Audio"];'
new_offline_categories = 'const categories = ["Footwear", "Apparel", "Accessories", "Bags"];'
js = js.replace(old_offline_categories, new_offline_categories)

old_mock_push = """            mockProducts.push({
                id: i,
                name: `${brand} ${type} ${i}`,
                price: Math.random() * (1000 - 10) + 10,
                rating: Math.floor(Math.random() * (5 - 3) + 3) + 0.5,
                img: `https://loremflickr.com/400/500/tech?lock=${i}`,
                category: categories[catKey],
                helpfulness_score: 0.5,
                review_length: 20
            });"""

new_mock_push = """            mockProducts.push({
                id: i,
                name: `${brand} ${type} X${i}`,
                price: Math.random() * (300 - 10) + 10,
                rating: Math.floor(Math.random() * (5 - 3) + 3) + 0.5,
                img: `https://loremflickr.com/400/500/fashion?lock=${i}`,
                category: categories[catKey],
                helpfulness_score: 0,
                review_length: 0,
                about_product: `This premium item is exceptionally designed for stylish everyday wear. Perfectly crafted by ${brand} to combine comfort and aesthetics.`
            });"""

js = js.replace(old_mock_push, new_mock_push)

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("Updated script.js successfully!")
