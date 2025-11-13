#!/usr/bin/env python3
"""
Load Testing Script for Digital Signage API
Tests concurrent users and monitors performance
"""

import asyncio
import aiohttp
import time
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any
import statistics

# Configuration
BASE_URL = "http://192.168.5.12:8001"
API_PREFIX = "/api/v1"

# Test user credentials
TEST_USERS = [
    {"username": "admin", "password": "admin123"},
    # Add more test users as needed
]

# Test scenarios
class LoadTestScenarios:
    """Different load test scenarios"""
    
    @staticmethod
    async def login_scenario(session: aiohttp.ClientSession, user_data: dict) -> dict:
        """Test login endpoint"""
        start = time.time()
        
        async with session.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json=user_data
        ) as resp:
            data = await resp.json()
            duration = time.time() - start
            
            return {
                "endpoint": "/auth/login",
                "status": resp.status,
                "duration": duration,
                "success": resp.status == 200,
                "token": data.get("access_token") if resp.status == 200 else None
            }
    
    @staticmethod
    async def list_devices_scenario(session: aiohttp.ClientSession, token: str) -> dict:
        """Test list devices endpoint"""
        start = time.time()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with session.get(
            f"{BASE_URL}{API_PREFIX}/devices",
            headers=headers
        ) as resp:
            data = await resp.json()
            duration = time.time() - start
            
            return {
                "endpoint": "/devices",
                "status": resp.status,
                "duration": duration,
                "success": resp.status == 200,
                "count": data.get("total", 0) if resp.status == 200 else 0
            }
    
    @staticmethod
    async def list_content_scenario(session: aiohttp.ClientSession, token: str) -> dict:
        """Test list content endpoint"""
        start = time.time()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with session.get(
            f"{BASE_URL}{API_PREFIX}/contents?limit=20",
            headers=headers
        ) as resp:
            data = await resp.json()
            duration = time.time() - start
            
            return {
                "endpoint": "/contents",
                "status": resp.status,
                "duration": duration,
                "success": resp.status == 200,
                "count": data.get("total", 0) if resp.status == 200 else 0
            }
    
    @staticmethod
    async def list_playlists_scenario(session: aiohttp.ClientSession, token: str) -> dict:
        """Test list playlists endpoint"""
        start = time.time()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with session.get(
            f"{BASE_URL}{API_PREFIX}/playlists?limit=20",
            headers=headers
        ) as resp:
            data = await resp.json()
            duration = time.time() - start
            
            return {
                "endpoint": "/playlists",
                "status": resp.status,
                "duration": duration,
                "success": resp.status == 200,
                "count": data.get("total", 0) if resp.status == 200 else 0
            }
    
    @staticmethod
    async def health_check_scenario(session: aiohttp.ClientSession) -> dict:
        """Test health check endpoint"""
        start = time.time()
        
        async with session.get(f"{BASE_URL}/health") as resp:
            data = await resp.json()
            duration = time.time() - start
            
            return {
                "endpoint": "/health",
                "status": resp.status,
                "duration": duration,
                "success": resp.status == 200,
                "healthy": data.get("status") == "healthy" if resp.status == 200 else False
            }


class UserSimulator:
    """Simulates a single user's behavior"""
    
    def __init__(self, user_id: int, user_data: dict, duration_seconds: int):
        self.user_id = user_id
        self.user_data = user_data
        self.duration_seconds = duration_seconds
        self.results: List[dict] = []
        self.token: str = None
    
    async def run(self, session: aiohttp.ClientSession):
        """Run user simulation"""
        start_time = time.time()
        request_count = 0
        
        # Initial login
        login_result = await LoadTestScenarios.login_scenario(session, self.user_data)
        self.results.append(login_result)
        
        if login_result["success"]:
            self.token = login_result["token"]
            print(f"User {self.user_id} logged in successfully")
        else:
            print(f"User {self.user_id} login failed")
            return
        
        # Main simulation loop
        while time.time() - start_time < self.duration_seconds:
            try:
                # Random scenario selection
                scenario = request_count % 4
                
                if scenario == 0:
                    result = await LoadTestScenarios.list_devices_scenario(session, self.token)
                elif scenario == 1:
                    result = await LoadTestScenarios.list_content_scenario(session, self.token)
                elif scenario == 2:
                    result = await LoadTestScenarios.list_playlists_scenario(session, self.token)
                else:
                    result = await LoadTestScenarios.health_check_scenario(session)
                
                self.results.append(result)
                request_count += 1
                
                # Wait between requests (0.5 to 2 seconds)
                await asyncio.sleep(0.5 + (request_count % 3) * 0.5)
                
            except Exception as e:
                print(f"User {self.user_id} error: {e}")
                self.results.append({
                    "endpoint": "unknown",
                    "status": 0,
                    "duration": 0,
                    "success": False,
                    "error": str(e)
                })
        
        print(f"User {self.user_id} completed {request_count} requests")


class LoadTestRunner:
    """Manages the load test execution"""
    
    def __init__(self, num_users: int, duration_seconds: int):
        self.num_users = num_users
        self.duration_seconds = duration_seconds
        self.results: List[dict] = []
    
    async def run(self):
        """Run the load test"""
        print(f"Starting load test with {self.num_users} users for {self.duration_seconds} seconds")
        print(f"Target: {BASE_URL}")
        print("=" * 60)
        
        # Create users
        users = []
        for i in range(self.num_users):
            # Cycle through test users if we have more virtual users than test accounts
            user_data = TEST_USERS[i % len(TEST_USERS)].copy()
            # Add suffix to username for uniqueness
            if i >= len(TEST_USERS):
                user_data["username"] = f"{user_data['username']}_{i}"
            
            user = UserSimulator(i, user_data, self.duration_seconds)
            users.append(user)
        
        # Run all users concurrently
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=100)
        async with aiohttp.ClientSession(connector=connector) as session:
            await asyncio.gather(*[user.run(session) for user in users])
        
        # Collect all results
        for user in users:
            self.results.extend(user.results)
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate load test report"""
        print("\n" + "=" * 60)
        print("LOAD TEST REPORT")
        print("=" * 60)
        print(f"Test Duration: {self.duration_seconds} seconds")
        print(f"Virtual Users: {self.num_users}")
        print(f"Total Requests: {len(self.results)}")
        
        # Group results by endpoint
        endpoints = {}
        for result in self.results:
            endpoint = result["endpoint"]
            if endpoint not in endpoints:
                endpoints[endpoint] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "durations": [],
                    "status_codes": {}
                }
            
            endpoints[endpoint]["total"] += 1
            if result["success"]:
                endpoints[endpoint]["success"] += 1
            else:
                endpoints[endpoint]["failed"] += 1
            
            endpoints[endpoint]["durations"].append(result["duration"])
            
            status = str(result["status"])
            if status not in endpoints[endpoint]["status_codes"]:
                endpoints[endpoint]["status_codes"][status] = 0
            endpoints[endpoint]["status_codes"][status] += 1
        
        # Print statistics per endpoint
        print("\nEndpoint Statistics:")
        print("-" * 60)
        
        for endpoint, stats in endpoints.items():
            durations = stats["durations"]
            success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            
            print(f"\n{endpoint}:")
            print(f"  Total Requests: {stats['total']}")
            print(f"  Success Rate: {success_rate:.1f}%")
            print(f"  Response Times:")
            if durations:
                print(f"    Min: {min(durations)*1000:.0f}ms")
                print(f"    Max: {max(durations)*1000:.0f}ms")
                print(f"    Avg: {statistics.mean(durations)*1000:.0f}ms")
                print(f"    Median: {statistics.median(durations)*1000:.0f}ms")
                if len(durations) > 1:
                    print(f"    95th percentile: {sorted(durations)[int(len(durations)*0.95)]*1000:.0f}ms")
            print(f"  Status Codes: {stats['status_codes']}")
        
        # Overall statistics
        all_durations = [r["duration"] for r in self.results]
        total_success = sum(1 for r in self.results if r["success"])
        overall_success_rate = (total_success / len(self.results)) * 100 if self.results else 0
        
        print("\n" + "=" * 60)
        print("OVERALL STATISTICS")
        print("=" * 60)
        print(f"Total Success Rate: {overall_success_rate:.1f}%")
        print(f"Requests per Second: {len(self.results) / self.duration_seconds:.1f}")
        if all_durations:
            print(f"Average Response Time: {statistics.mean(all_durations)*1000:.0f}ms")
            print(f"Median Response Time: {statistics.median(all_durations)*1000:.0f}ms")
            if len(all_durations) > 1:
                print(f"95th Percentile: {sorted(all_durations)[int(len(all_durations)*0.95)]*1000:.0f}ms")
        
        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"load_test_results_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump({
                "config": {
                    "base_url": BASE_URL,
                    "num_users": self.num_users,
                    "duration_seconds": self.duration_seconds,
                    "recorded_at": timestamp
                },
                "summary": {
                    "total_requests": len(self.results),
                    "success_rate": overall_success_rate,
                    "requests_per_second": len(self.results) / self.duration_seconds
                },
                "endpoints": endpoints,
                "raw_results": self.results
            }, f, indent=2)
        
        print(f"\nDetailed results saved to: {filename}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Load test Digital Signage API")
    parser.add_argument("-u", "--users", type=int, default=10, help="Number of concurrent users (default: 10)")
    parser.add_argument("-d", "--duration", type=int, default=60, help="Test duration in seconds (default: 60)")
    parser.add_argument("-b", "--base-url", type=str, default=BASE_URL, help=f"Base URL (default: {BASE_URL})")
    
    args = parser.parse_args()
    
    # Update base URL if provided
    global BASE_URL
    BASE_URL = args.base_url
    
    # Run load test
    runner = LoadTestRunner(args.users, args.duration)
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())