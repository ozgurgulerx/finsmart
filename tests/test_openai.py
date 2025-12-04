#!/usr/bin/env python3
"""
Quick test script to verify OpenAI API access with gpt-5-mini reasoning.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def test_openai_reasoning():
    """Test OpenAI API with gpt-5-mini reasoning model."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    print(f"API Key: {api_key[:10]}...{api_key[-4:] if api_key else 'NOT SET'}")
    print("-" * 40)
    
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set in .env file")
        return False
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Test with gpt-5-mini reasoning
        result = client.responses.create(
            model="gpt-5-mini",
            input="If 2+2 = 3 and 3+3 = 5 then 4+4 = ?",
            reasoning={"effort": "low"},
            text={"verbosity": "low"},
        )
        
        print(f"✓ Response: {result.output_text}")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_openai_reasoning()
    print("-" * 40)
    print("Status:", "OK" if success else "FAILED")
