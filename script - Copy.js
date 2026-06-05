// Elements
const loginView = document.getElementById('login-view');
const verifyView = document.getElementById('verify-view');
const appContainer = document.getElementById('app-container');
const storefrontView = document.getElementById('storefront-view');

const loginForm = document.getElementById('login-form');
const toggleAuth = document.getElementById('toggle-auth');
const toggleText = document.getElementById('toggle-text');
const authBtn = document.getElementById('auth-btn');
const authTitle = document.getElementById('auth-title');
const authError = document.getElementById('auth-error');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const confirmPasswordInput = document.getElementById('confirm-password');
const passwordTick = document.getElementById('password-tick');

const verifyForm = document.getElementById('verify-form');
const verifyCodeInput = document.getElementById('verify-code');
const verifyBtn = document.getElementById('verify-btn');
const verifyError = document.getElementById('verify-error');
const verifySuccess = document.getElementById('verify-success');
const resendBtn = document.getElementById('resend-btn');
const resendTimer = document.getElementById('resend-timer');

let resendInterval = null;
let resendSeconds = 60;

function startResendTimer() {
    resendBtn.style.pointerEvents = 'none';
    resendBtn.style.color = 'var(--text-muted)';
    resendTimer.style.display = 'inline';
    resendSeconds = 60;

    resendTimer.textContent = `(${resendSeconds}s)`;

    clearInterval(resendInterval);
    resendInterval = setInterval(() => {
        resendSeconds--;
        resendTimer.textContent = `(${resendSeconds}s)`;

        if (resendSeconds <= 0) {
            clearInterval(resendInterval);
            resendBtn.style.pointerEvents = 'auto';
            resendBtn.style.color = 'var(--primary-color)';
            resendTimer.style.display = 'none';
        }
    }, 1000);
}

const profileView = document.getElementById('profile-view');
const navStore = document.getElementById('nav-store');

let cart = [];
const navCart = document.getElementById('nav-cart');
const cartOverlay = document.getElementById('cart-overlay');
const cartDrawer = document.getElementById('cart-drawer');
const closeCartBtn = document.getElementById('close-cart');

function toggleCart() {
    const isOpen = cartDrawer.classList.contains('open');
    if (isOpen) {
        cartDrawer.classList.remove('open');
        cartOverlay.classList.remove('show');
    } else {
        renderCartItems();
        cartDrawer.classList.add('open');
        cartOverlay.classList.add('show');
    }
}

navCart.addEventListener('click', toggleCart);
cartOverlay.addEventListener('click', toggleCart);
closeCartBtn.addEventListener('click', toggleCart);
const floatingCart = document.getElementById('floating-cart');
if (floatingCart) floatingCart.addEventListener('click', toggleCart);

window.addToCart = function (productStr) {
    const prod = JSON.parse(decodeURIComponent(productStr));
    cart.push(prod);

    const badge = document.getElementById('cart-badge-amz');
    if (badge) {
        badge.textContent = cart.length;
    }
    const floatBadge = document.getElementById('cart-badge-floating');
    if (floatBadge) floatBadge.textContent = cart.length;

    navCart.style.transition = 'transform 0.2s';
    navCart.style.transform = 'scale(1.1)';
    setTimeout(() => navCart.style.transform = 'scale(1)', 200);
};

window.removeFromCart = function (index) {
    cart.splice(index, 1);
    renderCartItems();

    const badge = document.getElementById('cart-badge-amz');
    if (badge) {
        badge.textContent = cart.length;
    }
    const floatBadge = document.getElementById('cart-badge-floating');
    if (floatBadge) floatBadge.textContent = cart.length;
};

function renderCartItems() {
    const list = document.getElementById('cart-items');
    const totalEl = document.getElementById('cart-total-price');
    list.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        list.innerHTML = '<div class="empty-cart">Your cart is empty. Pick something awesome!</div>';
        totalEl.textContent = '$0.00';
        return;
    }

    cart.forEach((item, index) => {
        total += item.price;
        const el = document.createElement('div');
        el.className = 'cart-item';
        el.innerHTML = `
            <img src="${item.img}" alt="${item.name}">
            <div class="cart-item-info">
                <h4>${item.name}</h4>
                <div class="price">$${item.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            </div>
            <button class="remove-btn" onclick="removeFromCart(${index})">✕</button>
        `;
        list.appendChild(el);
    });

    totalEl.textContent = `$${total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

const paypalContainer = document.getElementById('paypal-button-container');
const checkoutBtn = document.getElementById('checkout-btn');

if (paypalContainer) {
    if (checkoutBtn) checkoutBtn.style.display = 'none';
    
    paypal.Buttons({
        style: {
            layout: 'vertical',
            color:  'blue',
            shape:  'rect',
            label:  'paypal'
        },
        createOrder: function(data, actions) {
            if (cart.length === 0) {
                alert('Your cart is empty! Add some items before processing checkout.');
                throw new Error('Cart empty');
            }
            
            // Calculate total in USD directly
            let totalAmountUSD = 0;
            cart.forEach(item => totalAmountUSD += item.price);
            
            totalAmountUSD = totalAmountUSD.toFixed(2);
            
            if(parseFloat(totalAmountUSD) <= 0.00) totalAmountUSD = "0.01";

            return actions.order.create({
                purchase_units: [{
                    amount: {
                        value: totalAmountUSD
                    }
                }]
            });
        },
        onApprove: function(data, actions) {
            return actions.order.capture().then(function(details) {
                let message = 'Payment API complete! Capture Reference: ' + details.id;
                alert(message + '\n\n🚀 Thank you for shopping with XAI E-Commerce, ' + details.payer.name.given_name + '!');
                
                cart = [];
                renderCartItems();
                toggleCart();
            });
        },
        onError: function (err) {
            console.error("PayPal Error:", err);
            if(!err.message || !err.message.includes('Cart empty')) {
                alert("PayPal gateway closed or encountered an error.");
            }
        }
    }).render('#paypal-button-container');
}

if (navStore) {
    navStore.addEventListener('click', () => {
        profileView.classList.remove('active');
        storefrontView.classList.add('active');
    });
}

const dropProfile = document.getElementById('drop-profile');
if (dropProfile) {
    dropProfile.addEventListener('click', (e) => {
        e.preventDefault();
        storefrontView.classList.remove('active');
        profileView.classList.add('active');
    });
}

const dropOrders = document.getElementById('drop-orders');
if (dropOrders) {
    dropOrders.addEventListener('click', (e) => {
        e.preventDefault();
        storefrontView.classList.remove('active');
        profileView.classList.add('active');
        setTimeout(() => {
            const txList = document.getElementById('transaction-list');
            if (txList) txList.scrollIntoView({behavior: 'smooth', block: 'center'});
        }, 100);
    });
}

const dropLogout = document.getElementById('drop-logout');
if (dropLogout) {
    dropLogout.addEventListener('click', (e) => {
        e.preventDefault();
        if (logoutBtn) logoutBtn.click();
    });
}

const themeToggle = document.getElementById('theme-toggle');
const xaiToggle = document.getElementById('xai-toggle');

if (xaiToggle) {
    // Load saved preference
    const savedXai = localStorage.getItem('xai_mode');
    if (savedXai !== null) {
        xaiToggle.checked = savedXai === 'true';
    }

    xaiToggle.addEventListener('change', () => {
        localStorage.setItem('xai_mode', xaiToggle.checked);
        renderStorefront();
    });
}

// Helper to apply theme
function applyTheme(isDark) {
    if (isDark) {
        document.documentElement.style.setProperty('--bg-color', '#0B1121');
        document.documentElement.style.setProperty('--card-bg', 'rgba(30, 41, 59, 0.7)');
        document.documentElement.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.1)');
        document.documentElement.style.setProperty('--text-main', '#f8fafc');
        document.documentElement.style.setProperty('--text-muted', '#94a3b8');
    } else {
        document.documentElement.style.setProperty('--bg-color', '#f1f5f9');
        document.documentElement.style.setProperty('--card-bg', 'rgba(255, 255, 255, 0.7)');
        document.documentElement.style.setProperty('--border-color', 'rgba(0, 0, 0, 0.1)');
        document.documentElement.style.setProperty('--text-main', '#0f172a');
        document.documentElement.style.setProperty('--text-muted', '#64748b');
    }
}

if (themeToggle) {
    // Load saved preference
    const savedTheme = localStorage.getItem('theme_dark');
    if (savedTheme !== null) {
        themeToggle.checked = savedTheme === 'true';
    }
    applyTheme(themeToggle.checked);

    themeToggle.addEventListener('change', (e) => {
        localStorage.setItem('theme_dark', e.target.checked);
        applyTheme(e.target.checked);
    });
}

const recGrid = document.getElementById('recommended-grid');
const allGrid = document.getElementById('all-grid');



const API_URL = "http://127.0.0.1:8001";

const inputSearch = document.getElementById('search-bar');
let cachedAllProducts = [];
let cachedRecProducts = [];

let currentCategoryFilter = "All";

// Derive manual products list from the cache (products added via the modal)
function getManualProducts() {
    try {
        const localStr = localStorage.getItem('manual_products');
        return localStr ? JSON.parse(localStr) : [];
    } catch (e) {
        return [];
    }
}

function showCategoryView(category) {
    const categoryFilterBar = document.querySelector('.category-filters');
    const addProductBar = document.querySelector('#open-add-product-modal')?.parentElement;
    const recSection = document.getElementById('rec-section');
    const allSection = document.getElementById('all-section');
    const categoryBackBar = document.getElementById('category-back-bar');
    const categoryTitle = document.getElementById('category-view-title');

    if (category === "All") {
        // Restore normal layout
        if (categoryFilterBar) categoryFilterBar.style.display = '';
        if (addProductBar) addProductBar.style.display = '';
        if (recSection) recSection.style.display = '';
        if (allSection) allSection.style.display = '';
        if (categoryBackBar) categoryBackBar.style.display = 'none';

        // Restore filter button active state
        document.querySelectorAll('.filter-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.category === 'All');
        });

        renderProductGrids(cachedRecProducts, cachedAllProducts);
    } else {
        // Category-specific view: only manual products in this category
        if (categoryFilterBar) categoryFilterBar.style.display = 'none';
        if (addProductBar) addProductBar.style.display = 'none';
        if (recSection) recSection.style.display = 'none';
        if (categoryBackBar) categoryBackBar.style.display = 'flex';
        if (categoryTitle) categoryTitle.textContent = category;

        const filtered = cachedAllProducts.filter(p => p.category === category);

        if (allSection) allSection.style.display = '';
        allGrid.innerHTML = '';

        if (filtered.length === 0) {
            allGrid.innerHTML = `<p style="padding: 20px; color: var(--text-muted);">No products in ${category} yet. Add some!</p>`;
        } else {
            filtered.forEach(prod => {
                const card = document.createElement('div');
                card.className = 'card glass hover-effect';
                card.innerHTML = `
                    <div class="card-content" style="padding-bottom: 5px;">
                        <h4 style="margin-bottom: 0;">${prod.name}</h4>
                    </div>
                    <img src="${prod.img}" alt="${prod.name}" style="border-radius: 0;">
                    <div class="card-content" style="padding-top: 10px;">
                        <div class="price" style="margin-bottom:12px; font-weight:bold; color:var(--text-main);">$${prod.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                        <button class="primary-btn" style="margin-top:auto;" onclick="addToCart('${encodeURIComponent(JSON.stringify(prod)).replace(/'/g, "%27")}')">🛒 Add to Cart</button>
                    </div>
                `;
                allGrid.appendChild(card);
            });
        }
    }
}

function applyFilters() {
    const query = inputSearch ? inputSearch.value.toLowerCase() : "";
    
    if (currentCategoryFilter !== "All") {
        // Handled by showCategoryView
        return;
    }
    
    const filteredAll = cachedAllProducts.filter(p => {
        return p.name.toLowerCase().includes(query) || p.category.toLowerCase().includes(query);
    });
    
    const filteredRec = cachedRecProducts.filter(p => {
        return p.name.toLowerCase().includes(query) || p.category.toLowerCase().includes(query);
    });

    renderProductGrids(filteredRec, filteredAll);
}

if (inputSearch) {
    inputSearch.addEventListener('input', applyFilters);
}

const filterBtns = document.querySelectorAll('.filter-btn');
filterBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
        currentCategoryFilter = e.target.dataset.category;
        showCategoryView(currentCategoryFilter);
    });
});

const categoryBackBtn = document.getElementById('category-back-btn');
if (categoryBackBtn) {
    categoryBackBtn.addEventListener('click', () => {
        currentCategoryFilter = 'All';
        showCategoryView('All');
    });
}

function renderProductGrids(recProducts, allProducts) {
    recGrid.innerHTML = '';
    recProducts.slice(0, 8).forEach(prod => {
        const card = document.createElement('div');
        card.className = 'card glass hover-effect';
        card.style.position = 'relative';
        
        card.innerHTML = `
            <div class="card-content" style="padding-bottom: 5px;">
                <h4 style="margin-bottom: 0;">${prod.name}</h4>
            </div>
            <img src="${prod.img}" alt="${prod.name}" style="border-radius: 0;">
            <div class="card-content" style="padding-top: 10px;">
                <div class="price" style="margin-bottom:12px;">$${prod.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                <div style="display:flex; gap:10px; margin-top: auto;">
                    <button class="primary-btn" style="flex:1; margin-top:0;" onclick="addToCart('${encodeURIComponent(JSON.stringify(prod)).replace(/'/g, "%27")}')">🛒 Add to Cart</button>
                </div>
            </div>
        `;
        recGrid.appendChild(card);
    });

    allGrid.innerHTML = '';
    allProducts.forEach(prod => {
        const card = document.createElement('div');
        card.className = 'card glass hover-effect';
        card.innerHTML = `
            <div class="card-content" style="padding-bottom: 5px;">
                <h4 style="margin-bottom: 0;">${prod.name}</h4>
            </div>
            <img src="${prod.img}" alt="${prod.name}" style="border-radius: 0;">
            <div class="card-content" style="padding-top: 10px;">
                <div class="price" style="margin-bottom:12px; font-weight:bold; color:var(--text-main);">$${prod.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                <button class="primary-btn" style="margin-top:auto;" onclick="addToCart('${encodeURIComponent(JSON.stringify(prod)).replace(/'/g, "%27")}')">🛒 Add to Cart</button>
            </div>
        `;
        allGrid.appendChild(card);
    });
}

let isLogin = true;
let emailForVerification = "";
let currentUserEmail = "";

toggleAuth.addEventListener('click', (e) => {
    e.preventDefault();
    isLogin = !isLogin;
    if (isLogin) {
        authTitle.textContent = "🧠 XAI E-Commerce";
        authBtn.textContent = "Sign In";
        toggleText.textContent = "Don't have an account? ";
        toggleAuth.textContent = "Sign Up";
        confirmPasswordInput.style.display = 'none';
        confirmPasswordInput.required = false;
        passwordTick.style.display = 'none';
        passwordInput.value = '';
    } else {
        authTitle.textContent = "Sign Up";
        authBtn.textContent = "Create Account";
        toggleText.textContent = "Already have an account? ";
        toggleAuth.textContent = "Log In";
        emailInput.value = "";
        passwordInput.value = "";
        confirmPasswordInput.value = "";
        confirmPasswordInput.style.display = 'block';
        confirmPasswordInput.required = true;
    }
    authError.style.display = 'none';
});

// Bypass regex checks to allow any password
const strongPasswordRegex = /.*/;

passwordInput.addEventListener('input', () => {
    if (!isLogin) {
        if (strongPasswordRegex.test(passwordInput.value)) {
            passwordTick.style.display = 'block';
        } else {
            passwordTick.style.display = 'none';
        }
    }
});

// Show/Hide logic
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    authError.style.display = 'none';

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!isLogin && !strongPasswordRegex.test(password)) {
        authError.textContent = "Password must be at least 8 chars, 1 uppercase, 1 lowercase, 1 number, and 1 special character.";
        authError.style.display = 'block';
        return;
    }

    if (!isLogin && password !== confirmPasswordInput.value) {
        authError.textContent = "Passwords do not match.";
        authError.style.display = 'block';
        return;
    }

    authBtn.disabled = true;
    authBtn.textContent = "Loading...";

    try {
        const endpoint = isLogin ? "/login" : "/signup";
        const res = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Authentication Failed");
        }

        if (!isLogin) {
            emailForVerification = email;
            loginView.classList.remove('active');
            verifyView.classList.add('active');
            startResendTimer();
        } else {
            currentUserEmail = email;
            loginView.classList.remove('active');
            appContainer.classList.add('active');
            renderStorefront();
        }
    } catch (err) {
        if (err.message === "Failed to fetch" || err.message.includes("Failed to fetch") || err.message.includes("Load failed")) {
            console.warn("Backend unavailable. Proceeding with offline mock mode.");
            currentUserEmail = email || "testuser@amazon.com";
            loginView.classList.remove('active');
            appContainer.classList.add('active');
            renderStorefront();
        } else {
            authError.textContent = err.message;
            authError.style.display = 'block';
        }
    } finally {
        authBtn.disabled = false;
        authBtn.textContent = isLogin ? "Sign In" : "Create Account";
    }
});

verifyForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    verifyError.style.display = 'none';

    verifyBtn.disabled = true;
    verifyBtn.textContent = "Verifying...";

    try {
        const res = await fetch(`${API_URL}/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: emailForVerification, code: verifyCodeInput.value.trim() })
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Verification Failed");
        }

        verifyView.classList.remove('active');
        appContainer.classList.add('active');
        currentUserEmail = emailForVerification;
        renderStorefront();
    } catch (err) {
        verifyError.textContent = err.message;
        verifyError.style.display = 'block';
    } finally {
        verifyBtn.disabled = false;
        verifyBtn.textContent = "Verify Account";
    }
});

resendBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    verifyError.style.display = 'none';
    verifySuccess.style.display = 'none';

    if (resendBtn.style.pointerEvents === 'none') return;

    try {
        const res = await fetch(`${API_URL}/resend_code`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: emailForVerification })
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Failed to resend code");
        }

        verifySuccess.textContent = "Code resent! Check your terminal logs.";
        verifySuccess.style.display = 'block';
        startResendTimer();

    } catch (err) {
        verifyError.textContent = err.message;
        verifyError.style.display = 'block';
    }
});

async function renderStorefront() {
    recGrid.innerHTML = '<p style="padding: 20px;">Loading recommendations...</p>';
    allGrid.innerHTML = '<p style="padding: 20px;">Loading products...</p>';

    // Load live model metrics into the banner if elements exist
    try {
        const mRes = await fetch(`${API_URL}/trust_metrics`);
        if (mRes.ok) {
            const m = await mRes.json();
            const fmt = v => (v !== undefined && v !== null) ? (v * 100).toFixed(1) + '%' : '—';
            const el = id => document.getElementById(id);
            if (el('metric-accuracy'))  el('metric-accuracy').innerHTML  = `Accuracy: <strong style="color:#22c55e">${fmt(m.accuracy)}</strong>`;
            if (el('metric-precision')) el('metric-precision').innerHTML = `Precision: <strong style="color:#38bdf8">${fmt(m.precision)}</strong>`;
            if (el('metric-recall'))    el('metric-recall').innerHTML    = `Recall: <strong style="color:#f59e0b">${fmt(m.recall)}</strong>`;
            if (el('metric-f1'))        el('metric-f1').innerHTML        = `F1: <strong style="color:#a78bfa">${fmt(m.f1)}</strong>`;
            if (el('metric-samples'))   el('metric-samples').textContent = `Training samples: ${m.training_samples || '—'}`;
        }
    } catch (e) {
        console.warn('Could not load trust metrics:', e);
    }

    // Fetch Profile
    try {
        if (currentUserEmail) {
            const profileRes = await fetch(`${API_URL}/profile?email=${encodeURIComponent(currentUserEmail)}`);
            if (profileRes.ok) {
                const profileData = await profileRes.json();
                if (editNameInput) editNameInput.value = profileData.name;
                if (editEmailInput) editEmailInput.value = profileData.email;

                // Update premium social profile elements
                const socialName = document.getElementById('social-name');
                const socialEmail = document.getElementById('social-email');
                const socialAvatar = document.getElementById('social-avatar');
                const navAvatar = document.getElementById('nav-avatar');
                
                if (socialName) socialName.textContent = profileData.name;
                if (socialEmail) socialEmail.textContent = profileData.email;
                
                const avatarUrl = `https://ui-avatars.com/api/?name=${encodeURIComponent(profileData.name)}&background=3b82f6&color=fff&size=120`;
                const navAvatarUrl = `https://ui-avatars.com/api/?name=${encodeURIComponent(profileData.name)}&background=3b82f6&color=fff&size=40`;
                if (socialAvatar) socialAvatar.src = avatarUrl;
                if (navAvatar) navAvatar.src = navAvatarUrl;

                const txList = document.getElementById('transaction-list');
                if (txList) txList.innerHTML = '';
                let totalSpent = 0;

                if (profileData.transactions && profileData.transactions.length > 0) {
                    profileData.transactions.forEach((tx, index) => {
                        totalSpent += tx.amount;
                        
                        const statuses = ['Success', 'Pending', 'Delivered'];
                        const status = statuses[index % 3];
                        let statusClass = 'status-success';
                        if (status === 'Pending') statusClass = 'status-pending';

                        const trHTML = `
                            <tr>
                                <td>${tx.date}</td>
                                <td style="font-weight: 500;">${tx.item}</td>
                                <td>$${tx.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                                <td><span class="status-pill ${statusClass}">${status}</span></td>
                            </tr>
                        `;
                        if (txList) txList.innerHTML += trHTML;
                    });
                    
                    const statTotalOrders = document.getElementById('social-stat-orders');
                    const statTotalSpent = document.getElementById('social-stat-spent');
                    if (statTotalOrders) statTotalOrders.textContent = profileData.transactions.length;
                    if (statTotalSpent) statTotalSpent.textContent = '$' + totalSpent.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                } else {
                    if (txList) txList.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 20px;">No transactions yet</td></tr>';
                    const statTotalOrders = document.getElementById('social-stat-orders');
                    const statTotalSpent = document.getElementById('social-stat-spent');
                    if (statTotalOrders) statTotalOrders.textContent = "0";
                    if (statTotalSpent) statTotalSpent.textContent = "$0.00";
                }
            }
        }
    } catch (err) {
        console.error("Profile fetch error:", err);
    }

    try {
        const [recRes, allRes] = await Promise.all([
            fetch(`${API_URL}/recommendations?email=${encodeURIComponent(currentUserEmail)}`),
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

    // Merge with local storage manual products to support offline mode perfectly
    try {
        const localManualStr = localStorage.getItem('manual_products');
        if (localManualStr) {
            const localManual = JSON.parse(localManualStr);
            // Deduplicate if backend also returned them (backend wins)
            const backendNames = new Set(cachedAllProducts.map(p => p.name));
            const offlineManual = localManual.filter(p => !backendNames.has(p.name));
            
            cachedAllProducts = [...offlineManual, ...cachedAllProducts];
            cachedRecProducts = [...offlineManual, ...cachedRecProducts];
            
            if (offlineManual.length > 0) {
                renderProductGrids(cachedRecProducts, cachedAllProducts);
            }
        }
    } catch (e) {
        console.error("Failed to load offline manual products", e);
    }
}

// Explanation Overlay Modal Implementation (replaces full page analysisView)
window.showAnalysis = window.showExplanation = async function (prodArg) {
    const overlay = document.getElementById('explanation-overlay');
    if (overlay) {
        overlay.style.display = 'flex';
    }
    let prod = prodArg;
    if (typeof prod === 'string') {
        try {
            prod = JSON.parse(decodeURIComponent(prod));
        } catch (e) {
            console.error("Failed to parse product string in showExplanation", e);
        }
    }
    if (!overlay) return;

    const productNameEl = document.getElementById('explanation-product-name');
    if (productNameEl) productNameEl.textContent = prod.name;

    const shapBars = document.getElementById('modal-shap-bars');
    const limeBars = document.getElementById('modal-lime-bars');
    const expContent = document.getElementById('explanation-content');

    if (shapBars) shapBars.innerHTML = '<p style="color:var(--text-muted); font-size: 13px;">Analyzing SHAP...</p>';
    if (limeBars) limeBars.innerHTML = '<p style="color:var(--text-muted); font-size: 13px;">Analyzing LIME...</p>';
    if (expContent) expContent.textContent = "Executing NLG translation layer...";

    try {
        const res = await fetch(`${API_URL}/explain`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: prod.name,
                rating: prod.rating || 5.0,
                price: prod.price,
                category: prod.category,
                about_product: prod.description || prod.about_product || "A stylish premium item.",
                email: currentUserEmail
            })
        });

        const data = await res.json();

        if (shapBars) shapBars.innerHTML = '';
        if (limeBars) limeBars.innerHTML = '';

        if (shapBars && data.shap) {
            drawShapBar(shapBars, "Rating", data.shap.Rating || 0.01);
            drawShapBar(shapBars, "Category", data.shap.Category || 0.01);
            drawShapBar(shapBars, "Price", data.shap.Price || -0.01, true); // Reverse color for price
        }

        if (limeBars && data.lime) {
            drawShapBar(limeBars, "Rating", data.lime.Rating || 0.01);
            drawShapBar(limeBars, "Category", data.lime.Category || 0.01);
            drawShapBar(limeBars, "Price", data.lime.Price || -0.01, true);
        }

        if (expContent) {
            expContent.innerHTML = data.explanation.replace(/\*\*/g, '<strong>').replace(/\*\*/g, '</strong>');
        }

    } catch (err) {
        console.error("Error fetching explanation:", err);
        if (shapBars) shapBars.innerHTML = '<p style="color:#ef4444; font-size: 13px;">Failed to generate SHAP metrics.</p>';
        if (limeBars) limeBars.innerHTML = '<p style="color:#ef4444; font-size: 13px;">Failed to generate LIME metrics.</p>';
        if (expContent) expContent.textContent = "Error communicating with the Natural Language Generator layer.";
    }
};

function drawShapBar(container, name, value, reverse = false) {
    let isPos = value > 0;
    if (reverse) isPos = !isPos;

    // Scale impact multiplier to visualize nicely on max/min score range
    const absValue = Math.abs(value);
    const widthRaw = absValue * 250;
    const width = Math.min(100, Math.max(5, widthRaw));

    const color = isPos ? '#22c55e' : '#ef4444';

    const wrap = document.createElement('div');
    wrap.className = 'shap-bar-wrap';

    wrap.innerHTML = `
        <div class="shap-label"><strong>${name}</strong>: ${value.toFixed(3)}</div>
        <div class="shap-track">
            <div class="shap-fill" style="width: 0%; background-color: ${color};"></div>
        </div>
    `;
    container.appendChild(wrap);

    setTimeout(() => {
        const fill = wrap.querySelector('.shap-fill');
        if (fill) fill.style.width = width + '%';
    }, 50);
}

// Close explanation modal on clicking backdrop
const explanationOverlay = document.getElementById('explanation-overlay');
if (explanationOverlay) {
    explanationOverlay.addEventListener('click', (e) => {
        if (e.target === explanationOverlay) {
            explanationOverlay.style.display = 'none';
        }
    });
}

// --- Profile & Logout logic ---
const logoutBtn = document.getElementById('logout-btn');
const editProfileForm = document.getElementById('edit-profile-form');
const editNameInput = document.getElementById('edit-name');
const editEmailInput = document.getElementById('edit-email');

let saveTimeout = null;
const saveStatus = document.getElementById('save-status');

async function autoSaveProfile() {
    if (saveStatus) {
        saveStatus.textContent = 'Saving...';
        saveStatus.style.color = 'var(--text-muted)';
        saveStatus.style.opacity = '1';
    }

    try {
        await fetch(`${API_URL}/update_profile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: editEmailInput.value, name: editNameInput.value })
        });

        if (saveStatus) {
            saveStatus.textContent = '✓ Saved automatically';
            saveStatus.style.color = 'var(--success)';
            setTimeout(() => { saveStatus.style.opacity = '0'; }, 2000);
        }
    } catch (err) {
        console.error("Save error:", err);
        if (saveStatus) {
            saveStatus.textContent = '✗ Error saving';
            saveStatus.style.color = 'var(--danger)';
            setTimeout(() => { saveStatus.style.opacity = '0'; }, 2000);
        }
    }
}

if (editNameInput) {
    editNameInput.addEventListener('input', () => {
        if (saveStatus) {
            saveStatus.textContent = 'Typing...';
            saveStatus.style.color = 'var(--text-muted)';
            saveStatus.style.opacity = '1';
        }
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(autoSaveProfile, 1000);
    });
}

if (editProfileForm) {
    editProfileForm.addEventListener('submit', (e) => {
        e.preventDefault();
        clearTimeout(saveTimeout);
        autoSaveProfile();
    });
}

if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        currentUserEmail = "";
        cart = [];
        renderCartItems();

        document.getElementById('app-container').classList.remove('active');
        profileView.classList.remove('active');

        storefrontView.classList.add('active');
        document.getElementById('login-view').classList.add('active');

        document.getElementById('email').value = "";
        document.getElementById('password').value = "";
    });
}

// Add Product Modal Logic
const addProductModal = document.getElementById('add-product-overlay');
const openAddProductBtn = document.getElementById('open-add-product-modal');
const closeAddProductBtn = document.getElementById('close-add-product');
const addProductForm = document.getElementById('add-product-form');

if (openAddProductBtn) {
    openAddProductBtn.addEventListener('click', () => {
        addProductModal.style.display = 'flex';
        setTimeout(() => {
            addProductModal.classList.add('show');
        }, 10);
    });
}

if (closeAddProductBtn) {
    closeAddProductBtn.addEventListener('click', () => {
        addProductModal.classList.remove('show');
        setTimeout(() => {
            addProductModal.style.display = 'none';
        }, 400);
    });
}

if (addProductForm) {
    addProductForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const photoInput = document.getElementById('add-product-photo');
        if (!photoInput.files || photoInput.files.length === 0) {
            alert("Please select a photo first.");
            return;
        }
        
        let img = "";
        try {
            const file = photoInput.files[0];
            img = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result);
                reader.onerror = () => reject("Error reading file");
                reader.readAsDataURL(file);
            });
        } catch (err) {
            alert(err);
            return;
        }
        
        const name = document.getElementById('add-product-name').value;
        const price = parseFloat(document.getElementById('add-product-price').value);
        const desc = document.getElementById('add-product-desc').value;
        const assignedCategory = document.getElementById('add-product-category').value;
        
        const newProduct = {
            id: 'man_' + Date.now(),
            name: name,
            img: img,
            price: price,
            category: assignedCategory,
            description: desc,
            rating: 5.0, 
            helpfulness_score: 1.0,
            review_length: desc.split(' ').length
        };
        
        try {
            await fetch(`${API_URL}/add_product`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    price: price,
                    category: assignedCategory,
                    description: desc,
                    image: img
                })
            });
        } catch (err) {
            console.warn("Backend not available for saving product, doing local saving only.");
        }
        
        // Add locally so it appears immediately
        cachedAllProducts.unshift(newProduct);
        cachedRecProducts.unshift(newProduct); // Add to recommendations grid too visually
        
        // Save to offline storage so it persists even without backend
        try {
            const localManualStr = localStorage.getItem('manual_products');
            let localManual = localManualStr ? JSON.parse(localManualStr) : [];
            localManual.unshift(newProduct);
            localStorage.setItem('manual_products', JSON.stringify(localManual));
        } catch (e) {
            console.warn("Failed to save to local storage", e);
        }
        
        alert(`Product added successfully under ${assignedCategory} category!`);
        
        // Reset and close
        addProductForm.reset();
        addProductModal.classList.remove('show');
        setTimeout(() => {
            addProductModal.style.display = 'none';
        }, 400);
        
        // Jump UI to the category the user just added to
        currentCategoryFilter = assignedCategory;
        const filterBtns = document.querySelectorAll('.filter-btn');
        filterBtns.forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.category === assignedCategory) {
                btn.classList.add('active');
            }
        });
        
        // Refresh grids
        if (currentCategoryFilter === "All") {
            applyFilters();
        } else {
            showCategoryView(currentCategoryFilter);
        }
    });
}
