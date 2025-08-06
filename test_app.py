#!/usr/bin/env python3
"""
Test script to run the newsletter app in test mode without LLM calls.
This will use fallback values instead of making API calls.
"""

import os
import subprocess
import sys

def main():
    print("🧪 Starting Newsletter Generator in TEST MODE")
    print("📝 This will use fallback values instead of LLM API calls")
    print("=" * 50)
    
    # Set environment variable for test mode
    env = os.environ.copy()
    env['TEST_MODE'] = 'true'
    
    try:
        # Run streamlit with test mode enabled
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'app.py'
        ], env=env)
    except KeyboardInterrupt:
        print("\n🛑 Test mode stopped")

if __name__ == "__main__":
    main()