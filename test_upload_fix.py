#!/usr/bin/env python3
"""
Test script to verify the upload fix handles list responses correctly
"""

def test_result_handling():
    """Test different result formats that RAGFlow might return"""

    print("🧪 Testing upload result handling...\n")

    # Test data - simulating different RAGFlow API responses
    test_cases = [
        {
            "name": "List response (actual RAGFlow format)",
            "result": [{'chunk_method': 'naive', 'created_by': '654988b4937a11f099bebeda909148e4', 'dataset_id': 'fe55769e937a11f095e2beda909148e4', 'id': 'f85fb466938411f0976ebeda909148e4', 'location': 'sample.md', 'name': 'sample.md', 'parser_config': {'pages': [[1, 1000000]]}, 'run': 'UNSTART', 'size': 4060, 'suffix': 'md', 'thumbnail': '', 'type': 'doc'}]
        },
        {
            "name": "Dictionary response",
            "result": {'id': 'doc_12345', 'name': 'test.md', 'status': 'uploading'}
        },
        {
            "name": "Empty list",
            "result": []
        },
        {
            "name": "None result",
            "result": None
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. Testing: {test_case['name']}")
        result = test_case['result']

        # This is the fixed logic from the upload scripts
        if result:
            # Handle the case where result is a list (which RAGFlow returns)
            if isinstance(result, list) and len(result) > 0:
                file_obj = result[0]  # Return the first uploaded file
                print(f"   ✅ Extracted from list: {file_obj.get('id', 'No ID')}")
            elif isinstance(result, dict):
                print(f"   ✅ Dictionary format: {result.get('id', 'No ID')}")
            else:
                print(f"   ⚠️ Unexpected result format: {type(result)}")
        else:
            print(f"   ❌ No result or empty result")
        print()

    print("🎉 All test cases completed!")

if __name__ == "__main__":
    test_result_handling()