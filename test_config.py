"""
Test the configuration and verify proxy setup.
"""
from dotenv import load_dotenv
import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except AttributeError:
        pass

# Load environment variables
load_dotenv()

def test_config():
    """Test if required configuration is present."""
    print("=" * 60)
    print("Configuration Test")
    print("=" * 60)
    
    # Test OpenAI API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        masked_key = api_key[:20] + "..." if len(api_key) > 20 else api_key
        print(f"✅ OPENAI_API_KEY: {masked_key}")
    else:
        print("❌ OPENAI_API_KEY: Not set!")
        return False
    
    # Test Proxy URL
    proxy_url = os.environ.get("PROXY_URL")
    if proxy_url:
        # Mask sensitive parts
        if "@" in proxy_url:
            parts = proxy_url.split("@")
            masked = parts[0].split(":")
            if len(masked) >= 2:
                masked_password = "****"
                masked_url = f"{masked[0]}://****:{masked_password}@{parts[1]}"
            else:
                masked_url = proxy_url
        else:
            masked_url = proxy_url
        print(f"✅ PROXY_URL: {masked_url}")
    else:
        print("⚠️  PROXY_URL: Not set (optional but recommended)")
    
    # Test League Filtering
    league_tier = os.environ.get("LEAGUE_TIER", "1")
    print(f"📊 LEAGUE_TIER: {league_tier}")
    
    selected_leagues = os.environ.get("SELECTED_LEAGUES", "")
    if selected_leagues:
        print(f"📋 SELECTED_LEAGUES: {selected_leagues}")
    else:
        print("📋 SELECTED_LEAGUES: Not set (will scrape all leagues in tier)")
    
    # Test Base URL
    base_url = os.environ.get("SPORTS_BASE_URL", "")
    if base_url:
        print(f"🌐 SPORTS_BASE_URL: {base_url}")
    else:
        print("⚠️  SPORTS_BASE_URL: Not set")
        print("   Individual league URLs must be set instead")
    
    # Count configured league URLs
    from web_scrapping import EUROPEAN_LEAGUES
    configured_count = 0
    for league_key in EUROPEAN_LEAGUES.keys():
        env_var = league_key.upper().replace(" ", "_").replace(".", "").replace("-", "_")
        if os.environ.get(f"{env_var}_URL"):
            configured_count += 1
    
    if base_url or configured_count > 0:
        if base_url:
            print(f"📊 Using SPORTS_BASE_URL pattern for all {len(EUROPEAN_LEAGUES)} leagues")
        else:
            print(f"📊 Configured individual URLs for {configured_count} leagues")
    else:
        print("❌ No league URLs configured!")
        print("   Set SPORTS_BASE_URL or individual league URLs in .env file")
        return False
    
    print("=" * 60)
    print("✅ Configuration looks good!")
    print("=" * 60)
    print("\nAvailable leagues:")
    print(f"  Total: {len(EUROPEAN_LEAGUES)}")
    
    # Group by tier
    tiers = {}
    for league_key, league_info in EUROPEAN_LEAGUES.items():
        tier = league_info.get("tier", 1)
        if tier not in tiers:
            tiers[tier] = []
        tiers[tier].append(league_key)
    
    for tier in sorted(tiers.keys()):
        print(f"  Tier {tier}: {len(tiers[tier])}")
    
    return True

if __name__ == "__main__":
    success = test_config()
    if success:
        print("\n🚀 Ready to run: python web_scrapping.py")
    else:
        print("\n⚠️  Please configure your .env file first")

