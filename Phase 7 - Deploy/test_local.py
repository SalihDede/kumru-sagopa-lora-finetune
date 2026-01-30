"""
Local test script for the RunPod handler
Run this before deploying to verify the handler works correctly
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from handler import handler, load_model

def test_simple_prompt():
    """Test with a simple prompt"""
    print("\n" + "="*50)
    print("Test 1: Simple Prompt")
    print("="*50)

    event = {
        "input": {
            "prompt": "Merhaba, nasılsın?",
            "max_new_tokens": 100,
            "temperature": 0.7
        }
    }

    result = handler(event)
    print(f"Input: {event['input']['prompt']}")
    print(f"Output: {result.get('output', result.get('error'))}")
    return result

def test_chat_format():
    """Test with chat message format"""
    print("\n" + "="*50)
    print("Test 2: Chat Format")
    print("="*50)

    event = {
        "input": {
            "messages": [
                {"role": "user", "content": "Sagopa Kajmer kimdir?"}
            ],
            "max_new_tokens": 200,
            "temperature": 0.7
        }
    }

    result = handler(event)
    print(f"Input: {event['input']['messages']}")
    print(f"Output: {result.get('output', result.get('error'))}")
    return result

def test_multi_turn_conversation():
    """Test with multi-turn conversation"""
    print("\n" + "="*50)
    print("Test 3: Multi-turn Conversation")
    print("="*50)

    event = {
        "input": {
            "messages": [
                {"role": "user", "content": "Bana bir şarkı sözü yazar mısın?"},
                {"role": "assistant", "content": "Tabii ki, hangi konuda olsun?"},
                {"role": "user", "content": "Hayat ve umut hakkında olsun."}
            ],
            "max_new_tokens": 300,
            "temperature": 0.8,
            "top_p": 0.9
        }
    }

    result = handler(event)
    print(f"Conversation: {event['input']['messages']}")
    print(f"Output: {result.get('output', result.get('error'))}")
    return result

def test_error_handling():
    """Test error handling with invalid input"""
    print("\n" + "="*50)
    print("Test 4: Error Handling")
    print("="*50)

    event = {
        "input": {}  # No prompt or messages
    }

    result = handler(event)
    print(f"Input: Empty")
    print(f"Output: {result}")
    return result

if __name__ == "__main__":
    print("="*50)
    print("RunPod Handler Local Test")
    print("="*50)

    # Load model first
    print("\nLoading model...")
    load_model()

    # Run tests
    test_simple_prompt()
    test_chat_format()
    test_multi_turn_conversation()
    test_error_handling()

    print("\n" + "="*50)
    print("All tests completed!")
    print("="*50)
