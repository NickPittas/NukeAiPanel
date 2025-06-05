#!/usr/bin/env python
"""
Run all model mapping tests to verify fixes.

This script runs a series of tests to verify that the model mapping fixes
are working correctly for all providers.
"""

import asyncio
import sys
import os
import logging
import subprocess
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("model_mapping_tests")

# Test cases for each provider
TEST_CASES = {
    "openrouter": [
        "google/gemini-pro",
        "gpt-3.5-turbo",
        "gpt-4",
        "claude-3-opus",
        "mistral-small"
    ],
    "ollama": [
        "llama2:70b",
        "mistral",
        "mixtral",
        "gemini-pro",
        "gpt-4"
    ]
}

def run_test_script():
    """Run the main test script."""
    logger.info("Running tests/test_model_mapping_fixes.py")
    
    try:
        result = subprocess.run(
            [sys.executable, "tests/test_model_mapping_fixes.py"],
            capture_output=True,
            text=True,
            check=False
        )
        
        logger.info("Test script output:")
        for line in result.stdout.splitlines():
            logger.info(f"  {line}")
            
        if result.stderr:
            logger.error("Test script errors:")
            for line in result.stderr.splitlines():
                logger.error(f"  {line}")
                
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running test script: {e}")
        return False

async def run_verification_tests():
    """Run verification tests for each provider and model."""
    logger.info("Running verification tests")
    
    results = []
    
    for provider, models in TEST_CASES.items():
        logger.info(f"Testing provider: {provider}")
        
        for model in models:
            logger.info(f"Testing model: {model}")
            
            try:
                result = subprocess.run(
                    [
                        sys.executable, 
                        "verify_model_mapping_fixes.py",
                        "--provider", provider,
                        "--model", model
                    ],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                success = result.returncode == 0
                results.append((provider, model, success))
                
                if success:
                    logger.info(f"✅ {provider}/{model}: Verification successful")
                else:
                    logger.error(f"❌ {provider}/{model}: Verification failed")
                    logger.error(f"Error output: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error running verification for {provider}/{model}: {e}")
                results.append((provider, model, False))
    
    return results

def generate_report(results: List[Tuple[str, str, bool]]):
    """Generate a report of test results."""
    logger.info("Generating test report")
    
    total_tests = len(results)
    successful_tests = sum(1 for _, _, success in results if success)
    
    print("\n" + "="*60)
    print(f"MODEL MAPPING TESTS REPORT")
    print("="*60)
    print(f"Total tests: {total_tests}")
    print(f"Successful tests: {successful_tests}")
    print(f"Failed tests: {total_tests - successful_tests}")
    print(f"Success rate: {successful_tests/total_tests*100:.1f}%")
    print("-"*60)
    
    # Group by provider
    provider_results = {}
    for provider, model, success in results:
        if provider not in provider_results:
            provider_results[provider] = []
        provider_results[provider].append((model, success))
    
    # Print results by provider
    for provider, provider_tests in provider_results.items():
        successful = sum(1 for _, success in provider_tests if success)
        total = len(provider_tests)
        print(f"\n{provider.upper()} ({successful}/{total} successful)")
        print("-"*60)
        
        for model, success in provider_tests:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {model}")
    
    print("\n" + "="*60)
    
    return successful_tests == total_tests

async def main():
    """Main function."""
    logger.info("Starting model mapping tests")
    
    # Run the main test script
    main_test_success = run_test_script()
    
    # Run verification tests
    verification_results = await run_verification_tests()
    
    # Generate report
    all_verification_passed = generate_report(verification_results)
    
    # Overall success
    overall_success = main_test_success and all_verification_passed
    
    if overall_success:
        logger.info("All tests passed successfully!")
        return 0
    else:
        logger.error("Some tests failed. See report for details.")
        return 1

if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)