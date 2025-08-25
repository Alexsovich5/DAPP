#!/usr/bin/env python3
"""
Comprehensive linting fix for AI modules
"""

import os
import re
import autopep8

def fix_ai_linting():
    """Fix linting issues in AI modules"""
    
    ai_dir = "app/ai"
    
    for filename in os.listdir(ai_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(ai_dir, filename)
            print(f"Fixing {filepath}...")
            
            # Read file
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Apply autopep8 fixes
            fixed_content = autopep8.fix_code(
                content,
                options={
                    'max_line_length': 79,
                    'aggressive': 2,
                    'experimental': True
                }
            )
            
            # Additional custom fixes
            fixed_content = apply_custom_fixes(fixed_content, filename)
            
            # Write back
            with open(filepath, 'w') as f:
                f.write(fixed_content)
            
            print(f"Fixed {filepath}")

def apply_custom_fixes(content: str, filename: str) -> str:
    """Apply custom fixes for specific issues"""
    
    # Remove unused imports
    if 'from app.core.config import settings' in content and 'settings.' not in content:
        content = re.sub(r'from app\.core\.config import settings\n', '', content)
    
    if 'from app.ai.model_storage import model_storage_manager' in content and 'model_storage_manager' not in content:
        content = re.sub(r'from app\.ai\.model_storage import model_storage_manager\n', '', content)
    
    # Fix undefined redis_cluster_manager
    if 'redis_cluster_manager' in content and 'from app.core.redis_cluster import redis_cluster_manager' not in content:
        # Add missing import after other imports
        lines = content.split('\n')
        import_end = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                import_end = i
        
        lines.insert(import_end + 1, 'from app.core.redis_cluster import redis_cluster_manager')
        content = '\n'.join(lines)
    
    # Fix event_publisher import if missing
    if 'event_publisher' in content and 'from app.core.event_publisher import event_publisher' not in content:
        lines = content.split('\n')
        import_end = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                import_end = i
        
        lines.insert(import_end + 1, 'from app.core.event_publisher import event_publisher')
        content = '\n'.join(lines)
    
    # Remove empty lines with whitespace
    content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)
    
    # Fix continuation line indentation
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        if i > 0 and line.strip() and not line.startswith(' ' * 4) and not line.startswith('\t'):
            prev_line = lines[i-1]
            if prev_line.endswith('(') or prev_line.endswith(',') or prev_line.endswith('\\'):
                # This is a continuation line, fix indentation
                stripped = line.lstrip()
                if stripped:
                    line = ' ' * 8 + stripped  # Use 8 spaces for continuation
        
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Ensure file ends with newline
    if not content.endswith('\n'):
        content += '\n'
    
    return content

if __name__ == "__main__":
    fix_ai_linting()