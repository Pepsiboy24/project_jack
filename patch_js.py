import sys

with open('script.js', 'r', encoding='utf-8') as f:
    text = f.read()

bad_segment = """    try {
    document.querySelector('.ai-explanation').textContent = "Executing NLG translation layer...";"""

good_segment = """    try {
        const [recRes, allRes] = await Promise.all([
            fetch(`${API_URL}/recommendations`),
            fetch(`${API_URL}/all_products`)
        ]);

        const recommendedProducts = await recRes.json();
        const allProducts = await allRes.json();

        cachedRecProducts = recommendedProducts;
        cachedAllProducts = allProducts;

        renderProductGrids(cachedRecProducts, cachedAllProducts);

    } catch (err) {
        console.warn("Backend unavailable. No products to display.", err);
        cachedRecProducts = [];
        cachedAllProducts = [];
        recGrid.innerHTML = '<p style="padding: 20px;">No recommended products available.</p>';
        allGrid.innerHTML = '<p style="padding: 20px;">No products available at this time.</p>';
    }
}

window.showAnalysis = async function (prod) {
    storefrontView.classList.remove('active');
    analysisView.classList.add('active');

    document.getElementById('analysis-img').src = prod.img;
    document.getElementById('analysis-name').textContent = prod.name;
    document.getElementById('analysis-price').textContent = `₦${prod.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

    const shapBars = document.getElementById('shap-bars');
    const limeBars = document.getElementById('lime-bars');
    if (limeBars) limeBars.innerHTML = '';
    shapBars.innerHTML = '<p>Generating Hybrid Explanation via Python backend...</p>';
    document.querySelector('.ai-explanation').textContent = "Executing NLG translation layer...";"""

if bad_segment in text:
    text = text.replace(bad_segment, good_segment)
    with open('script.js', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed successfully!")
else:
    print("Bad segment not found! Text is:\n", text[15000:16000])
