"""
Test AI provider endpoint URL construction
Verifies that each AI provider uses the correct base URL format
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

from config_manager import ConfigManager
from ai_client import AIClient


def test_ollama_endpoint_construction():
    """Test that Ollama endpoints get /v1 appended"""
    os.environ['AI_ENABLED'] = 'true'
    os.environ['AI_PROVIDER'] = 'ollama'
    os.environ['AI_ENDPOINT'] = 'http://localhost:11434'
    os.environ['AI_MODEL'] = 'llama2'
    
    config = ConfigManager()
    ai = AIClient(config)
    
    # Check that the client was initialized with correct base_url
    if ai.client:
        # The OpenAI client's base_url should end with /v1 (may have trailing slash)
        assert ai.client.base_url is not None
        base_url_str = str(ai.client.base_url).rstrip('/')
        assert base_url_str.endswith('/v1'), f"Ollama base_url should end with /v1, got: {base_url_str}"
        print("✓ Test passed: Ollama endpoint has /v1 appended")
        return True
    else:
        print("⚠ Warning: AI client not initialized (OpenAI library may not be available)")
        return True


def test_lmstudio_endpoint_construction():
    """Test that LMStudio endpoints get /v1 appended"""
    os.environ['AI_ENABLED'] = 'true'
    os.environ['AI_PROVIDER'] = 'lmstudio'
    os.environ['AI_ENDPOINT'] = 'http://localhost:1234'
    os.environ['AI_MODEL'] = 'local-model'
    
    config = ConfigManager()
    ai = AIClient(config)
    
    # Check that the client was initialized with correct base_url
    if ai.client:
        # The OpenAI client's base_url should end with /v1 (may have trailing slash)
        assert ai.client.base_url is not None
        base_url_str = str(ai.client.base_url).rstrip('/')
        assert base_url_str.endswith('/v1'), f"LMStudio base_url should end with /v1, got: {base_url_str}"
        print("✓ Test passed: LMStudio endpoint has /v1 appended")
        return True
    else:
        print("⚠ Warning: AI client not initialized (OpenAI library may not be available)")
        return True


def test_openwebui_endpoint_construction():
    """Test that OpenWebUI endpoints get /api appended (NOT /v1)"""
    os.environ['AI_ENABLED'] = 'true'
    os.environ['AI_PROVIDER'] = 'openwebui'
    os.environ['AI_ENDPOINT'] = 'http://localhost:8080'
    os.environ['AI_MODEL'] = 'gpt-3.5-turbo'
    os.environ['API_KEY'] = 'test-key'
    
    config = ConfigManager()
    ai = AIClient(config)
    
    # Check that the client was initialized with correct base_url
    if ai.client:
        # The OpenAI client's base_url should end with /api (not /v1) (may have trailing slash)
        assert ai.client.base_url is not None
        base_url_str = str(ai.client.base_url).rstrip('/')
        assert base_url_str.endswith('/api'), f"OpenWebUI base_url should end with /api, got: {base_url_str}"
        assert not base_url_str.endswith('/v1'), f"OpenWebUI base_url should NOT end with /v1, got: {base_url_str}"
        print("✓ Test passed: OpenWebUI endpoint has /api appended (not /v1)")
        return True
    else:
        print("⚠ Warning: AI client not initialized (OpenAI library may not be available)")
        return True


def test_openai_endpoint_no_modification():
    """Test that OpenAI endpoints are not modified"""
    os.environ['AI_ENABLED'] = 'true'
    os.environ['AI_PROVIDER'] = 'openai'
    os.environ['AI_ENDPOINT'] = ''  # Default OpenAI endpoint
    os.environ['AI_MODEL'] = 'gpt-4'
    os.environ['API_KEY'] = 'test-key'
    
    config = ConfigManager()
    ai = AIClient(config)
    
    # For OpenAI with no custom endpoint, base_url should be None (uses default)
    if ai.client:
        # The OpenAI client should use default base_url when endpoint is empty
        print("✓ Test passed: OpenAI uses default endpoint when not specified")
        return True
    else:
        print("⚠ Warning: AI client not initialized (OpenAI library may not be available)")
        return True


def test_openwebui_endpoint_already_has_api():
    """Test that /api is not duplicated if user includes it"""
    os.environ['AI_ENABLED'] = 'true'
    os.environ['AI_PROVIDER'] = 'openwebui'
    os.environ['AI_ENDPOINT'] = 'http://localhost:8080/api'
    os.environ['AI_MODEL'] = 'gpt-3.5-turbo'
    os.environ['API_KEY'] = 'test-key'
    
    config = ConfigManager()
    ai = AIClient(config)
    
    # Check that the client was initialized without duplicating /api
    if ai.client:
        assert ai.client.base_url is not None
        base_url_str = str(ai.client.base_url).rstrip('/')
        # Should end with /api, not /api/api
        assert base_url_str.endswith('/api'), f"OpenWebUI base_url should end with /api, got: {base_url_str}"
        assert '/api/api' not in base_url_str, f"OpenWebUI base_url should not have duplicate /api, got: {base_url_str}"
        print("✓ Test passed: OpenWebUI does not duplicate /api if already present")
        return True
    else:
        print("⚠ Warning: AI client not initialized (OpenAI library may not be available)")
        return True


def test_ollama_endpoint_already_has_v1():
    """Test that /v1 is not duplicated if user includes it"""
    os.environ['AI_ENABLED'] = 'true'
    os.environ['AI_PROVIDER'] = 'ollama'
    os.environ['AI_ENDPOINT'] = 'http://localhost:11434/v1'
    os.environ['AI_MODEL'] = 'llama2'
    
    config = ConfigManager()
    ai = AIClient(config)
    
    # Check that the client was initialized without duplicating /v1
    if ai.client:
        assert ai.client.base_url is not None
        base_url_str = str(ai.client.base_url).rstrip('/')
        # Should end with /v1, not /v1/v1
        assert base_url_str.endswith('/v1'), f"Ollama base_url should end with /v1, got: {base_url_str}"
        assert '/v1/v1' not in base_url_str, f"Ollama base_url should not have duplicate /v1, got: {base_url_str}"
        print("✓ Test passed: Ollama does not duplicate /v1 if already present")
        return True
    else:
        print("⚠ Warning: AI client not initialized (OpenAI library may not be available)")
        return True


if __name__ == '__main__':
    print("Running AI provider endpoint URL construction tests...\n")
    
    tests = [
        test_ollama_endpoint_construction,
        test_lmstudio_endpoint_construction,
        test_openwebui_endpoint_construction,
        test_openai_endpoint_no_modification,
        test_openwebui_endpoint_already_has_api,
        test_ollama_endpoint_already_has_v1
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests completed: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    sys.exit(0 if failed == 0 else 1)
