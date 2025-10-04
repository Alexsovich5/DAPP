#!/usr/bin/env python3
"""
Security Headers Test Script
Tests that all security headers are properly implemented in the Dinner First API
"""

import sys
from typing import Dict

import requests


def test_security_headers(
    base_url: str = "http://localhost:5000",
) -> Dict[str, bool]:
    """
    Test all security headers on the API endpoints

    Args:
        base_url: Base URL of the API server

    Returns:
        Dictionary with test results for each security header
    """
    results = {}

    # Test endpoints
    endpoints = [
        "/",
        "/health",
        "/api/v1/docs",
        "/api/v1/auth/login",
    ]  # POST endpoint

    print(f"🔒 Testing Security Headers for {base_url}")
    print("=" * 60)

    for endpoint in endpoints:
        print(f"\n📍 Testing endpoint: {endpoint}")

        try:
            # Test GET request
            response = requests.get(
                f"{base_url}{endpoint}",
                headers={
                    "Origin": "http://localhost:4200",  # Simulate Angular frontend
                    "User-Agent": "DinnerFirst-SecurityTest/1.0",
                },
                timeout=10,
            )

            headers = response.headers
            endpoint_results = {}

            # Security headers to check
            security_headers = {
                "Content-Security-Policy": "Content security policy",
                "X-Content-Type-Options": "MIME type sniffing protection",
                "X-Frame-Options": "Clickjacking protection",
                "X-XSS-Protection": "XSS protection",
                "Referrer-Policy": "Referrer policy",
                "Permissions-Policy": "Permissions policy",
                "X-Permitted-Cross-Domain-Policies": "Cross-domain policy",
                "Cache-Control": "Cache control",
                "X-Dating-Platform-Security": "Custom security header",
            }

            print(f"   Status Code: {response.status_code}")

            for header, description in security_headers.items():
                present = header in headers
                endpoint_results[header] = present

                status = "✅" if present else "❌"
                value = (
                    headers.get(header, "NOT PRESENT")[:50] + "..."
                    if len(headers.get(header, "")) > 50
                    else headers.get(header, "NOT PRESENT")
                )
                print(f"   {status} {header}: {value}")

            # CORS headers check
            cors_headers = {
                "Access-Control-Allow-Origin": "CORS origin",
                "Access-Control-Allow-Methods": "CORS methods",
                "Access-Control-Allow-Headers": "CORS headers",
            }

            print("   \n   CORS Headers:")
            for header, description in cors_headers.items():
                present = header in headers
                status = "✅" if present else "❌"
                value = headers.get(header, "NOT PRESENT")
                print(f"   {status} {header}: {value}")

            # Check for removed/secured headers
            insecure_headers = ["Server", "X-Powered-By"]
            print("   \n   Security Header Removal:")
            for header in insecure_headers:
                removed = header not in headers
                status = "✅" if removed else "⚠️"
                action = "REMOVED" if removed else f"PRESENT: {headers.get(header)}"
                print(f"   {status} {header}: {action}")

            results[endpoint] = endpoint_results

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error testing {endpoint}: {str(e)}")
            results[endpoint] = {"error": str(e)}

    return results


def test_cors_preflight(
    base_url: str = "http://localhost:5000",
) -> Dict[str, any]:
    """
    Test CORS preflight requests
    """
    print("\n🌐 Testing CORS Preflight Requests")
    print("=" * 40)

    try:
        # Simulate Angular preflight request
        response = requests.options(
            f"{base_url}/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:4200",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            },
            timeout=10,
        )

        print(f"Status Code: {response.status_code}")

        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers",
            "Access-Control-Allow-Credentials",
            "Access-Control-Max-Age",
        ]

        for header in cors_headers:
            value = response.headers.get(header, "NOT PRESENT")
            status = "✅" if value != "NOT PRESENT" else "❌"
            print(f"{status} {header}: {value}")

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
        }

    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing CORS preflight: {str(e)}")
        return {"error": str(e)}


def generate_security_report(results: Dict[str, any]) -> None:
    """
    Generate a summary security report
    """
    print("\n📊 Security Headers Summary Report")
    print("=" * 50)

    len(results)
    total_headers_checked = 0
    total_headers_present = 0

    for endpoint, endpoint_results in results.items():
        if "error" not in endpoint_results:
            total_headers_checked += len(endpoint_results)
            total_headers_present += sum(
                1 for present in endpoint_results.values() if present
            )

    if total_headers_checked > 0:
        coverage_percentage = (total_headers_present / total_headers_checked) * 100
        print(
            f"Security Headers Coverage: {coverage_percentage:.1f}% ({total_headers_present}/{total_headers_checked})"
        )

    # Security recommendations
    print("\n🛡️  Security Recommendations:")
    print("- Ensure HTTPS is enabled in production")
    print("- Verify CSP policy allows necessary resources only")
    print("- Test CORS configuration with actual frontend domain")
    print("- Monitor security headers in production regularly")

    # Grade the implementation
    if total_headers_checked > 0:
        if coverage_percentage >= 90:
            grade = "A+"
            print(f"\n🏆 Security Grade: {grade} - Excellent security implementation!")
        elif coverage_percentage >= 80:
            grade = "A"
            print(f"\n🎉 Security Grade: {grade} - Great security implementation!")
        elif coverage_percentage >= 70:
            grade = "B"
            print(f"\n👍 Security Grade: {grade} - Good security implementation!")
        else:
            grade = "C"
            print(f"\n⚠️  Security Grade: {grade} - Security headers need improvement!")


if __name__ == "__main__":
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"

    print("🧪 Dinner First API Security Headers Test")
    print("Testing Soul Before Skin platform security implementation")
    print("=" * 60)

    try:
        # Test security headers
        header_results = test_security_headers(base_url)

        # Test CORS preflight
        cors_results = test_cors_preflight(base_url)

        # Generate report
        generate_security_report(header_results)

        print("\n✅ Security test completed successfully!")
        print(f"💡 Run with: python test_security_headers.py {base_url}")

    except Exception as e:
        print(f"\n❌ Security test failed: {str(e)}")
        sys.exit(1)
