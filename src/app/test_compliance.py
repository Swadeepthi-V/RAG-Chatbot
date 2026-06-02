import time
import unittest
from compliance_gate import (
    IngressComplianceGate, 
    PII_REFUSAL_MESSAGE, 
    ADVISORY_REFUSAL_MESSAGE, 
    PERFORMANCE_BYPASS_MESSAGE
)

class TestComplianceGate(unittest.TestCase):
    def setUp(self):
        # We share/pass None to trigger the lazy loading of BGE model during testing
        self.gate = IngressComplianceGate()

    def test_pii_pan_regex(self):
        """Verify that standard, spaced, and digit-obfuscated PAN details are blocked."""
        # Standard PAN
        self.assertEqual(self.gate.check_pii("My PAN is ABCDE1234F"), PII_REFUSAL_MESSAGE)
        # Spaced PAN
        self.assertEqual(self.gate.check_pii("PAN is A B C D E 1 2 3 4 F"), PII_REFUSAL_MESSAGE)
        # Obfuscated text digits PAN
        self.assertEqual(self.gate.check_pii("PAN is A B C D E one two three four F"), PII_REFUSAL_MESSAGE)
        # Safe text (no PAN)
        self.assertIsNone(self.gate.check_pii("Please tell me about HDFC Mid-Cap Fund"))

    def test_pii_aadhaar_card_regex(self):
        """Verify Aadhaar identity cards and credit cards are blocked."""
        # Aadhaar formats
        self.assertEqual(self.gate.check_pii("My Aadhaar is 1234-5678-9012"), PII_REFUSAL_MESSAGE)
        self.assertEqual(self.gate.check_pii("Aadhaar 1234 5678 9012"), PII_REFUSAL_MESSAGE)
        self.assertEqual(self.gate.check_pii("123456789012"), PII_REFUSAL_MESSAGE)
        
        # Credit Card format
        self.assertEqual(self.gate.check_pii("Card number: 4111 2222 3333 4444"), PII_REFUSAL_MESSAGE)
        self.assertEqual(self.gate.check_pii("Card: 4111-2222-3333-4444"), PII_REFUSAL_MESSAGE)

    def test_pii_contacts_regex(self):
        """Verify emails and phone contacts are blocked."""
        # Emails
        self.assertEqual(self.gate.check_pii("Email is relations@hdfcfund.com"), PII_REFUSAL_MESSAGE)
        # Mobile contacts
        self.assertEqual(self.gate.check_pii("Mobile: +919876543210"), PII_REFUSAL_MESSAGE)
        self.assertEqual(self.gate.check_pii("Call 9876543210"), PII_REFUSAL_MESSAGE)

    def test_advisory_keyword_shortcircuit_latency(self):
        """Verify that standard advisory requests are blocked instantly under 100ms."""
        query = "Should I buy HDFC Large Cap?"
        
        start_time = time.perf_counter()
        route_result = self.gate.route_query(query)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        self.assertIsNotNone(route_result)
        self.assertEqual(route_result["status"], "blocked")
        self.assertEqual(route_result["category"], "advisory")
        self.assertEqual(route_result["response"], ADVISORY_REFUSAL_MESSAGE)
        
        # Ingress routing MUST happen under 100ms
        logger_info = f"Advisory routing latency: {duration_ms:.2f}ms"
        print(logger_info)
        self.assertTrue(duration_ms < 100.0, f"Advisory routing took too long: {duration_ms:.2f}ms")

    def test_performance_factsheet_bypass(self):
        """Verify performance/comparison requests are redirected to factsheet bypass links."""
        # Compare vs performance keywords
        self.assertEqual(
            self.gate.route_query("Which fund returns are better HDFC Mid Cap or HDFC Small Cap?")["response"],
            PERFORMANCE_BYPASS_MESSAGE
        )
        self.assertEqual(
            self.gate.route_query("HDFC Mid-Cap performance history")["response"],
            PERFORMANCE_BYPASS_MESSAGE
        )

    def test_semantic_classification_routing(self):
        """Verify semantic zero-shot query router correctly classifies intent using BGE Small."""
        # Prototypical advisory query with no keywords
        category, confidence = self.gate.classify_query("Is HDFC Large Cap a good choice for wealth accumulation?")
        self.assertEqual(category, "advisory")
        
        # Factual query
        category, confidence = self.gate.classify_query("What is the name of the HDFC Mid Cap fund manager?")
        self.assertEqual(category, "factual")

if __name__ == "__main__":
    unittest.main()
