import requests
import sys
import json
from datetime import datetime
import socketio
import asyncio
import time

class CricketAuctionTester:
    def __init__(self, base_url="https://374567c9-e5e1-416d-83be-3819d87c4319.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.room_code = None
        self.socket_client = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=10):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error Response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error Response: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout after {timeout} seconds")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test the health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "",
            200
        )
        return success

    def test_create_room(self):
        """Test room creation"""
        success, response = self.run_test(
            "Create Room",
            "POST",
            "room/create",
            200
        )
        if success and 'room_code' in response:
            self.room_code = response['room_code']
            print(f"   Created room with code: {self.room_code}")
            # Validate room code is 6 digits
            if len(self.room_code) == 6 and self.room_code.isdigit():
                print("✅ Room code format is correct (6 digits)")
            else:
                print(f"❌ Room code format is incorrect: {self.room_code}")
                return False
        return success

    def test_get_room(self):
        """Test room retrieval"""
        if not self.room_code:
            print("❌ No room code available for testing")
            return False
            
        success, response = self.run_test(
            "Get Room",
            "GET",
            f"room/{self.room_code}",
            200
        )
        if success:
            # Validate room structure
            required_fields = ['id', 'code', 'host_id', 'teams', 'auction_state', 'players_pool']
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"❌ Missing required fields in room response: {missing_fields}")
                return False
            print("✅ Room structure is valid")
        return success

    def test_get_players(self):
        """Test players endpoint"""
        success, response = self.run_test(
            "Get Players",
            "GET",
            "players",
            200
        )
        if success:
            if isinstance(response, list):
                player_count = len(response)
                print(f"   Found {player_count} players")
                if player_count == 200:
                    print("✅ Correct number of players (200)")
                else:
                    print(f"❌ Expected 200 players, found {player_count}")
                    return False
                
                # Check if famous players exist
                player_names = [player.get('name', '') for player in response]
                famous_players = ['Virat Kohli', 'Rohit Sharma', 'KL Rahul', 'Hardik Pandya']
                found_famous = [name for name in famous_players if name in player_names]
                print(f"   Found famous players: {found_famous}")
                
                # Validate player structure
                if response:
                    sample_player = response[0]
                    required_fields = ['id', 'name', 'role', 'base_price', 'country', 'rating']
                    missing_fields = [field for field in required_fields if field not in sample_player]
                    if missing_fields:
                        print(f"❌ Missing required fields in player: {missing_fields}")
                        return False
                    print("✅ Player structure is valid")
            else:
                print("❌ Players response is not a list")
                return False
        return success

    def test_start_auction(self):
        """Test auction start"""
        if not self.room_code:
            print("❌ No room code available for testing")
            return False
            
        success, response = self.run_test(
            "Start Auction",
            "POST",
            f"room/{self.room_code}/start",
            200
        )
        if success and 'message' in response:
            print(f"   Auction start message: {response['message']}")
        return success

    def test_invalid_room(self):
        """Test invalid room code"""
        success, response = self.run_test(
            "Invalid Room Code",
            "GET",
            "room/999999",
            200  # API returns 200 with error message
        )
        if success and 'error' in response:
            print("✅ Correctly handles invalid room code")
        return success

    def test_socket_connection(self):
        """Test Socket.io connection"""
        print(f"\n🔍 Testing Socket.io Connection...")
        try:
            # Create a synchronous socket client with polling transport only
            sio = socketio.SimpleClient()
            
            # Connect to the server
            print(f"   Connecting to: {self.base_url}")
            sio.connect(self.base_url, transports=['polling'])
            print("✅ Socket.io connection successful")
            
            # Test join_room event
            if self.room_code:
                print(f"   Testing join_room event with room code: {self.room_code}")
                sio.emit('join_room', {
                    'room_code': self.room_code,
                    'team_name': 'Test Team'
                })
                
                # Wait for response
                time.sleep(2)
                print("✅ join_room event sent successfully")
            
            sio.disconnect()
            self.tests_run += 1
            self.tests_passed += 1
            return True
            
        except Exception as e:
            print(f"❌ Socket.io connection failed: {str(e)}")
            self.tests_run += 1
            return False

def main():
    print("🏏 Cricket Auction Backend Testing")
    print("=" * 50)
    
    # Setup
    tester = CricketAuctionTester()
    
    # Run API tests
    print("\n📡 API ENDPOINT TESTS")
    print("-" * 30)
    
    # Test health check (if exists)
    tester.test_health_check()
    
    # Test room creation
    if not tester.test_create_room():
        print("❌ Room creation failed, stopping dependent tests")
        return 1
    
    # Test room retrieval
    tester.test_get_room()
    
    # Test players endpoint
    tester.test_get_players()
    
    # Test auction start
    tester.test_start_auction()
    
    # Test invalid room
    tester.test_invalid_room()
    
    # Test Socket.io connection
    print("\n🔌 SOCKET.IO TESTS")
    print("-" * 30)
    tester.test_socket_connection()
    
    # Print results
    print(f"\n📊 FINAL RESULTS")
    print("=" * 50)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())