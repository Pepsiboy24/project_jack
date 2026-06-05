import pandas as pd
import shutil
import glob
import os

print("Starting update script...")
df = pd.read_csv('products.csv')

# The added IDs from earlier were 5003, 5004, 5005, 5006
new_ids = [5003, 5004, 5005, 5006]

# Keep items: not footwear, OR in new_ids
category_mask = df['main_category'] != 'Footwear'
id_mask = df['id'].isin(new_ids)
df_filtered = df[category_mask | id_mask].copy()

# Ensure images dir exists
images_dest = "images"
if not os.path.exists(images_dest):
    os.makedirs(images_dest)

# Map our IDs to the generated image artifacts
artifact_dir = r"C:\Users\Hp\.gemini\antigravity\brain\4c68c16d-27bc-45f1-ae29-c4dabc503e32"
mapping = {
    5003: ("black_leather_oxford", "black_leather_oxford*.png"),
    5004: ("black_knit_sneaker", "black_knit_sneaker*.png"),
    5005: ("navy_knit_sneaker", "navy_knit_sneaker*.png"),
    5006: ("floral_converse", "floral_converse*.png")
}

for item_id, (name, pattern) in mapping.items():
    # find artifact generated
    files = glob.glob(os.path.join(artifact_dir, pattern))
    if files:
        src = files[0]
        dest_filename = f"{name}.png"
        dest = os.path.join(images_dest, dest_filename)
        shutil.copy(src, dest)
        
        # update dataframe to point to local images path mapped by FastAPI
        # Since FastAPI serves StaticFiles(directory="images") at /images
        # Wait, the frontend might prepend the backend URL. The original URLs were https://...
        # So we should use an absolute path for local backend, which is /images/name.png or the full URL.
        # Given frontend fetch is to backend 8001:
        img_url = f"http://localhost:8001/images/{dest_filename}"
        df_filtered.loc[df_filtered['id'] == item_id, 'Image_URL'] = img_url
        print(f"Updated {name}")

df_filtered.to_csv('products.csv', index=False)
print("Done filtering and updating images.")
