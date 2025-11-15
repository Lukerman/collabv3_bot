"""
Test Perplexity API authentication
"""
import asyncio
import aiohttp
from config import config

async def test_auth():
    """Test if API key is valid"""
    
    headers = {
        "Authorization": f"Bearer {config.PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Try with a simple model name from latest docs
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }
    
    print(f"Testing Perplexity API Authentication...")
    print(f"API Key: {config.PERPLEXITY_API_KEY[:15]}...{config.PERPLEXITY_API_KEY[-5:]}")
    print(f"API URL: {config.PERPLEXITY_API_URL}\n")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                config.PERPLEXITY_API_URL,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                status = response.status
                text = await response.text()
                
                print(f"Status Code: {status}")
                print(f"Response: {text}\n")
                
                if status == 401:
                    print("❌ Authentication Failed!")
                    print("Your API key is invalid or expired.")
                    print("\nPlease:")
                    print("1. Check your API key at https://www.perplexity.ai/settings/api")
                    print("2. Make sure you have API credits")
                    print("3. Verify the key is active")
                elif status == 400:
                    print("⚠️  Bad Request - Check model name")
                    print("The API key might be valid but the model name is wrong")
                elif status == 200:
                    print("✅ API key is valid and working!")
                else:
                    print(f"❓ Unexpected status: {status}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth())