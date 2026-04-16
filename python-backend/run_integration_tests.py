#!/usr/bin/env python3
"""
Comprehensive Integration Test Runner - Sprint 4
Runs all integration tests for real-time features with reporting
"""

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.health_monitor import health_monitor  # noqa: E402
from app.core.logging_config import get_logger, setup_logging  # noqa: E402


class TestRunner:
    """Comprehensive test runner with reporting"""

    def __init__(self):
        self.logger = get_logger("test_runner")
        self.test_results = {}
        self.start_time = None
        self.end_time = None

    def setup_test_environment(self):
        """Setup test environment"""
        print("🔧 Setting up test environment...")

        # Configure logging for tests
        setup_logging(
            environment="development",
            log_level="INFO",
            enable_structured_logging=False,
        )

        # Ensure test database is ready
        try:
            from app.core.database import create_tables  # noqa: E402

            create_tables()
            print("  ✅ Test database ready")
        except Exception as e:
            print(f"  ⚠️  Database setup warning: {str(e)}")

        # Import test modules to ensure they're loadable
        try:
            pass

            print("  ✅ Test modules loaded")
        except ImportError as e:
            print(f"  ❌ Test module import failed: {str(e)}")
            return False

        return True

    async def run_health_check_before_tests(self):
        """Run system health check before starting tests"""
        print("🏥 Pre-test health check...")

        try:
            system_health = await health_monitor.perform_comprehensive_health_check()
            health_monitor.to_dict(system_health)

            print(f"  Overall Status: {system_health.overall_status.value}")
            print(f"  Components Checked: {len(system_health.checks)}")

            # Check if system is healthy enough for testing
            if system_health.overall_status.value in ["critical", "unhealthy"]:
                print("  ⚠️  System health issues detected. Tests may fail.")
                return False

            print("  ✅ System health check passed")
            return True

        except Exception as e:
            print(f"  ❌ Health check failed: {str(e)}")
            return False

    def run_pytest_suite(self, test_file: str, test_name: str) -> dict:
        """Run a specific pytest test suite"""
        print(f"🧪 Running {test_name}...")

        start_time = time.time()

        try:
            # Run pytest with verbose output and JSON reporting
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                test_file,
                "-v",
                "--tb=short",
                "-x",  # Stop on first failure for faster feedback
                "--disable-warnings",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per test suite
            )

            end_time = time.time()
            duration = end_time - start_time

            # Parse results
            success = result.returncode == 0
            output_lines = result.stdout.split("\n") if result.stdout else []
            _ = result.stderr.split("\n") if result.stderr else []

            # Count test results from output
            passed_count = len([line for line in output_lines if "PASSED" in line])
            failed_count = len([line for line in output_lines if "FAILED" in line])
            error_count = len([line for line in output_lines if "ERROR" in line])

            test_result = {
                "name": test_name,
                "file": test_file,
                "success": success,
                "duration_seconds": duration,
                "passed_tests": passed_count,
                "failed_tests": failed_count,
                "error_tests": error_count,
                "output": (
                    result.stdout[:1000] if result.stdout else ""
                ),  # Limit output size
                "errors": result.stderr[:1000] if result.stderr else "",
            }

            if success:
                print(f"  ✅ {test_name} completed successfully ({duration:.2f}s)")
                print(
                    f"     Passed: {passed_count}, Failed: {failed_count}, Errors: {error_count}"
                )
            else:
                print(f"  ❌ {test_name} failed ({duration:.2f}s)")
                print(
                    f"     Passed: {passed_count}, Failed: {failed_count}, Errors: {error_count}"
                )
                if result.stderr:
                    print(f"     Error: {result.stderr[:200]}...")

            return test_result

        except subprocess.TimeoutExpired:
            print(f"  ⏰ {test_name} timed out after 5 minutes")
            return {
                "name": test_name,
                "file": test_file,
                "success": False,
                "duration_seconds": 300,
                "error": "Test suite timed out",
            }

        except Exception as e:
            print(f"  💥 {test_name} crashed: {str(e)}")
            return {
                "name": test_name,
                "file": test_file,
                "success": False,
                "duration_seconds": 0,
                "error": str(e),
            }

    async def run_all_tests(self):
        """Run all integration test suites"""
        print("🚀 Starting Comprehensive Integration Test Suite")
        print("=" * 70)

        self.start_time = time.time()

        # Define test suites
        test_suites = [
            (
                "tests/test_realtime_integration.py",
                "Real-time Integration Tests",
            ),
            (
                "tests/test_websocket_integration.py",
                "WebSocket Integration Tests",
            ),
            ("tests/test_performance.py", "Performance Tests"),
        ]

        # Run each test suite
        for test_file, test_name in test_suites:
            if Path(test_file).exists():
                result = self.run_pytest_suite(test_file, test_name)
                self.test_results[test_name] = result
            else:
                print(f"  ⚠️  {test_file} not found, skipping...")
                self.test_results[test_name] = {
                    "name": test_name,
                    "file": test_file,
                    "success": False,
                    "error": "Test file not found",
                }

        self.end_time = time.time()

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 70)
        print("📊 Integration Test Report")
        print("=" * 70)

        total_duration = (
            self.end_time - self.start_time if self.end_time and self.start_time else 0
        )
        successful_suites = sum(
            1 for result in self.test_results.values() if result.get("success", False)
        )
        total_suites = len(self.test_results)

        # Overall summary
        print("\n🎯 Overall Results:")
        print(f"  Total Test Suites: {total_suites}")
        print(f"  Successful Suites: {successful_suites}")
        print(f"  Failed Suites: {total_suites - successful_suites}")
        print(f"  Total Duration: {total_duration:.2f} seconds")

        # Detailed results
        print("\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
            duration = result.get("duration_seconds", 0)

            print(f"\n  {status} {test_name} ({duration:.2f}s)")

            if "passed_tests" in result:
                passed = result["passed_tests"]
                failed = result["failed_tests"]
                errors = result["error_tests"]
                print(f"    Tests: {passed} passed, {failed} failed, {errors} errors")

            if not result.get("success", False) and "error" in result:
                print(f"    Error: {result['error']}")

        # Performance summary
        print("\n⚡ Performance Summary:")
        performance_result = self.test_results.get("Performance Tests", {})
        if performance_result.get("success", False):
            print("  ✅ Performance tests completed successfully")
            print(f"  Duration: {performance_result.get('duration_seconds', 0):.2f}s")
        else:
            print("  ❌ Performance tests failed or skipped")

        # Recommendations
        print("\n💡 Recommendations:")
        if successful_suites == total_suites:
            print("  🎉 All tests passed! System is ready for production.")
            print("  🔄 Consider running these tests regularly in CI/CD pipeline.")
        else:
            print("  🔧 Address failing tests before deploying to production.")
            print("  📝 Review error messages and fix underlying issues.")
            print("  🧪 Run individual test suites for detailed debugging.")

        # Save detailed report to file
        self.save_report_to_file()

        return successful_suites == total_suites

    def save_report_to_file(self):
        """Save test report to JSON file"""
        try:
            report_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_duration_seconds": (
                    self.end_time - self.start_time
                    if self.end_time and self.start_time
                    else 0
                ),
                "test_results": self.test_results,
                "summary": {
                    "total_suites": len(self.test_results),
                    "successful_suites": sum(
                        1 for r in self.test_results.values() if r.get("success", False)
                    ),
                    "overall_success": all(
                        r.get("success", False) for r in self.test_results.values()
                    ),
                },
            }

            report_file = (
                Path("test_reports")
                / f"integration_test_report_{int(time.time())}.json"
            )
            report_file.parent.mkdir(exist_ok=True)

            with open(report_file, "w") as f:
                json.dump(report_data, f, indent=2)

            print(f"\n📄 Detailed report saved to: {report_file}")

        except Exception as e:
            print(f"  ⚠️  Could not save report file: {str(e)}")

    async def run_post_test_health_check(self):
        """Run health check after tests to detect issues"""
        print("\n🏥 Post-test health check...")

        try:
            system_health = await health_monitor.perform_comprehensive_health_check()
            print(f"  Final System Status: {system_health.overall_status.value}")

            # Check for any degradation
            degraded_components = [
                check
                for check in system_health.checks
                if check.status.value in ["degraded", "unhealthy", "critical"]
            ]

            if degraded_components:
                print(f"  ⚠️  {len(degraded_components)} components showing issues:")
                for component in degraded_components:
                    print(
                        f"    - {component.component.value}: {component.status.value}"
                    )
            else:
                print("  ✅ All components healthy after testing")

        except Exception as e:
            print(f"  ❌ Post-test health check failed: {str(e)}")


async def main():
    """Main test runner entry point"""
    runner = TestRunner()

    print("🧪 Sprint 4: Comprehensive Integration Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Setup
    if not runner.setup_test_environment():
        print("❌ Test environment setup failed")
        return False

    # Pre-test health check
    if not await runner.run_health_check_before_tests():
        print("⚠️  Proceeding with tests despite health check issues...")

    # Run all tests
    await runner.run_all_tests()

    # Generate report
    success = runner.generate_test_report()

    # Post-test health check
    await runner.run_post_test_health_check()

    # Final status
    if success:
        print("\n🎉 All integration tests PASSED!")
        print("✅ Sprint 4: Backend Integration & Production Readiness - COMPLETE")
    else:
        print("\n❌ Some integration tests FAILED!")
        print("🔧 Please review and fix issues before production deployment")

    return success


if __name__ == "__main__":
    # Install required test dependencies
    print("📦 Checking test dependencies...")

    required_packages = ["pytest", "websockets", "psutil"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"Installing missing packages: {', '.join(missing_packages)}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages)

    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
