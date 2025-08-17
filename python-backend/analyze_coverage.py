#!/usr/bin/env python3

import json

def analyze_coverage():
    with open('coverage.json', 'r') as f:
        data = json.load(f)

    print('=== SERVICE COVERAGE ANALYSIS ===')
    services = []
    for file_path, file_data in data['files'].items():
        if 'services/' in file_path:
            coverage = file_data['summary']['percent_covered']
            missing = file_data['summary']['missing_lines']
            total = file_data['summary']['num_statements']
            services.append((file_path, coverage, missing, total))

    services.sort(key=lambda x: x[1])  # Sort by coverage

    print(f"{'Service':<50} {'Coverage':<10} {'Missing':<10} {'Total':<10}")
    print('-' * 80)
    for service, coverage, missing, total in services:
        service_name = service.split('/')[-1]
        print(f'{service_name:<50} {coverage:<10.1f}% {missing:<10} {total:<10}')

    print('\n=== ROUTER COVERAGE ANALYSIS ===')
    routers = []
    for file_path, file_data in data['files'].items():
        if 'routers/' in file_path:
            coverage = file_data['summary']['percent_covered']
            missing = file_data['summary']['missing_lines']
            total = file_data['summary']['num_statements']
            routers.append((file_path, coverage, missing, total))

    routers.sort(key=lambda x: x[1])  # Sort by coverage

    print(f"{'Router':<50} {'Coverage':<10} {'Missing':<10} {'Total':<10}")
    print('-' * 80)
    for router, coverage, missing, total in routers:
        router_name = router.split('/')[-1]
        print(f'{router_name:<50} {coverage:<10.1f}% {missing:<10} {total:<10}')

if __name__ == "__main__":
    analyze_coverage()