
import requests
import sys
import json
from datetime import datetime

class ForexSignalAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.signals_created = []

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                    return False, response.json()
                except:
                    return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test the health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        if success:
            print(f"Health check response: {response}")
            if response.get("gemini_configured"):
                print("✅ Gemini API is configured")
            else:
                print("⚠️ Gemini API is not configured")
        return success

    def test_extract_signal(self, message, group_name="Test Group"):
        """Test signal extraction"""
        success, response = self.run_test(
            "Extract Signal",
            "POST",
            "api/extract-signal",
            200,
            data={"message": message, "group_name": group_name}
        )
        if success and response.get("success"):
            print(f"✅ Signal extracted successfully: {response.get('signal')}")
            if response.get("signal") and "id" in response.get("signal"):
                self.signals_created.append(response["signal"]["id"])
            return True, response.get("signal")
        else:
            print(f"❌ Signal extraction failed or no valid signal found")
            return False, None

    def test_get_signals(self):
        """Test getting all signals"""
        success, response = self.run_test(
            "Get All Signals",
            "GET",
            "api/signals",
            200
        )
        if success:
            signals = response.get("signals", [])
            print(f"✅ Retrieved {len(signals)} signals")
            return True, signals
        return False, []

    def test_get_analytics(self):
        """Test getting analytics"""
        success, response = self.run_test(
            "Get Analytics",
            "GET",
            "api/analytics",
            200
        )
        if success:
            print(f"✅ Analytics retrieved successfully")
            # Check for new analytics fields
            if "avg_quality_score" in response:
                print(f"✅ Quality Score analytics present: {response.get('avg_quality_score')}")
            else:
                print("❌ Quality Score analytics missing")
                
            if "sentiment_breakdown" in response:
                print(f"✅ Sentiment breakdown present: {response.get('sentiment_breakdown')}")
            else:
                print("❌ Sentiment breakdown missing")
                
            if "performance_metrics" in response and "avg_risk_reward" in response.get("performance_metrics", {}):
                print(f"✅ Risk/Reward metrics present: {response.get('performance_metrics').get('avg_risk_reward')}")
            else:
                print("❌ Risk/Reward metrics missing")
                
            return True, response
        return False, {}

    def test_delete_signal(self, signal_id):
        """Test deleting a specific signal"""
        success, response = self.run_test(
            f"Delete Signal {signal_id}",
            "DELETE",
            f"api/signals/{signal_id}",
            200
        )
        if success:
            print(f"✅ Signal {signal_id} deleted successfully")
            if signal_id in self.signals_created:
                self.signals_created.remove(signal_id)
            return True
        return False

    def test_clear_all_signals(self):
        """Test clearing all signals"""
        success, response = self.run_test(
            "Clear All Signals",
            "DELETE",
            "api/signals",
            200
        )
        if success:
            print(f"✅ All signals cleared successfully")
            self.signals_created = []
            return True
        return False

    def test_export_csv(self):
        """Test exporting signals to CSV"""
        print(f"\n🔍 Testing Export to CSV...")
        url = f"{self.base_url}/api/export/csv"
        
        try:
            response = requests.get(url)
            success = response.status_code == 200
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"✅ Content-Type: {response.headers.get('Content-Type')}")
                print(f"✅ Content-Disposition: {response.headers.get('Content-Disposition')}")
                
                # Check if we got CSV content
                if response.headers.get('Content-Type') == 'text/csv' and 'forex_signals.csv' in response.headers.get('Content-Disposition', ''):
                    print(f"✅ CSV export successful - Content length: {len(response.content)} bytes")
                    # Print first few lines of CSV
                    content_preview = response.content.decode('utf-8').split('\n')[:3]
                    print(f"CSV Preview: {content_preview}")
                    return True
                else:
                    print("❌ Response doesn't appear to be a valid CSV file")
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                print(f"Response: {response.text}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False
            
    def test_export_json(self):
        """Test exporting signals to JSON"""
        print(f"\n🔍 Testing Export to JSON...")
        url = f"{self.base_url}/api/export/json"
        
        try:
            response = requests.get(url)
            success = response.status_code == 200
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"✅ Content-Type: {response.headers.get('Content-Type')}")
                print(f"✅ Content-Disposition: {response.headers.get('Content-Disposition')}")
                
                # Check if we got JSON content
                if response.headers.get('Content-Type') == 'application/json' and 'forex_signals.json' in response.headers.get('Content-Disposition', ''):
                    try:
                        json_data = response.json()
                        print(f"✅ JSON export successful - {len(json_data.get('signals', []))} signals exported")
                        print(f"✅ JSON contains metadata: export_timestamp={json_data.get('export_timestamp')}, total_signals={json_data.get('total_signals')}")
                        return True
                    except json.JSONDecodeError:
                        print("❌ Response is not valid JSON")
                else:
                    print("❌ Response doesn't appear to be a valid JSON file")
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                print(f"Response: {response.text}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

def main():
    # Get backend URL from frontend .env
    backend_url = "https://fd0b28aa-ed2e-4fe8-a658-44d405b0fdef.preview.emergentagent.com"
    
    print(f"🔌 Testing API at: {backend_url}")
    
    # Setup tester
    tester = ForexSignalAPITester(backend_url)
    
    # Test health check
    if not tester.test_health_check():
        print("❌ Health check failed, stopping tests")
        return 1
    
    # Test signal extraction with sample messages
    sample_messages = [
        "🔔 EURUSD BUY 1.0945 TP1=1.0980 TP2=1.1000 TP3=1.1020 SL=1.0920",
        "📈 GBPJPY SELL ZONE 185.50-186.00 TP1: 184.80 TP2: 184.20 TP3: 183.50 SL: 186.80",
        "⚡ XAUUSD BUY NOW @ 2025.50 🎯 TP1: 2030.00 🎯 TP2: 2035.00 🎯 TP3: 2040.00 ❌ SL: 2020.00",
        "🔥 USDJPY SELL 148.25 Take Profit 1: 147.80 Take Profit 2: 147.30 Take Profit 3: 146.80 Stop Loss: 149.00"
    ]
    
    # Test with each sample message
    for i, message in enumerate(sample_messages):
        group_name = f"Test Group {i+1}"
        success, signal = tester.test_extract_signal(message, group_name)
        if success:
            print(f"✅ Sample {i+1} extraction successful")
            # Check for new fields in the signal
            if signal:
                if "quality_score" in signal and signal["quality_score"] is not None:
                    print(f"✅ Quality Score present: {signal['quality_score']}")
                else:
                    print("❌ Quality Score missing")
                    
                if "sentiment" in signal and signal["sentiment"] is not None:
                    print(f"✅ Sentiment present: {signal['sentiment']}")
                else:
                    print("❌ Sentiment missing")
                    
                if "risk_reward_ratio" in signal and signal["risk_reward_ratio"] is not None:
                    print(f"✅ Risk/Reward Ratio present: {signal['risk_reward_ratio']}")
                else:
                    print("❌ Risk/Reward Ratio missing")
        else:
            print(f"❌ Sample {i+1} extraction failed")
    
    # Test getting all signals
    tester.test_get_signals()
    
    # Test analytics
    tester.test_get_analytics()
    
    # Test export endpoints
    tester.test_export_csv()
    tester.test_export_json()
    
    # Test deleting a signal if we have any
    if tester.signals_created:
        tester.test_delete_signal(tester.signals_created[0])
    
    # Test getting signals after deletion
    tester.test_get_signals()
    
    # Test analytics after deletion
    tester.test_get_analytics()
    
    # Test error handling with invalid message
    tester.test_extract_signal("This is not a forex signal", "Invalid Group")
    
    # Clean up
    tester.cleanup()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
