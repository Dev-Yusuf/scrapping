"""
Quick test script to verify Gemini configuration with a single league.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the scraper function
from web_scrapping import scrape_league_table, ScraperConfig

async def test_single_league():
    """Test scraping a single league table with Gemini."""
    print("=" * 70)
    print("Testing Gemini with Premier League")
    print("=" * 70)
    
    # Configuration
    config = ScraperConfig(
        max_depth=1,
        max_pages=3,  # Reduced for testing
        headless=True,
        use_proxy=False,  # Disabled proxy for testing due to tunnel issues
        llm_provider="gemini/gemini-pro",
        output_dir="output"
    )
    
    # Test with Premier League
    url = "https://www.fctables.com/premier-league"
    
    print(f"\nTesting URL: {url}")
    print(f"LLM Provider: {config.llm_provider}")
    print(f"Proxy: Enabled\n")
    
    result = await scrape_league_table(
        start_url=url,
        league_name="Premier League",
        config=config,
        retries=2,  # Reduced for testing
        save_to_file=True
    )
    
    if result:
        print("\n" + "=" * 70)
        print("SUCCESS! Data extracted:")
        print("=" * 70)
        print(f"League: {result.get('sport', 'N/A')} - {result.get('league', 'N/A')}")
        print(f"Teams found: {len(result.get('standings', []))}")
        if result.get('standings'):
            top_team = result['standings'][0]
            print(f"\nTop Team: {top_team.get('team_name', 'N/A')} - {top_team.get('points', 'N/A')} points")
    else:
        print("\n" + "=" * 70)
        print("FAILED: Could not extract data")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_single_league())

