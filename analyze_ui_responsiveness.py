#!/usr/bin/env python3
"""
Automatic UI Responsiveness Patcher
====================================

This script automatically identifies and patches UI components that use fixed sizes,
making them responsive across different screen resolutions.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

def find_python_ui_files(base_path: str) -> List[Path]:
    """Find all Python UI files in the project"""
    ui_patterns = [
        "**/gui/**/*.py",
        "**/windows/**/*.py", 
        "**/components/**/*.py",
        "**/widgets/**/*.py"
    ]
    
    files = []
    base = Path(base_path)
    
    for pattern in ui_patterns:
        files.extend(base.glob(pattern))
    
    return sorted(list(set(files)))

def analyze_fixed_sizes(file_path: Path) -> Dict[str, List[Tuple[int, str]]]:
    """Analyze a file for fixed size usage"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}
    
    issues = {
        'setFixedSize': [],
        'setGeometry': [],
        'setMinimumSize': [],
        'setMaximumSize': [],
        'resize': [],
        'setColumnWidth': [],
        'setRowHeight': [],
        'font_size': [],
        'padding': [],
        'margins': []
    }
    
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Check for fixed size methods
        if 'setFixedSize(' in line:
            issues['setFixedSize'].append((line_num, line.strip()))
        
        if 'setGeometry(' in line:
            issues['setGeometry'].append((line_num, line.strip()))
            
        if 'setMinimumSize(' in line:
            issues['setMinimumSize'].append((line_num, line.strip()))
            
        if 'setMaximumSize(' in line:
            issues['setMaximumSize'].append((line_num, line.strip()))
            
        if '.resize(' in line:
            issues['resize'].append((line_num, line.strip()))
            
        if 'setColumnWidth(' in line:
            issues['setColumnWidth'].append((line_num, line.strip()))
            
        if 'setRowHeight(' in line or 'setDefaultSectionSize(' in line:
            issues['setRowHeight'].append((line_num, line.strip()))
            
        # Check for hardcoded font sizes
        if re.search(r'font-size:\s*\d+px', line):
            issues['font_size'].append((line_num, line.strip()))
            
        # Check for hardcoded padding/margins in stylesheets
        if re.search(r'(padding|margin):\s*\d+px', line):
            issues['padding'].append((line_num, line.strip()))
    
    # Filter out empty issues
    return {k: v for k, v in issues.items() if v}

def generate_responsive_suggestions(file_path: Path, issues: Dict[str, List[Tuple[int, str]]]) -> List[str]:
    """Generate suggestions for making the code responsive"""
    suggestions = []
    
    if not issues:
        return suggestions
    
    suggestions.append(f"\n📁 FILE: {file_path}")
    suggestions.append("=" * 60)
    
    # Check if already imports responsive utilities
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            has_responsive_import = 'responsive_utils' in content
    except:
        has_responsive_import = False
    
    if not has_responsive_import:
        suggestions.append("\n🔧 REQUIRED IMPORTS:")
        suggestions.append("Add to imports section:")
        suggestions.append("from src.gui.utils.responsive_utils import ResponsiveWidget, make_window_responsive")
        suggestions.append("\nUpdate class definition:")
        suggestions.append("class YourWidget(OriginalClass, ResponsiveWidget):")
        suggestions.append("    def __init__(self):")
        suggestions.append("        OriginalClass.__init__(self)")
        suggestions.append("        ResponsiveWidget.__init__(self)")
    
    # Specific suggestions for each type of issue
    if 'setFixedSize' in issues:
        suggestions.append(f"\n❌ FIXED SIZES ({len(issues['setFixedSize'])} found):")
        for line_num, line in issues['setFixedSize']:
            suggestions.append(f"  Line {line_num}: {line}")
        suggestions.append("✅ SOLUTION: Replace with responsive sizing:")
        suggestions.append("  self.set_responsive_size(base_width, base_height)")
    
    if 'setGeometry' in issues:
        suggestions.append(f"\n❌ FIXED GEOMETRY ({len(issues['setGeometry'])} found):")
        for line_num, line in issues['setGeometry']:
            suggestions.append(f"  Line {line_num}: {line}")
        suggestions.append("✅ SOLUTION: Use responsive positioning:")
        suggestions.append("  make_window_responsive(self, content_width, content_height)")
    
    if 'setColumnWidth' in issues:
        suggestions.append(f"\n❌ FIXED COLUMN WIDTHS ({len(issues['setColumnWidth'])} found):")
        for line_num, line in issues['setColumnWidth']:
            suggestions.append(f"  Line {line_num}: {line}")
        suggestions.append("✅ SOLUTION: Scale column widths:")
        suggestions.append("  scaled_width, _ = self.screen_utils.scale_size(base_width, 20)")
        suggestions.append("  table.setColumnWidth(col, scaled_width)")
    
    if 'font_size' in issues:
        suggestions.append(f"\n❌ FIXED FONT SIZES ({len(issues['font_size'])} found):")
        for line_num, line in issues['font_size']:
            suggestions.append(f"  Line {line_num}: {line}")
        suggestions.append("✅ SOLUTION: Use responsive font sizing:")
        suggestions.append("  font_size = self.get_responsive_font_size(base_size)")
        suggestions.append("  f'font-size: {font_size}px;'")
    
    if 'padding' in issues:
        suggestions.append(f"\n❌ FIXED PADDING/MARGINS ({len(issues['padding'])} found):")
        for line_num, line in issues['padding']:
            suggestions.append(f"  Line {line_num}: {line}")
        suggestions.append("✅ SOLUTION: Use responsive spacing:")
        suggestions.append("  spacing = self.get_responsive_spacing()")
        suggestions.append("  margins = self.get_responsive_margins()")
        suggestions.append("  f'padding: {spacing[\"medium\"]}px;'")
    
    return suggestions

def analyze_project_responsiveness(base_path: str = "."):
    """Analyze entire project for responsiveness issues"""
    print("🔍 ANALYZING PROJECT FOR UI RESPONSIVENESS")
    print("=" * 60)
    
    ui_files = find_python_ui_files(base_path)
    print(f"Found {len(ui_files)} UI files to analyze")
    
    total_issues = 0
    all_suggestions = []
    
    for file_path in ui_files:
        if 'responsive_utils.py' in str(file_path):
            continue  # Skip our own utility file
            
        issues = analyze_fixed_sizes(file_path)
        if issues:
            issue_count = sum(len(v) for v in issues.values())
            total_issues += issue_count
            
            suggestions = generate_responsive_suggestions(file_path, issues)
            all_suggestions.extend(suggestions)
    
    # Summary
    print(f"\n📊 ANALYSIS SUMMARY:")
    print(f"   Files analyzed: {len(ui_files)}")
    print(f"   Files with issues: {len([f for f in ui_files if analyze_fixed_sizes(f)])}")
    print(f"   Total issues found: {total_issues}")
    
    if total_issues > 0:
        print(f"\n📋 DETAILED ANALYSIS:")
        for suggestion in all_suggestions:
            print(suggestion)
        
        print(f"\n🚀 NEXT STEPS:")
        print("1. Add responsive utility imports to files with issues")
        print("2. Update class definitions to inherit from ResponsiveWidget") 
        print("3. Replace fixed sizes with responsive equivalents")
        print("4. Test on different screen resolutions")
        print("5. Use create_responsive_stylesheet() for consistent styling")
    else:
        print("✅ No responsiveness issues found!")

def create_responsiveness_implementation_plan():
    """Create a step-by-step implementation plan"""
    plan = """
🎯 RESPONSIVENESS IMPLEMENTATION PLAN
=====================================

PHASE 1: Core Infrastructure ✅ COMPLETED
• Created responsive_utils.py with ScreenUtils and ResponsiveWidget
• Implemented automatic scaling calculations
• Added responsive stylesheet generation
• Created make_window_responsive() helper

PHASE 2: Main Components (IN PROGRESS)
• ✅ Updated main_window.py
• ✅ Updated dimensional_table_ui.py 
• ✅ Updated dimensional_study_window.py
• ⏳ Update remaining window classes
• ⏳ Update widget classes

PHASE 3: Specific Improvements (TODO)
• Update all setFixedSize() calls to use responsive sizing
• Convert hardcoded column widths to responsive scaling
• Replace fixed font sizes with responsive calculations
• Update all padding/margin values in stylesheets
• Test on multiple screen resolutions

PHASE 4: Testing & Validation (TODO)
• Test on 1366x768 (small laptops)
• Test on 1600x900 (medium laptops)
• Test on 1920x1080 (standard desktop)  
• Test on 2560x1440 (high-res monitors)
• Test on 4K displays
• Verify all UI elements are visible and usable

KEY BENEFITS:
• Automatic adaptation to any screen resolution
• Consistent user experience across devices
• No more cut-off widgets or buttons
• Professional appearance on all displays
• Improved usability for different screen sizes
"""
    
    print(plan)

def main():
    """Main function"""
    print("🎯 PYTHON TECNICA RESPONSIVENESS ANALYZER")
    print("=========================================")
    
    # Analyze current project
    analyze_project_responsiveness(".")
    
    print("\n" + "="*60)
    create_responsiveness_implementation_plan()

if __name__ == "__main__":
    main()