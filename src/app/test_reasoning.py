"""Unit and Integration Tests for Phase 4 Reasoning & Egress validation."""

import os
import unittest
from unittest.mock import patch, MagicMock
import requests

from reasoning import LLMReasoningEngine, split_sentences

class TestReasoningAndEgress(unittest.TestCase):
    
    def setUp(self):
        # Set up a test instance of LLMReasoningEngine
        self.engine = LLMReasoningEngine()
        
        # Define some sample test search results
        self.sample_results = [
            {
                "id": "chunk_1",
                "text": "HDFC Small Cap Fund has an exit load of 1.0% if redeemed within 1 year. No exit load is charged after 1 year. The fund's objective is to provide long-term capital appreciation.",
                "confidence": 0.85,
                "metadata": {
                    "source_url": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct"
                }
            },
            {
                "id": "chunk_2",
                "text": "The minimum SIP investment amount is Rs. 100 per month. The fund manager is Mr. Chirag Setalvad.",
                "confidence": 0.75,
                "metadata": {
                    "source_url": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct"
                }
            }
        ]

    def test_split_sentences_basic(self):
        """Test basic sentence splitting."""
        text = "Hello world! This is sentence two. Is this sentence three?"
        s = split_sentences(text)
        self.assertEqual(len(s), 3)
        self.assertEqual(s[0], "Hello world!")
        self.assertEqual(s[1], "This is sentence two.")
        self.assertEqual(s[2], "Is this sentence three?")

    def test_split_sentences_abbreviations(self):
        """Test sentence splitting handles common financial abbreviations and initials."""
        text = "HDFC Mutual Fund Co. has an AUM of Rs. 10 Lakh. Exit load is 1% p.a. if redeemed in 1 year. The fund manager is Mr. Chirag Setalvad."
        s = split_sentences(text)
        self.assertEqual(len(s), 3)
        self.assertIn("HDFC Mutual Fund Co. has an AUM of Rs. 10 Lakh.", s)
        self.assertIn("Exit load is 1% p.a. if redeemed in 1 year.", s)
        self.assertIn("The fund manager is Mr. Chirag Setalvad.", s)

    def test_split_sentences_decimals(self):
        """Test sentence splitting handles decimal numbers and formatted values."""
        text = "The returns were 12.5% for the last year. Minimum investment is Rs. 10,000.50 starting today."
        s = split_sentences(text)
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0], "The returns were 12.5% for the last year.")
        self.assertEqual(s[1], "Minimum investment is Rs. 10,000.50 starting today.")

    def test_citation_validator_valid(self):
        """Test citation validator leaves text intact if exactly one correct citation exists."""
        url = "https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct"
        text = f"HDFC Small Cap Fund exit load is 1.0%. [Source Link]({url})"
        result = self.engine.validate_and_fix_citation(text, url)
        self.assertEqual(result, text)

    def test_citation_validator_missing(self):
        """Test citation validator appends citation if missing."""
        url = "https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct"
        text = "HDFC Small Cap Fund exit load is 1.0%."
        result = self.engine.validate_and_fix_citation(text, url)
        self.assertEqual(result, f"HDFC Small Cap Fund exit load is 1.0%. [Source]({url})")

    def test_citation_validator_multiple(self):
        """Test citation validator cleans up multiple or incorrect markdown links."""
        url = "https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct"
        wrong_url = "https://www.google.com"
        text = f"Read about [HDFC Fund]({url}) and check [Google]({wrong_url})."
        result = self.engine.validate_and_fix_citation(text, url)
        self.assertEqual(result, f"Read about HDFC Fund and check Google. [Source]({url})")

    def test_fallback_response(self):
        """Test fallback response formats the top chunk content correctly."""
        top_chunk = self.sample_results[0]
        # Make the top chunk text long to test truncation
        top_chunk["text"] = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        url = top_chunk["metadata"]["source_url"]
        
        fallback = self.engine._fallback_response("dummy query", top_chunk)
        # Should be first 3 sentences, plus the citation link
        expected_text = f"Sentence one. Sentence two. Sentence three. [Source]({url})"
        self.assertEqual(fallback, expected_text)

    @patch('requests.post')
    def test_generate_answer_success(self, mock_post):
        """Test successful response from Groq API."""
        # Configure mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_ok = True
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "The exit load for HDFC Small Cap Fund is 1% if redeemed within a year. There is no exit load after 1 year. The manager is Chirag Setalvad."
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Temporarily set API key to test API path
        self.engine.api_key = "gsk_test_key"
        
        response = self.engine.generate_answer("what is exit load?", self.sample_results)
        
        # Verify call parameters
        mock_post.assert_called_once()
        self.assertIn("The exit load for HDFC Small Cap Fund is 1%", response)
        self.assertIn("[Source](https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct)", response)
        self.assertIn("Last updated from sources:", response)

    @patch('requests.post')
    def test_generate_answer_api_error(self, mock_post):
        """Test API returning 500 error triggers fallback."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        self.engine.api_key = "gsk_test_key"
        response = self.engine.generate_answer("what is exit load?", self.sample_results)
        
        # Verify fallback was used (contains text from chunk_1 first 3 sentences)
        self.assertIn("HDFC Small Cap Fund has an exit load of 1.0%", response)
        self.assertIn("[Source](https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct)", response)
        self.assertIn("Last updated from sources:", response)

    @patch('requests.post')
    def test_generate_answer_timeout(self, mock_post):
        """Test API timeout triggers fallback."""
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")
        
        self.engine.api_key = "gsk_test_key"
        response = self.engine.generate_answer("what is exit load?", self.sample_results)
        
        # Verify fallback was used
        self.assertIn("HDFC Small Cap Fund has an exit load of 1.0%", response)
        self.assertIn("[Source](https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct)", response)

    def test_generate_answer_missing_api_key(self):
        """Test missing API key triggers fallback directly without network call."""
        self.engine.api_key = ""
        
        with patch('requests.post') as mock_post:
            response = self.engine.generate_answer("what is exit load?", self.sample_results)
            # Verify no network call was made
            mock_post.assert_not_called()
            
        # Verify fallback was used
        self.assertIn("HDFC Small Cap Fund has an exit load of 1.0%", response)
        self.assertIn("[Source](https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct)", response)


if __name__ == "__main__":
    unittest.main()
