"""
Local test script for RunPod handler
Run this to test the handler locally before deploying
"""

import sys
import os

# Mock runpod module for local testing
class MockRunPod:
    class serverless:
        @staticmethod
        def start(config):
            print("Mock RunPod serverless started")
            print("Testing handler function...")

            handler = config['handler']

            # Test case 1: Simple prompt
            test_job = {
                'input': {
                    'prompt': 'Merhaba Sagopa, nasılsın?',
                    'max_new_tokens': 50,
                    'temperature': 0.7
                }
            }

            print("\n=== Test Case 1: Simple Prompt ===")
            print(f"Input: {test_job}")
            result = handler(test_job)
            print(f"Output: {result}")

            # Test case 2: With conversation history
            test_job_2 = {
                'input': {
                    'prompt': 'Şarkılarından bahset',
                    'messages': [
                        {'role': 'user', 'content': 'Merhaba'},
                        {'role': 'assistant', 'content': 'Selam'}
                    ],
                    'max_new_tokens': 50,
                    'temperature': 0.7
                }
            }

            print("\n=== Test Case 2: With Conversation History ===")
            print(f"Input: {test_job_2}")
            result_2 = handler(test_job_2)
            print(f"Output: {result_2}")

            # Test case 3: Empty prompt (should fail)
            test_job_3 = {
                'input': {
                    'max_new_tokens': 50
                }
            }

            print("\n=== Test Case 3: Empty Prompt (Expected to Fail) ===")
            print(f"Input: {test_job_3}")
            result_3 = handler(test_job_3)
            print(f"Output: {result_3}")

sys.modules['runpod'] = MockRunPod()

# Now import the handler
print("Importing handler...")
print("=" * 50)

# Update model path for local testing
os.environ['MODEL_PATH'] = './SagoChatBOTAPI/kumru-sagopa-merged'

try:
    from handler import handler, load_model
    print("Handler imported successfully!")
    print("\nAttempting to load model...")
    print("Note: This requires the model to be in ./SagoChatBOTAPI/kumru-sagopa-merged")
    print("=" * 50)

    # Try to load the model
    model, tokenizer = load_model()
    print("\nModel loaded successfully!")

    # Run tests
    MockRunPod.serverless.start({'handler': handler})

except FileNotFoundError as e:
    print(f"\n⚠️  Model not found: {e}")
    print("Please ensure the model is in ./SagoChatBOTAPI/kumru-sagopa-merged")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
