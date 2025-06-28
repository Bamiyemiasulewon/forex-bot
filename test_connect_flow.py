#!/usr/bin/env python3
"""
Test script for the multi-step MT5 connection flow.
This script simulates the user interaction with the /connect command.
"""

import asyncio
import logging
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_session_manager():
    """Test the session manager functionality."""
    from app.telegram.bot import session_manager
    import time
    
    logger.info("🧪 Testing Session Manager...")
    
    # Test session creation
    user_id = 12345
    session_manager.create_session(user_id, "mt5_connect")
    session = session_manager.get_session(user_id)
    assert session is not None, "Session should be created"
    assert session['type'] == "mt5_connect", "Session type should be correct"
    logger.info("✅ Session creation test passed")
    
    # Test session update
    session_manager.update_session(user_id, 'login', '12345678')
    session = session_manager.get_session(user_id)
    assert session['data']['login'] == '12345678', "Session data should be updated"
    logger.info("✅ Session update test passed")
    
    # Test session timeout (simulate)
    session_manager.sessions[user_id]['created_at'] = time.time() - 130  # 2+ minutes ago
    session = session_manager.get_session(user_id)
    assert session is None, "Expired session should be cleaned up"
    logger.info("✅ Session timeout test passed")
    
    # Test session cleanup
    session_manager.create_session(user_id, "mt5_connect")
    session_manager.clear_session(user_id)
    session = session_manager.get_session(user_id)
    assert session is None, "Session should be cleared"
    logger.info("✅ Session cleanup test passed")
    
    logger.info("🎉 All session manager tests passed!")

def test_connect_flow():
    """Test the multi-step connect flow logic."""
    from app.telegram.bot import session_manager
    
    logger.info("🧪 Testing Connect Flow Logic...")
    
    user_id = 12345
    
    # Simulate step 1: Login
    session_manager.create_session(user_id, "mt5_connect")
    session_manager.update_session(user_id, 'login', '12345678')
    session = session_manager.get_session(user_id)
    assert 'login' in session['data'], "Login should be stored"
    assert session['data']['login'] == '12345678', "Login should be correct"
    logger.info("✅ Step 1 (Login) test passed")
    
    # Simulate step 2: Password
    session_manager.update_session(user_id, 'password', 'mypassword')
    session = session_manager.get_session(user_id)
    assert 'password' in session['data'], "Password should be stored"
    assert session['data']['password'] == 'mypassword', "Password should be correct"
    logger.info("✅ Step 2 (Password) test passed")
    
    # Simulate step 3: Server
    session_manager.update_session(user_id, 'server', 'MetaQuotes-Demo')
    session = session_manager.get_session(user_id)
    assert 'server' in session['data'], "Server should be stored"
    assert session['data']['server'] == 'MetaQuotes-Demo', "Server should be correct"
    logger.info("✅ Step 3 (Server) test passed")
    
    # Verify all data is collected
    data = session['data']
    assert len(data) == 3, "All three pieces of data should be collected"
    assert data['login'] == '12345678', "Login should be preserved"
    assert data['password'] == 'mypassword', "Password should be preserved"
    assert data['server'] == 'MetaQuotes-Demo', "Server should be preserved"
    logger.info("✅ Complete data collection test passed")
    
    # Clean up
    session_manager.clear_session(user_id)
    logger.info("🎉 All connect flow tests passed!")

def main():
    """Run all tests."""
    logger.info("🚀 Starting Multi-step Connect Flow Tests...")
    
    try:
        test_session_manager()
        test_connect_flow()
        
        logger.info("\n📊 Test Results:")
        logger.info("✅ Session Manager: PASS")
        logger.info("✅ Connect Flow: PASS")
        logger.info("🎉 All tests passed! The multi-step connect functionality is working correctly.")
        
        logger.info("\n💡 How to use the new /connect command:")
        logger.info("1. Type /connect to start the process")
        logger.info("2. Enter your MT5 login ID when prompted")
        logger.info("3. Enter your password when prompted")
        logger.info("4. Enter your server name when prompted")
        logger.info("5. The bot will attempt to connect and show the result")
        logger.info("6. Use /cancel at any time to stop the process")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 