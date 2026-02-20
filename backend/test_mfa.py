#!/usr/bin/env python3
"""
Quick MFA Testing Script
Tests the complete MFA flow
"""
import requests
import time

API_BASE = "http://localhost:5000/api"

def test_mfa_registration():
    """Test registration with MFA enabled"""
    print("=" * 50)
    print("TEST 1: Register with MFA Enabled")
    print("=" * 50)
    
    email = input("Enter your email: ")
    username = input("Enter username (or press Enter for 'testuser'): ") or "testuser"
    password = "testpass123"
    
    response = requests.post(f"{API_BASE}/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
        "enable_mfa": True
    })
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 201:
        data = response.json()
        if data.get('mfa_required'):
            print("\n✅ SUCCESS! MFA code should be sent to your email")
            print(f"📧 Check {email} for your 6-digit code")
            
            # Wait for user to get code
            code = input("\nEnter the 6-digit code from your email: ")
            
            # Verify the code
            print("\n" + "=" * 50)
            print("TEST 2: Verify MFA Code")
            print("=" * 50)
            
            verify_response = requests.post(f"{API_BASE}/auth/verify-mfa", json={
                "email": email,
                "code": code
            })
            
            print(f"\nStatus Code: {verify_response.status_code}")
            print(f"Response: {verify_response.json()}")
            
            if verify_response.status_code == 200:
                data = verify_response.json()
                if 'access_token' in data:
                    print("\n✅ SUCCESS! You're logged in!")
                    print(f"Access Token: {data['access_token'][:50]}...")
                    return data['access_token'], email, password
                else:
                    print("\n❌ FAILED! No access token received")
            else:
                print("\n❌ FAILED! Code verification failed")
        else:
            print("\n❌ FAILED! MFA not required in response")
    else:
        print(f"\n❌ FAILED! Registration failed: {response.json()}")
    
    return None, email, password


def test_mfa_login(email, password):
    """Test login with MFA"""
    print("\n" + "=" * 50)
    print("TEST 3: Login with MFA")
    print("=" * 50)
    
    response = requests.post(f"{API_BASE}/auth/login", json={
        "email": email,
        "password": password
    })
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('mfa_required'):
            print("\n✅ SUCCESS! MFA code sent to your email")
            print(f"📧 Check {email} for your 6-digit code")
            
            code = input("\nEnter the 6-digit code from your email: ")
            
            verify_response = requests.post(f"{API_BASE}/auth/verify-mfa", json={
                "email": email,
                "code": code
            })
            
            print(f"\nVerify Status Code: {verify_response.status_code}")
            print(f"Verify Response: {verify_response.json()}")
            
            if verify_response.status_code == 200:
                print("\n✅ SUCCESS! Login with MFA complete!")
            else:
                print("\n❌ FAILED! Code verification failed")
        else:
            print("\n❌ FAILED! MFA not required in response")
    else:
        print(f"\n❌ FAILED! Login failed: {response.json()}")


def test_enable_mfa_from_profile(token):
    """Test enabling MFA from profile settings"""
    print("\n" + "=" * 50)
    print("TEST 4: Enable MFA from Profile Settings")
    print("=" * 50)
    
    response = requests.post(
        f"{API_BASE}/auth/profile/mfa",
        json={"enable": True},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('mfa_required'):
            print("\n✅ SUCCESS! MFA setup code sent")
            
            code = input("\nEnter the 6-digit code: ")
            
            verify_response = requests.post(
                f"{API_BASE}/auth/profile/mfa/verify",
                json={"code": code},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            print(f"\nVerify Status Code: {verify_response.status_code}")
            print(f"Verify Response: {verify_response.json()}")
            
            if verify_response.status_code == 200:
                print("\n✅ SUCCESS! MFA enabled from profile!")
            else:
                print("\n❌ FAILED! Code verification failed")
        else:
            print("\n❌ FAILED! MFA not required in response")
    else:
        print(f"\n❌ FAILED! Enable MFA failed")


def main():
    print("""
╔════════════════════════════════════════════════════════╗
║                                                        ║
║           ShareMyShows MFA Test Suite                 ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
    """)
    
    print("This script will test the MFA implementation.")
    print("Make sure your server is running on http://localhost:5000\n")
    
    choice = input("Choose test:\n1. Full test (Registration + Login)\n2. Login only\n3. Profile MFA enable\nChoice (1-3): ")
    
    if choice == "1":
        token, email, password = test_mfa_registration()
        if token and email:
            time.sleep(2)
            test_mfa_login(email, password)
    elif choice == "2":
        email = input("Enter email: ")
        password = input("Enter password: ")
        test_mfa_login(email, password)
    elif choice == "3":
        token = input("Enter your JWT token: ")
        test_enable_mfa_from_profile(token)
    else:
        print("Invalid choice")
    
    print("\n" + "=" * 50)
    print("Testing Complete!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
