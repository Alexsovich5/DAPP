#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, '/Users/alex/Desktop/Projects/DAPP/python-backend')

# Set testing environment
os.environ["TESTING"] = "1"

from app.core.security import get_password_hash, verify_password

def test_password_compatibility():
    print("=== Testing Password Compatibility ===")
    
    # Test the exact same scenario as the test
    password = "testpassword"
    
    print(f"Testing with password: '{password}'")
    
    # Create hash like the test fixture does
    hashed = get_password_hash(password)
    print(f"Generated hash: {hashed}")
    
    # Test verification like the test fixture does
    verification1 = verify_password(password, hashed)
    print(f"First verification (fixture style): {verification1}")
    
    # Test verification multiple times to see if it's consistent
    verification2 = verify_password(password, hashed)
    print(f"Second verification: {verification2}")
    
    verification3 = verify_password(password, hashed)
    print(f"Third verification: {verification3}")
    
    # Test with wrong password
    wrong_verification = verify_password("wrongpassword", hashed)
    print(f"Wrong password verification: {wrong_verification}")
    
    # Test with slight variations
    caps_verification = verify_password("TESTPASSWORD", hashed)
    print(f"Caps variation verification: {caps_verification}")
    
    space_verification = verify_password("testpassword ", hashed)
    print(f"Space variation verification: {space_verification}")
    
    # Test creating multiple hashes of the same password
    hash2 = get_password_hash(password)
    hash3 = get_password_hash(password)
    
    print(f"\nMultiple hashes of same password:")
    print(f"Hash 1: {hashed}")
    print(f"Hash 2: {hash2}")
    print(f"Hash 3: {hash3}")
    print(f"Hashes are different (expected): {len(set([hashed, hash2, hash3])) == 3}")
    
    # Test all hashes work with original password
    verify_hash2 = verify_password(password, hash2)
    verify_hash3 = verify_password(password, hash3)
    print(f"Hash 2 verifies: {verify_hash2}")
    print(f"Hash 3 verifies: {verify_hash3}")
    
    if all([verification1, verification2, verification3, verify_hash2, verify_hash3]):
        print("\n✅ Password hashing and verification is working correctly")
    else:
        print("\n❌ Password hashing and verification has issues!")
        
    if not wrong_verification and not caps_verification and not space_verification:
        print("✅ Password verification correctly rejects wrong passwords")
    else:
        print("❌ Password verification incorrectly accepts wrong passwords!")

if __name__ == "__main__":
    test_password_compatibility()