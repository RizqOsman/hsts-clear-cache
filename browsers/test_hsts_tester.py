#!/usr/bin/env python3
"""
Tests for HSTS Bypass Testing Tool
"""

import unittest
import os
import sys
import json
import tempfile
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hsts_tester import HSTSTester

class TestHSTSTester(unittest.TestCase):
    """Test cases for the HSTSTester class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_domain = "example.com"
        self.tester = HSTSTester(self.test_domain)
    
    def test_initialization(self):
        """Test that the tester initializes correctly"""
        self.assertEqual(self.tester.target_domain, self.test_domain)
        
    @patch('requests.get')
    def test_check_hsts_status_enabled(self, mock_get):
        """Test HSTS status checking with HSTS enabled"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.headers = {'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload'}
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.tester.check_hsts_status()
        
        # Verify results
        self.assertTrue(result['enabled'])
        self.assertEqual(result['max_age'], 31536000)
        self.assertTrue(result['include_subdomains'])
        self.assertTrue(result['preload'])
        
    @patch('requests.get')
    def test_check_hsts_status_disabled(self, mock_get):
        """Test HSTS status checking with HSTS disabled"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.tester.check_hsts_status()
        
        # Verify results
        self.assertFalse(result['enabled'])
        
    def test_domain_validation(self):
        """Test domain validation logic"""
        # Valid domains
        self.assertTrue(self.tester.set_target_domain("example.org"))
        self.assertTrue(self.tester.set_target_domain("sub.example.org"))
        self.assertTrue(self.tester.set_target_domain("https://example.org"))
        
        # Invalid domains should still parse in this implementation
        # This is just validating the parsing works
        self.assertTrue(self.tester.set_target_domain("example"))
    
    def test_parse_max_age(self):
        """Test parsing max-age from HSTS header"""
        # Valid max-age
        header = "max-age=31536000; includeSubDomains"
        self.assertEqual(self.tester._parse_max_age(header), 31536000)
        
        # No max-age
        header = "includeSubDomains; preload"
        self.assertIsNone(self.tester._parse_max_age(header))
        
    @patch('os.path.exists')
    def test_get_browser_data_path(self, mock_exists):
        """Test getting browser data paths"""
        # Make os.path.exists always return True for this test
        mock_exists.return_value = True
        
        # Test for a known browser
        path = self.tester.get_browser_data_path("chrome")
        self.assertIsNotNone(path)
        
    def test_save_results(self):
        """Test saving results to a file"""
        # Add some test data
        self.tester.results = {
            "test_data": "Some test results",
            "browser_test": {"chrome": {"success": True}}
        }
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            filename = tmp.name
        
        try:
            saved_file = self.tester.save_results(filename)
            self.assertEqual(saved_file, filename)
            
            # Verify file contents
            with open(filename, 'r') as f:
                data = json.load(f)
                self.assertEqual(data, self.tester.results)
        finally:
            # Clean up
            if os.path.exists(filename):
                os.remove(filename)

if __name__ == '__main__':
    unittest.main()
