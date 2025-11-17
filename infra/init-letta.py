#!/usr/bin/env python3
"""
Initialize Letta server with OpenAI provider configuration.
This script should be run after the Letta server starts to ensure
OpenAI models are available for agent creation.
"""
import os
import sys
import time
import requests
from letta_client import Letta


def wait_for_letta(base_url: str, max_retries: int = 30, delay: int = 2) -> bool:
    """Wait for Letta server to be ready."""
    print(f"Waiting for Letta server at {base_url}...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/v1/health", timeout=5)
            if response.status_code in [200, 307]:
                print(f"✓ Letta server is ready")
                return True
        except requests.exceptions.RequestException:
            pass

        if i < max_retries - 1:
            print(f"  Retry {i+1}/{max_retries}...")
            time.sleep(delay)

    print(f"✗ Letta server not available after {max_retries} retries")
    return False


def get_openai_models(client: Letta) -> list:
    """Get list of models that use OpenAI provider."""
    try:
        models = client.models.list()
        openai_models = [
            m for m in models
            if hasattr(m, 'provider_name') and m.provider_name == 'openai' and m.provider_type == 'openai'
        ]
        return openai_models
    except Exception as e:
        print(f"Error listing models: {e}")
        return []


def configure_openai_provider(base_url: str, api_key: str) -> bool:
    """
    Configure OpenAI provider in Letta by adding models through the API.
    Since Letta doesn't expose a direct provider configuration endpoint,
    we use the Letta Python client's internal provider setup.
    """
    try:
        client = Letta(base_url=base_url)

        # Check if OpenAI models already exist
        existing_openai = get_openai_models(client)
        if existing_openai:
            print(f"✓ OpenAI provider already configured with {len(existing_openai)} models")
            for model in existing_openai:
                print(f"  - {model.handle}")
            return True

        print("OpenAI provider not found, attempting to configure...")

        # Try to use letta-client's provider setup
        # The Letta server auto-detects providers from environment variables
        # We just need to trigger the detection

        # List models to trigger provider auto-detection
        models = client.models.list()
        print(f"Found {len(models)} models after refresh")

        # Check again for OpenAI models
        openai_models = get_openai_models(client)
        if openai_models:
            print(f"✓ OpenAI provider configured successfully with {len(openai_models)} models")
            for model in openai_models:
                print(f"  - {model.handle}")
            return True
        else:
            print("⚠ OpenAI provider not auto-configured. Letta may need manual configuration.")
            print("  Available models:")
            for model in models:
                print(f"  - {model.handle} (provider: {getattr(model, 'provider_name', 'N/A')})")
            return False

    except Exception as e:
        print(f"✗ Error configuring OpenAI provider: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("✗ OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    print("=" * 60)
    print("Letta OpenAI Provider Initialization")
    print("=" * 60)

    # Wait for Letta to be ready
    if not wait_for_letta(base_url):
        sys.exit(1)

    # Configure OpenAI provider
    if configure_openai_provider(base_url, api_key):
        print("\n✓ Letta initialization complete")
        sys.exit(0)
    else:
        print("\n⚠ Letta initialization completed with warnings")
        print("  The system will use default Letta models")
        # Don't fail - allow the system to start with letta-free
        sys.exit(0)


if __name__ == "__main__":
    main()
