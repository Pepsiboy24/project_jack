import sys
import unittest
import math
from pydantic import ValidationError

# Add current workspace to path to import main
sys.path.insert(0, ".")
import main
from main import ExplainRequest, _build_nlg

class TestNLG(unittest.TestCase):
    def setUp(self):
        # Default mock inputs
        self.default_req = ExplainRequest(
            name="Wireless Headphones",
            rating=4.5,
            price=99.99,
            category="Electronics",
            about_product="High-quality sound with active noise cancellation."
        )
        self.default_user_name = "Alice"
        self.default_has_history = True
        self.default_shap_feat = {"Price": 0.12, "Rating": 0.25, "Category": 0.08}
        self.default_lime_feat = {"Price": 0.10, "Rating": 0.22, "Category": 0.07}
        self.default_confidence = 0.88
        self.default_mode = "ml"

    def run_nlg(self, req=None, user_name=None, has_history=None, 
                shap_feat=None, lime_feat=None, confidence=None, mode=None):
        """Helper to run _build_nlg with fallbacks to defaults."""
        r = req if req is not None else self.default_req
        un = user_name if user_name is not None else self.default_user_name
        hh = has_history if has_history is not None else self.default_has_history
        sf = shap_feat if shap_feat is not None else self.default_shap_feat
        lf = lime_feat if lime_feat is not None else self.default_lime_feat
        conf = confidence if confidence is not None else self.default_confidence
        m = mode if mode is not None else self.default_mode
        return _build_nlg(r, un, hh, sf, lf, conf, m)

    def test_normal_case(self):
        """Verify normal execution works without errors."""
        res = self.run_nlg()
        self.assertTrue(isinstance(res, str))
        self.assertTrue(len(res) > 0)
        print("\n--- Normal Output ---")
        print(res)

    def test_extreme_prices(self):
        """Test with different price extremes."""
        price_cases = [0.0, -5.99, 1000000.0, float('inf'), float('nan')]
        for p in price_cases:
            with self.subTest(price=p):
                req = ExplainRequest(
                    name="Test Product",
                    rating=4.5,
                    price=p,
                    category="Electronics"
                )
                try:
                    res = self.run_nlg(req=req)
                    self.assertTrue(isinstance(res, str))
                    self.assertFalse(res.strip() == "")
                    
                    # Check for weird outputs in the generated text
                    if math.isnan(p):
                        self.assertNotIn("$nan", res)
                    if math.isinf(p):
                        self.assertNotIn("$inf", res)
                    if p < 0:
                        self.assertNotIn("$-", res)  # Negative prices shouldn't format as $-5.99
                except Exception as e:
                    self.fail(f"Crashed with price {p}: {e}")

    def test_ratings(self):
        """Test with different ratings."""
        ratings_cases = [0.0, -1.5, 5.0, 10.0, float('nan'), float('inf')]
        for r in ratings_cases:
            with self.subTest(rating=r):
                req = ExplainRequest(
                    name="Test Product",
                    rating=r,
                    price=49.99,
                    category="Electronics"
                )
                try:
                    res = self.run_nlg(req=req)
                    self.assertTrue(isinstance(res, str))
                    self.assertFalse(res.strip() == "")
                except Exception as e:
                    self.fail(f"Crashed with rating {r}: {e}")

    def test_categories(self):
        """Test with various category types."""
        categories = ["", None, "A" * 1000, "<script>alert(1)</script>"]
        for cat in categories:
            with self.subTest(category=cat):
                # category is required and must be str in ExplainRequest,
                # but we try to mock it if possible or bypass.
                # Let's bypass pydantic validation by constructing target dictionary
                # or creating ExplainRequest manually.
                try:
                    req = ExplainRequest.model_construct(
                        name="Test Product",
                        rating=4.5,
                        price=49.99,
                        category=cat
                    )
                    res = self.run_nlg(req=req)
                    self.assertTrue(isinstance(res, str))
                    self.assertFalse(res.strip() == "")
                    if cat is None:
                        self.assertNotIn("None", res)
                    if cat == "":
                        self.assertNotIn("<strong></strong>", res)
                except Exception as e:
                    self.fail(f"Crashed with category {cat}: {e}")

    def test_empty_or_rating_only_features(self):
        """Test when feature attributions are empty or contain only Rating."""
        feature_cases = [
            ({}, {}),
            ({"Rating": 0.5}, {"Rating": 0.4}),
            ({"Price": 0.1}, {}),  # mismatch/missing keys
            ({"Price": 0.1, "Rating": 0.2}, {"Rating": 0.3})
        ]
        for sf, lf in feature_cases:
            with self.subTest(shap_feat=sf, lime_feat=lf):
                try:
                    res = self.run_nlg(shap_feat=sf, lime_feat=lf)
                    self.assertTrue(isinstance(res, str))
                    self.assertFalse(res.strip() == "")
                except Exception as e:
                    print(f"EXPECTED FAILURE / CRASH on features (shap: {sf}, lime: {lf}): {e}")
                    # We will fail this test if the function crashes, identifying it as a bug.
                    self.fail(f"Crashed with features: {e}")

    def test_single_driver_repetition(self):
        """Verify that when only one feature is present, it does not repeat itself in NLG."""
        # If drivers contains only 'Price' (e.g. category has 0 impact)
        sf = {"Price": 0.5, "Rating": 0.1}
        lf = {"Price": 0.4, "Rating": 0.1}
        res = self.run_nlg(shap_feat=sf, lime_feat=lf)
        
        # Check if the phrase for price is repeated
        # e.g. "... aligns with friendly(Price) and friendly(Price)"
        # Let's check how many times the price description is in the response.
        # "its price of" or "its outstanding value" or "its premium quality"
        occurrences = res.count("price of") + res.count("outstanding value") + res.count("premium quality")
        self.assertLess(occurrences, 2, f"Repetitive phrasing found in: {res}")

    def test_confidence_extremes(self):
        """Test with extreme confidence scores."""
        conf_cases = [None, 0.0, 1.0, -0.5, 1.5, float('nan')]
        for c in conf_cases:
            with self.subTest(confidence=c):
                try:
                    res = self.run_nlg(confidence=c)
                    self.assertTrue(isinstance(res, str))
                    self.assertFalse(res.strip() == "")
                except Exception as e:
                    self.fail(f"Crashed with confidence {c}: {e}")

    def test_usernames(self):
        """Test with different user name styles."""
        names = ["", None, "A" * 1000, "<b>Bob</b>"]
        for name in names:
            with self.subTest(name=name):
                try:
                    res = self.run_nlg(user_name=name)
                    self.assertTrue(isinstance(res, str))
                    self.assertFalse(res.strip() == "")
                    if name is None:
                        self.assertNotIn("None", res)
                except Exception as e:
                    self.fail(f"Crashed with username {name}: {e}")

if __name__ == "__main__":
    unittest.main()
