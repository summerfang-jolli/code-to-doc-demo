#!/usr/bin/env python3
"""
Quick test script to verify database utilities work correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import (
    get_project_manager, get_code_file_manager,
    get_code_element_manager, get_documentation_manager
)

def test_database_utilities():
    """Test basic database utility functions."""
    print("Testing database utilities...")

    # Test project manager
    pm = get_project_manager()
    projects = pm.list_projects()
    print(f"✓ Found {len(projects)} projects")

    if projects:
        project = projects[0]
        print(f"✓ Sample project: {project.name}")

        # Test file manager
        fm = get_code_file_manager()
        files = fm.get_files_for_project(project.id)
        print(f"✓ Found {len(files)} files for project")

        if files:
            file = files[0]
            print(f"✓ Sample file: {file.file_path}")

            # Test element manager
            em = get_code_element_manager()
            elements = em.get_elements_for_file(file.id)
            print(f"✓ Found {len(elements)} code elements in file")

            if elements:
                element = elements[0]
                print(f"✓ Sample element: {element.name} ({element.element_type})")

    print("✓ Database utilities test completed successfully!")

if __name__ == "__main__":
    test_database_utilities()