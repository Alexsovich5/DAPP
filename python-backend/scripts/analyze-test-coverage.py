#!/usr/bin/env python3
"""
Test Coverage Analysis Script
Analyzes test coverage and provides detailed reporting and recommendations
"""

import os
import sys
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime


class TestCoverageAnalyzer:
    """Comprehensive test coverage analysis and reporting"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.coverage_data = {}
        self.recommendations = []
        
    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Run comprehensive coverage analysis"""
        print("🔍 Running Test Coverage Analysis...")
        
        # Generate coverage data
        self._generate_coverage_data()
        
        # Analyze coverage by category
        module_analysis = self._analyze_module_coverage()
        critical_path_analysis = self._analyze_critical_paths()
        test_quality_analysis = self._analyze_test_quality()
        
        # Generate recommendations
        self._generate_recommendations(module_analysis, critical_path_analysis)
        
        # Create comprehensive report
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_coverage": self._get_overall_coverage(),
            "module_analysis": module_analysis,
            "critical_paths": critical_path_analysis,
            "test_quality": test_quality_analysis,
            "recommendations": self.recommendations,
            "coverage_goals": self._check_coverage_goals(),
            "trend_analysis": self._analyze_coverage_trends()
        }
        
        return report
    
    def _generate_coverage_data(self):
        """Generate fresh coverage data"""
        print("📊 Generating coverage data...")
        
        try:
            # Run tests with coverage
            subprocess.run([
                "pytest", "tests/", 
                "--cov=app", 
                "--cov-report=xml:coverage.xml",
                "--cov-report=json:coverage.json",
                "--cov-report=html:htmlcov",
                "--quiet"
            ], check=True, cwd=self.project_root)
            
            print("✅ Coverage data generated successfully")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate coverage data: {e}")
            sys.exit(1)
    
    def _analyze_module_coverage(self) -> Dict[str, Any]:
        """Analyze coverage by module/component"""
        print("🔬 Analyzing module coverage...")
        
        coverage_file = self.project_root / "coverage.json"
        if not coverage_file.exists():
            return {"error": "Coverage data not found"}
        
        with open(coverage_file) as f:
            coverage_data = json.load(f)
        
        files = coverage_data.get("files", {})
        
        # Categorize modules
        categories = {
            "api_routers": [],
            "services": [],
            "models": [],
            "core": [],
            "middleware": [],
            "utils": []
        }
        
        for file_path, file_data in files.items():
            coverage_percent = file_data["summary"]["percent_covered"]
            missing_lines = file_data["summary"]["missing_lines"]
            
            module_info = {
                "file": file_path,
                "coverage": round(coverage_percent, 2),
                "missing_lines": missing_lines,
                "total_lines": file_data["summary"]["num_statements"],
                "covered_lines": file_data["summary"]["covered_lines"]
            }
            
            # Categorize based on file path
            if "api/v1/routers" in file_path:
                categories["api_routers"].append(module_info)
            elif "services/" in file_path:
                categories["services"].append(module_info)
            elif "models/" in file_path:
                categories["models"].append(module_info)
            elif "core/" in file_path:
                categories["core"].append(module_info)
            elif "middleware/" in file_path:
                categories["middleware"].append(module_info)
            elif "utils/" in file_path:
                categories["utils"].append(module_info)
        
        # Calculate category averages
        category_summary = {}
        for category, modules in categories.items():
            if modules:
                avg_coverage = sum(m["coverage"] for m in modules) / len(modules)
                total_lines = sum(m["total_lines"] for m in modules)
                covered_lines = sum(m["covered_lines"] for m in modules)
                
                category_summary[category] = {
                    "average_coverage": round(avg_coverage, 2),
                    "total_lines": total_lines,
                    "covered_lines": covered_lines,
                    "module_count": len(modules),
                    "modules": sorted(modules, key=lambda x: x["coverage"])
                }
        
        return category_summary
    
    def _analyze_critical_paths(self) -> Dict[str, Any]:
        """Analyze coverage of critical application paths"""
        print("🎯 Analyzing critical path coverage...")
        
        critical_modules = {
            "authentication": [
                "app/api/v1/routers/auth.py",
                "app/core/auth.py", 
                "app/core/security.py"
            ],
            "soul_connections": [
                "app/api/v1/routers/soul_connections.py",
                "app/services/soul_compatibility_service.py",
                "app/models/soul_connection.py"
            ],
            "user_safety": [
                "app/services/user_safety.py",
                "app/services/user_safety_simplified.py",
                "app/api/v1/routers/safety.py"
            ],
            "matching_algorithms": [
                "app/services/compatibility.py",
                "app/services/ai_matching_service.py"
            ],
            "real_time_features": [
                "app/api/v1/routers/websocket.py",
                "app/services/realtime.py"
            ]
        }
        
        coverage_file = self.project_root / "coverage.json"
        if not coverage_file.exists():
            return {"error": "Coverage data not found"}
        
        with open(coverage_file) as f:
            coverage_data = json.load(f)
        
        files = coverage_data.get("files", {})
        critical_analysis = {}
        
        for path_name, module_files in critical_modules.items():
            path_coverage = []
            total_lines = 0
            covered_lines = 0
            
            for module_file in module_files:
                if module_file in files:
                    file_data = files[module_file]
                    coverage_percent = file_data["summary"]["percent_covered"]
                    path_coverage.append({
                        "file": module_file,
                        "coverage": round(coverage_percent, 2),
                        "missing_lines": file_data["summary"]["missing_lines"]
                    })
                    total_lines += file_data["summary"]["num_statements"]
                    covered_lines += file_data["summary"]["covered_lines"]
            
            if path_coverage:
                avg_coverage = sum(m["coverage"] for m in path_coverage) / len(path_coverage)
                critical_analysis[path_name] = {
                    "average_coverage": round(avg_coverage, 2),
                    "total_lines": total_lines,
                    "covered_lines": covered_lines,
                    "modules": path_coverage,
                    "is_critical": True,
                    "coverage_goal": 85.0  # Higher goal for critical paths
                }
        
        return critical_analysis
    
    def _analyze_test_quality(self) -> Dict[str, Any]:
        """Analyze test quality metrics"""
        print("📈 Analyzing test quality...")
        
        test_files = list(self.project_root.glob("tests/test_*.py"))
        
        quality_metrics = {
            "total_test_files": len(test_files),
            "test_categories": self._count_test_categories(),
            "test_patterns": self._analyze_test_patterns(),
            "fixture_usage": self._analyze_fixture_usage(),
            "async_test_coverage": self._count_async_tests()
        }
        
        return quality_metrics
    
    def _count_test_categories(self) -> Dict[str, int]:
        """Count tests by category markers"""
        categories = {
            "unit": 0, "integration": 0, "async_tests": 0, 
            "performance": 0, "security": 0
        }
        
        try:
            # Run pytest with collect-only to get test info
            result = subprocess.run([
                "pytest", "tests/", "--collect-only", "-q"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                for category in categories.keys():
                    if f"@pytest.mark.{category}" in line or f"-m {category}" in line:
                        categories[category] += 1
            
        except Exception as e:
            print(f"Warning: Could not analyze test categories: {e}")
        
        return categories
    
    def _analyze_test_patterns(self) -> Dict[str, int]:
        """Analyze test code patterns"""
        patterns = {
            "parametrized_tests": 0,
            "fixture_tests": 0,
            "mock_usage": 0,
            "async_tests": 0
        }
        
        test_files = list(self.project_root.glob("tests/test_*.py"))
        
        for test_file in test_files:
            try:
                with open(test_file) as f:
                    content = f.read()
                    
                if "@pytest.mark.parametrize" in content:
                    patterns["parametrized_tests"] += content.count("@pytest.mark.parametrize")
                
                if "def test_" in content and "," in content:
                    # Rough estimate of fixture usage
                    patterns["fixture_tests"] += content.count("def test_")
                
                if "mock" in content.lower() or "Mock" in content:
                    patterns["mock_usage"] += 1
                
                if "@pytest.mark.asyncio" in content:
                    patterns["async_tests"] += content.count("@pytest.mark.asyncio")
                    
            except Exception as e:
                print(f"Warning: Could not analyze {test_file}: {e}")
        
        return patterns
    
    def _analyze_fixture_usage(self) -> Dict[str, Any]:
        """Analyze test fixture usage"""
        conftest_file = self.project_root / "tests" / "conftest.py"
        
        if not conftest_file.exists():
            return {"error": "conftest.py not found"}
        
        try:
            with open(conftest_file) as f:
                content = f.read()
            
            fixture_count = content.count("@pytest.fixture")
            async_fixture_count = content.count("async def") 
            
            return {
                "total_fixtures": fixture_count,
                "async_fixtures": async_fixture_count,
                "service_fixtures": content.count("_service"),
                "data_fixtures": content.count("_data") + content.count("_users"),
                "file_length": len(content.split('\n'))
            }
            
        except Exception as e:
            return {"error": f"Could not analyze fixtures: {e}"}
    
    def _count_async_tests(self) -> int:
        """Count async test methods"""
        async_test_count = 0
        test_files = list(self.project_root.glob("tests/test_*.py"))
        
        for test_file in test_files:
            try:
                with open(test_file) as f:
                    content = f.read()
                async_test_count += content.count("@pytest.mark.asyncio")
            except Exception:
                continue
        
        return async_test_count
    
    def _get_overall_coverage(self) -> Dict[str, float]:
        """Get overall coverage statistics"""
        coverage_file = self.project_root / "coverage.json"
        
        if not coverage_file.exists():
            return {"error": "Coverage data not found"}
        
        with open(coverage_file) as f:
            coverage_data = json.load(f)
        
        totals = coverage_data.get("totals", {})
        
        return {
            "percent_covered": round(totals.get("percent_covered", 0), 2),
            "covered_lines": totals.get("covered_lines", 0),
            "missing_lines": totals.get("missing_lines", 0),
            "total_lines": totals.get("num_statements", 0)
        }
    
    def _check_coverage_goals(self) -> Dict[str, Any]:
        """Check coverage against defined goals"""
        overall = self._get_overall_coverage()
        
        goals = {
            "overall_minimum": 50.0,
            "critical_paths": 85.0,
            "services": 80.0,
            "api_endpoints": 70.0
        }
        
        current_coverage = overall.get("percent_covered", 0)
        
        return {
            "current_coverage": current_coverage,
            "goals": goals,
            "goal_status": {
                "overall_minimum": current_coverage >= goals["overall_minimum"],
                "on_track": current_coverage >= goals["overall_minimum"] * 0.8
            },
            "improvement_needed": max(0, goals["overall_minimum"] - current_coverage)
        }
    
    def _analyze_coverage_trends(self) -> Dict[str, Any]:
        """Analyze coverage trends over time (if historical data available)"""
        # This would be enhanced with historical data storage
        # For now, provide current snapshot
        
        return {
            "current_snapshot": {
                "timestamp": datetime.now().isoformat(),
                "overall_coverage": self._get_overall_coverage(),
                "test_count": self._count_total_tests()
            },
            "trend_recommendation": "Implement coverage tracking in CI/CD for trend analysis"
        }
    
    def _count_total_tests(self) -> int:
        """Count total number of tests"""
        try:
            result = subprocess.run([
                "pytest", "tests/", "--collect-only", "-q"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            # Count test functions in output
            test_count = result.stdout.count("test_")
            return test_count
        except Exception:
            return 0
    
    def _generate_recommendations(self, module_analysis: Dict, critical_analysis: Dict):
        """Generate coverage improvement recommendations"""
        print("💡 Generating recommendations...")
        
        overall = self._get_overall_coverage()
        current_coverage = overall.get("percent_covered", 0)
        
        # Overall coverage recommendations
        if current_coverage < 50:
            self.recommendations.append({
                "priority": "HIGH",
                "category": "Overall Coverage",
                "issue": f"Overall coverage is {current_coverage}%, below 50% minimum",
                "recommendation": "Focus on unit tests for core business logic",
                "action_items": [
                    "Write unit tests for compatibility algorithms",
                    "Add tests for user authentication flows",
                    "Test input validation and error handling"
                ]
            })
        
        # Module-specific recommendations
        for category, data in module_analysis.items():
            if data.get("average_coverage", 0) < 60:
                low_coverage_modules = [
                    m for m in data.get("modules", []) 
                    if m["coverage"] < 50
                ]
                
                if low_coverage_modules:
                    self.recommendations.append({
                        "priority": "MEDIUM",
                        "category": f"{category.title()} Coverage",
                        "issue": f"Low coverage in {category}: {data['average_coverage']}%",
                        "recommendation": f"Prioritize testing in {category} modules",
                        "action_items": [
                            f"Add tests for {m['file']}" for m in low_coverage_modules[:3]
                        ]
                    })
        
        # Critical path recommendations
        for path_name, data in critical_analysis.items():
            if data.get("average_coverage", 0) < 85:
                self.recommendations.append({
                    "priority": "HIGH",
                    "category": "Critical Path Coverage",
                    "issue": f"{path_name} has {data['average_coverage']}% coverage, below 85% goal",
                    "recommendation": f"Increase test coverage for {path_name} (critical functionality)",
                    "action_items": [
                        f"Add comprehensive tests for {m['file']}" 
                        for m in data.get("modules", []) 
                        if m["coverage"] < 85
                    ]
                })
        
        # Test quality recommendations
        if len(self.recommendations) == 0:
            self.recommendations.append({
                "priority": "LOW",
                "category": "Test Quality",
                "issue": "Coverage goals met, focus on test quality",
                "recommendation": "Enhance test quality and add performance/security tests",
                "action_items": [
                    "Add more async/WebSocket tests",
                    "Implement performance benchmarks",
                    "Add security-focused tests",
                    "Improve test documentation"
                ]
            })
    
    def generate_report(self, output_file: str = "coverage_analysis_report.md"):
        """Generate comprehensive coverage report"""
        analysis = self.run_coverage_analysis()
        
        report_content = self._format_markdown_report(analysis)
        
        output_path = self.project_root / output_file
        with open(output_path, 'w') as f:
            f.write(report_content)
        
        print(f"📋 Coverage analysis report generated: {output_path}")
        return output_path
    
    def _format_markdown_report(self, analysis: Dict) -> str:
        """Format analysis results as markdown report"""
        overall = analysis["overall_coverage"]
        
        report = f"""# Test Coverage Analysis Report

**Generated**: {analysis["timestamp"]}  
**Overall Coverage**: {overall.get("percent_covered", 0)}%

## Executive Summary

Current test coverage is **{overall.get("percent_covered", 0)}%** with {overall.get("covered_lines", 0)} of {overall.get("total_lines", 0)} lines covered.

### Coverage Goals Status
- **Minimum Required**: 50% ({'✅' if overall.get("percent_covered", 0) >= 50 else '❌'})
- **Target Goal**: 70% ({'✅' if overall.get("percent_covered", 0) >= 70 else '❌'})
- **Critical Paths**: 85% (See detailed analysis below)

## Module Coverage Analysis

"""
        
        # Module analysis
        for category, data in analysis["module_analysis"].items():
            if data and "average_coverage" in data:
                status = "✅" if data["average_coverage"] >= 70 else "⚠️" if data["average_coverage"] >= 50 else "❌"
                report += f"### {category.replace('_', ' ').title()} {status}\n"
                report += f"- **Average Coverage**: {data['average_coverage']}%\n"
                report += f"- **Total Lines**: {data['total_lines']}\n"
                report += f"- **Modules**: {data['module_count']}\n\n"
                
                # Show lowest coverage modules
                low_coverage = [m for m in data["modules"] if m["coverage"] < 60]
                if low_coverage:
                    report += "**Low Coverage Modules**:\n"
                    for module in low_coverage[:3]:
                        report += f"- {module['file']}: {module['coverage']}%\n"
                    report += "\n"
        
        # Critical paths analysis
        report += "## Critical Path Coverage\n\n"
        for path_name, data in analysis["critical_paths"].items():
            if "average_coverage" in data:
                status = "✅" if data["average_coverage"] >= 85 else "⚠️" if data["average_coverage"] >= 70 else "❌"
                report += f"### {path_name.replace('_', ' ').title()} {status}\n"
                report += f"- **Coverage**: {data['average_coverage']}%\n"
                report += f"- **Goal**: 85%\n"
                report += f"- **Gap**: {max(0, 85 - data['average_coverage']):.1f}%\n\n"
        
        # Test quality metrics
        test_quality = analysis["test_quality"]
        report += f"""## Test Quality Metrics

- **Total Test Files**: {test_quality["total_test_files"]}
- **Async Tests**: {test_quality["async_test_coverage"]}
- **Test Fixtures**: {test_quality["fixture_usage"].get("total_fixtures", 0)}
- **Parametrized Tests**: {test_quality["test_patterns"]["parametrized_tests"]}

### Test Categories
"""
        for category, count in test_quality["test_categories"].items():
            report += f"- **{category.title()}**: {count} tests\n"
        
        # Recommendations
        report += "\n## Recommendations\n\n"
        for i, rec in enumerate(analysis["recommendations"], 1):
            priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
            emoji = priority_emoji.get(rec["priority"], "⚪")
            
            report += f"### {i}. {rec['category']} {emoji}\n"
            report += f"**Priority**: {rec['priority']}\n\n"
            report += f"**Issue**: {rec['issue']}\n\n"
            report += f"**Recommendation**: {rec['recommendation']}\n\n"
            
            if rec.get("action_items"):
                report += "**Action Items**:\n"
                for item in rec["action_items"]:
                    report += f"- {item}\n"
            report += "\n"
        
        # Next steps
        report += """## Next Steps

1. **Immediate Actions** (High Priority)
   - Address critical path coverage gaps
   - Add unit tests for low-coverage modules
   
2. **Short Term** (Medium Priority)  
   - Improve module coverage to 70%+
   - Add integration tests for key workflows
   
3. **Long Term** (Low Priority)
   - Enhance test quality and patterns
   - Implement coverage trend tracking
   - Add performance and security tests

## Coverage Tracking

To track coverage improvements:
```bash
# Generate coverage report
./scripts/run-tests.sh all

# Analyze coverage
python scripts/analyze-test-coverage.py

# View detailed coverage
open htmlcov/index.html
```

---
*Generated by Test Coverage Analyzer*
"""
        
        return report


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze test coverage")
    parser.add_argument("--output", "-o", default="coverage_analysis_report.md",
                       help="Output report file name")
    parser.add_argument("--json", action="store_true", 
                       help="Output JSON format")
    
    args = parser.parse_args()
    
    analyzer = TestCoverageAnalyzer()
    
    if args.json:
        # Output JSON analysis
        analysis = analyzer.run_coverage_analysis()
        output_file = args.output.replace('.md', '.json')
        
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"📄 JSON analysis saved to: {output_file}")
    else:
        # Generate markdown report
        report_path = analyzer.generate_report(args.output)
        print(f"✅ Analysis complete! Report: {report_path}")


if __name__ == "__main__":
    main()