#!/usr/bin/env python3
"""
Backend API Testing for Ollama Chat Interface
Tests all API endpoints with proper error handling for Ollama offline scenarios
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class OllamaChatAPITester:
    def __init__(self, base_url="https://4fc1ddd7-917a-4f61-80ab-fd7c78211898.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "status": "PASS" if success else "FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {name}: {details}")

    def test_basic_health(self):
        """Test basic API health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Response: {data}"
            self.log_test("Basic API Health", success, details)
            return success
        except Exception as e:
            self.log_test("Basic API Health", False, f"Error: {str(e)}")
            return False

    def test_ollama_health(self):
        """Test Ollama health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/ollama/health", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Ollama Status: {data.get('status', 'unknown')}"
                if data.get('status') == 'offline':
                    details += " (Expected - Ollama not running)"
            self.log_test("Ollama Health Check", success, details)
            return success, response.json() if success else {}
        except Exception as e:
            self.log_test("Ollama Health Check", False, f"Error: {str(e)}")
            return False, {}

    def test_ollama_models(self):
        """Test Ollama models endpoint"""
        try:
            response = requests.get(f"{self.api_url}/ollama/models", timeout=10)
            # This should return 503 when Ollama is offline
            expected_status = 503  # Service Unavailable when Ollama is offline
            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            if response.status_code == expected_status:
                details += " (Expected - Ollama offline)"
            elif response.status_code == 200:
                data = response.json()
                details += f", Models available: {len(data.get('models', []))}"
            self.log_test("Ollama Models Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Ollama Models Endpoint", False, f"Error: {str(e)}")
            return False

    def test_ollama_chat(self):
        """Test Ollama chat endpoint (should fail gracefully when offline)"""
        try:
            payload = {
                "message": "Hello, this is a test message",
                "model": "llama3.2:latest",
                "stream": False
            }
            response = requests.post(f"{self.api_url}/ollama/chat", json=payload, timeout=30)
            # Should return 503 when Ollama is offline
            expected_status = 503
            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            if response.status_code == expected_status:
                details += " (Expected - Ollama offline)"
            elif response.status_code == 200:
                details += " (Unexpected - Ollama seems to be running)"
            self.log_test("Ollama Chat Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Ollama Chat Endpoint", False, f"Error: {str(e)}")
            return False

    def test_ollama_chat_stream(self):
        """Test Ollama streaming chat endpoint"""
        try:
            payload = {
                "message": "Hello, this is a test streaming message",
                "model": "llama3.2:latest",
                "stream": True
            }
            response = requests.post(f"{self.api_url}/ollama/chat/stream", json=payload, timeout=30)
            # Should return 200 but stream error messages when Ollama is offline
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                # Check if it's a streaming response
                content_type = response.headers.get('content-type', '')
                if 'text/event-stream' in content_type:
                    details += ", Streaming response received"
                    # Try to read first chunk to see if it contains error
                    try:
                        first_chunk = next(response.iter_lines(decode_unicode=True))
                        if 'error' in first_chunk.lower():
                            details += " (Contains error as expected)"
                    except:
                        pass
            self.log_test("Ollama Streaming Chat", success, details)
            return success
        except Exception as e:
            self.log_test("Ollama Streaming Chat", False, f"Error: {str(e)}")
            return False

    def test_chat_history(self):
        """Test chat history endpoint"""
        try:
            response = requests.get(f"{self.api_url}/chat/history", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", History entries: {len(data)}"
            self.log_test("Chat History Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Chat History Endpoint", False, f"Error: {str(e)}")
            return False

    def test_status_endpoints(self):
        """Test status check endpoints"""
        try:
            # Test POST /api/status
            payload = {"client_name": f"test_client_{datetime.now().strftime('%H%M%S')}"}
            response = requests.post(f"{self.api_url}/status", json=payload, timeout=10)
            post_success = response.status_code == 200
            details = f"POST Status: {response.status_code}"
            
            if post_success:
                # Test GET /api/status
                response = requests.get(f"{self.api_url}/status", timeout=10)
                get_success = response.status_code == 200
                details += f", GET Status: {response.status_code}"
                if get_success:
                    data = response.json()
                    details += f", Status entries: {len(data)}"
                
                success = post_success and get_success
            else:
                success = False
            
            self.log_test("Status Check Endpoints", success, details)
            return success
        except Exception as e:
            self.log_test("Status Check Endpoints", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Backend API Tests for Ollama Chat Interface")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_basic_health():
            print("❌ Basic API connectivity failed. Stopping tests.")
            return False
        
        # Test Ollama-specific endpoints
        ollama_healthy, health_data = self.test_ollama_health()
        
        # Test models endpoint (should fail when Ollama is offline)
        self.test_ollama_models()
        
        # Test chat endpoints (should handle offline gracefully)
        self.test_ollama_chat()
        self.test_ollama_chat_stream()
        
        # Test database-related endpoints
        self.test_chat_history()
        self.test_status_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['test']}: {result['details']}")
        
        # Analyze Ollama status
        if ollama_healthy and health_data:
            ollama_status = health_data.get('status', 'unknown')
            print(f"\n🔍 OLLAMA STATUS: {ollama_status.upper()}")
            if ollama_status == 'offline':
                print("   This is expected behavior for testing without Ollama running.")
                print("   The application should handle this gracefully in the UI.")
            elif ollama_status == 'healthy':
                print("   Ollama is running and healthy.")
                print(f"   Available models: {health_data.get('models_available', 0)}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = OllamaChatAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All backend API tests passed!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())