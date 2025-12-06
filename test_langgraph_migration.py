#!/usr/bin/env python3
"""
Quick test script for LangGraph migration

Tests the hulatang workflow with router hot-plugging.
"""

import sys
from pathlib import Path

# Add mas_aider to path
sys.path.insert(0, str(Path(__file__).parent))

from mas_aider.main import MasAiderSession

def test_langgraph_hulatang():
    """Test hulatang workflow with LangGraph engine and router"""
    
    print("=" * 80)
    print("LangGraph Migration Test - Hulatang Workflow")
    print("=" * 80)
    
    # Create session
    with MasAiderSession() as session:
        try:
            # Run hulatang workflow
            result = session.run_workflow("hulatang")
            
            # Show results
            print("\n" + "=" * 80)
            print("TEST RESULTS")
            print("=" * 80)
            print(f"Success: {result.success}")
            print(f"Total turns: {result.total_turns}")
            print(f"Agents used: {', '.join(result.agents_used)}")
            
            if result.error_message:
                print(f"\nError: {result.error_message}")
            
            return result.success
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_langgraph_hulatang()
    sys.exit(0 if success else 1)
