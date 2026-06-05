import sys

with open('script.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.strip() == "const recommendedProducts = await recRes.json();":
        new_lines.append(line)
        new_lines.append("        const allProducts = await allRes.json();\n\n")
        new_lines.append("        cachedRecProducts = recommendedProducts;\n")
        new_lines.append("        cachedAllProducts = allProducts;\n\n")
        new_lines.append("        renderProductGrids(cachedRecProducts, cachedAllProducts);\n\n")
        new_lines.append("    } catch (err) {\n")
        new_lines.append("        console.warn(\"Backend unavailable. No products to display.\", err);\n")
        new_lines.append("        cachedRecProducts = [];\n")
        new_lines.append("        cachedAllProducts = [];\n")
        new_lines.append("        recGrid.innerHTML = '<p style=\"padding: 20px;\">No recommended products available.</p>';\n")
        new_lines.append("        allGrid.innerHTML = '<p style=\"padding: 20px;\">No products available at this time.</p>';\n")
        new_lines.append("    }\n")
        new_lines.append("}\n\n")
        new_lines.append("window.showAnalysis = async function (prod) {\n")
        new_lines.append("    storefrontView.classList.remove('active');\n")
        new_lines.append("    analysisView.classList.add('active');\n\n")
        skip = True
        continue
    
    if skip and "document.getElementById('analysis-img').src = prod.img;" in line:
        skip = False
        new_lines.append(line)
        continue
        
    if not skip:
        new_lines.append(line)

with open('script.js', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("script.js fixed successfully!")
