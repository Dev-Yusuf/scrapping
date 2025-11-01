"""
AI-Powered Sports Odds Web Scraper

This module uses Crawl4AI with GPT-4o to intelligently extract sports betting odds
from websites. It supports deep crawling, proxy configuration, and structured data extraction.
"""

from dotenv import load_dotenv
load_dotenv()
import asyncio
import os
import json
import logging
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

# Fix Windows console encoding issues
if sys.platform == 'win32':
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except AttributeError:
        # Already configured or not needed
        pass

from pydantic import BaseModel, Field, validator
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import (
    BrowserConfig,
    CrawlerRunConfig,
    LLMConfig
)
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.extraction_strategy import LLMExtractionStrategy

# Configure logging with UTF-8 encoding
log_file_handler = logging.FileHandler('scraper.log', encoding='utf-8')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        log_file_handler,
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --- 1. Define Your "Smart" Data Schema for League Tables ---
# This Pydantic model tells the AI *exactly* what data to find.
# This is the "smart" part. It won't break if a CSS class changes.

class LeagueTableEntry(BaseModel):
    """Represents a single team's position in the league table."""
    position: int = Field(description="The team's current position in the table (1, 2, 3, etc.)")
    team_name: str = Field(description="The name of the team")
    matches_played: int = Field(description="Number of matches played (MP)", alias="mp")
    wins: int = Field(description="Number of wins (W)")
    draws: int = Field(description="Number of draws (D)")
    losses: int = Field(description="Number of losses (L)")
    goals_for: int = Field(description="Goals scored (GF)", alias="gf")
    goals_against: int = Field(description="Goals conceded (GA)", alias="ga")
    goal_difference: int = Field(description="Goal difference (GD)", alias="gd")
    points: int = Field(description="Total points (Pts)")
    
    class Config:
        populate_by_name = True
    
    @validator('position')
    def validate_position(cls, v):
        """Position should be a positive integer."""
        if v < 1:
            raise ValueError("Position must be at least 1")
        return v
    
    @validator('points')
    def validate_points(cls, v):
        """Points should be non-negative."""
        if v < 0:
            raise ValueError("Points cannot be negative")
        return v
    
    @validator('team_name')
    def validate_team_name(cls, v):
        """Team name should not be empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Team name cannot be empty")
        return v.strip()

class LeagueTableData(BaseModel):
    """Container for league table data extracted from a page."""
    sport: str = Field(description="The name of the sport, e.g., 'Football'")
    league: str = Field(description="The name of the league, e.g., 'English Premier League'")
    season: Optional[str] = Field(description="The season, e.g., '2024-25'", default=None)
    standings: List[LeagueTableEntry] = Field(description="The complete league table with all teams ordered by position")
    
    def get_team_count(self) -> int:
        """Returns the number of teams in the league."""
        return len(self.standings)
    
    def get_top_team(self) -> Optional[LeagueTableEntry]:
        """Returns the team at the top of the table."""
        return self.standings[0] if self.standings else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the model to a dictionary."""
        return self.model_dump()


# --- 2. Configuration Class ---
class ScraperConfig:
    """Configuration class for the scraper with sensible defaults."""
    
    def __init__(
        self,
        max_depth: int = 2,
        max_pages: int = 10,
        headless: bool = True,
        use_proxy: bool = True,
        user_agent: Optional[str] = None,
        llm_provider: str = "openai/gpt-4o",
        output_dir: str = "output"
    ):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.headless = headless
        self.use_proxy = use_proxy
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.llm_provider = llm_provider
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)


# --- 3. Enhanced Scraping Function ---
async def scrape_league_table(
    start_url: str,
    league_name: str,
    config: Optional[ScraperConfig] = None,
    retries: int = 3,
    save_to_file: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Scrape a website for league table/standings data using AI-powered extraction.
    
    Args:
        start_url: The URL to start crawling from
        league_name: The name of the league (for logging and instruction)
        config: ScraperConfig object with custom settings
        retries: Number of retry attempts if scraping fails
        save_to_file: Whether to save the extracted data to a JSON file
        
    Returns:
        Dictionary containing extracted league table data or None if failed
    """
    config = config or ScraperConfig()
    
    logger.info(f"Starting league table scrape for: {league_name}")
    logger.info(f"URL: {start_url}")
    logger.info(f"Configuration: depth={config.max_depth}, pages={config.max_pages}")
    
    # Validate environment variables
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set!")
        return None
    
    # Get proxy URL if enabled
    proxy_url = None
    if config.use_proxy:
        proxy_url = os.environ.get("PROXY_URL")
        if proxy_url:
            logger.info("Using proxy for requests")
    
    # Enhanced instruction for league table extraction
    extraction_instruction = f"""
    Extract the complete current league table/standings for {league_name}.
    
    The table should include:
    - Position (1st, 2nd, 3rd, etc.)
    - Team name
    - Matches played (MP)
    - Wins (W)
    - Draws (D)
    - Losses (L)
    - Goals for (GF)
    - Goals against (GA)
    - Goal difference (GD)
    - Points (Pts)
    
    Extract ALL teams in the league table, typically 18-20 teams for top European leagues.
    Ensure the standings are ordered by position (1st place first, etc.).
    Be thorough and accurate. If you see a league table on the page, extract it completely.
    """
    
    for attempt in range(retries):
        try:
            # Browser Configuration
            browser_config = BrowserConfig(
                headless=config.headless,
                proxy=proxy_url,
                user_agent=config.user_agent
            )

            # Deep Crawl Strategy - reduced depth since we're looking for a specific table
            deep_crawl_strategy = BFSDeepCrawlStrategy(
                max_depth=config.max_depth,
                max_pages=config.max_pages,
                include_external=False
            )

            # LLM Extraction Strategy for League Tables
            extraction_strategy = LLMExtractionStrategy(
                llm_config=LLMConfig(
                    provider=config.llm_provider,
                    api_token=api_key
                ),
                schema=LeagueTableData.model_json_schema(),
                extraction_type="schema",
                instruction=extraction_instruction
            )

            # Combined Run Configuration
            run_config = CrawlerRunConfig(
                deep_crawl_strategy=deep_crawl_strategy,
                extraction_strategy=extraction_strategy,
                exclude_external_links=True
            )

            # Run the crawler
            logger.info(f"Attempt {attempt + 1}/{retries}")
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=start_url, config=run_config)

            # Process and validate results
            if result.extracted_data:
                logger.info("Successfully extracted data!")
                
                # Validate the extracted data
                try:
                    validated_data = LeagueTableData(**result.extracted_data)
                    team_count = validated_data.get_team_count()
                    top_team = validated_data.get_top_team()
                    
                    logger.info(f"✓ Found {team_count} teams in {validated_data.league}")
                    if top_team:
                        logger.info(f"✓ League leader: {top_team.team_name} with {top_team.points} points")
                    
                    # Save to file if requested
                    if save_to_file:
                        # Sanitize league name for filename
                        safe_league_name = league_name.lower().replace(" ", "_").replace("/", "_")
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = config.output_dir / f"{safe_league_name}_table_{timestamp}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(validated_data.to_dict(), f, indent=2, ensure_ascii=False)
                        logger.info(f"✓ Data saved to {filename}")
                    
                    return validated_data.to_dict()
                    
                except Exception as e:
                    logger.error(f"Data validation failed: {e}")
                    logger.debug(f"Raw extracted data: {result.extracted_data}")
                    # Try to save raw data for debugging
                    if save_to_file:
                        debug_filename = config.output_dir / f"debug_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        with open(debug_filename, 'w', encoding='utf-8') as f:
                            json.dump(result.extracted_data, f, indent=2, ensure_ascii=False)
                        logger.info(f"Raw data saved to {debug_filename} for debugging")
                    
            else:
                logger.warning("No data extracted from the page")
                
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("All retry attempts exhausted")
    
    return None

# --- 4. European Leagues Configuration ---
EUROPEAN_LEAGUES = {
    # Top 5 Leagues (Big 5)
    "Premier League": {
        "name": "Premier League",
        "country": "England",
        "tier": 1,
        "url": None  # Will be set from environment or default
    },
    "La Liga": {
        "name": "La Liga",
        "country": "Spain",
        "tier": 1,
        "url": None
    },
    "Bundesliga": {
        "name": "Bundesliga",
        "country": "Germany",
        "tier": 1,
        "url": None
    },
    "Serie A": {
        "name": "Serie A",
        "country": "Italy",
        "tier": 1,
        "url": None
    },
    "Ligue 1": {
        "name": "Ligue 1",
        "country": "France",
        "tier": 1,
        "url": None
    },
    
    # Other Major European Leagues
    "Eredivisie": {
        "name": "Eredivisie",
        "country": "Netherlands",
        "tier": 1,
        "url": None
    },
    "Primeira Liga": {
        "name": "Primeira Liga",
        "country": "Portugal",
        "tier": 1,
        "url": None
    },
    "Super Lig": {
        "name": "Süper Lig",
        "country": "Turkey",
        "tier": 1,
        "url": None
    },
    "Premier Liga": {
        "name": "Premier Liga",
        "country": "Russia",
        "tier": 1,
        "url": None
    },
    "Belgian First Division A": {
        "name": "Belgian First Division A",
        "country": "Belgium",
        "tier": 1,
        "url": None
    },
    "Super League": {
        "name": "Super League",
        "country": "Greece",
        "tier": 1,
        "url": None
    },
    "Austrian Bundesliga": {
        "name": "Austrian Bundesliga",
        "country": "Austria",
        "tier": 1,
        "url": None
    },
    "Super Liga": {
        "name": "Super Liga",
        "country": "Serbia",
        "tier": 1,
        "url": None
    },
    "Ukrainian Premier League": {
        "name": "Ukrainian Premier League",
        "country": "Ukraine",
        "tier": 1,
        "url": None
    },
    "First League": {
        "name": "First League",
        "country": "Czech Republic",
        "tier": 1,
        "url": None
    },
    "Swiss Super League": {
        "name": "Swiss Super League",
        "country": "Switzerland",
        "tier": 1,
        "url": None
    },
    
    # Championship/Second Tier Leagues
    "EFL Championship": {
        "name": "EFL Championship",
        "country": "England",
        "tier": 2,
        "url": None
    },
    "La Liga 2": {
        "name": "La Liga 2",
        "country": "Spain",
        "tier": 2,
        "url": None
    },
    "2. Bundesliga": {
        "name": "2. Bundesliga",
        "country": "Germany",
        "tier": 2,
        "url": None
    },
    "Serie B": {
        "name": "Serie B",
        "country": "Italy",
        "tier": 2,
        "url": None
    },
    "Ligue 2": {
        "name": "Ligue 2",
        "country": "France",
        "tier": 2,
        "url": None
    },
    
    # Scandinavian Leagues
    "Allsvenskan": {
        "name": "Allsvenskan",
        "country": "Sweden",
        "tier": 1,
        "url": None
    },
    "Eliteserien": {
        "name": "Eliteserien",
        "country": "Norway",
        "tier": 1,
        "url": None
    },
    "Danish Superliga": {
        "name": "Danish Superliga",
        "country": "Denmark",
        "tier": 1,
        "url": None
    },
    "Veikkausliiga": {
        "name": "Veikkausliiga",
        "country": "Finland",
        "tier": 1,
        "url": None
    },
    
    # Eastern European Leagues
    "Ekstraklasa": {
        "name": "Ekstraklasa",
        "country": "Poland",
        "tier": 1,
        "url": None
    },
    "Liga I": {
        "name": "Liga I",
        "country": "Romania",
        "tier": 1,
        "url": None
    },
    "Prva HNL": {
        "name": "Prva HNL",
        "country": "Croatia",
        "tier": 1,
        "url": None
    },
    "HNL": {
        "name": "HNL",
        "country": "Slovenia",
        "tier": 1,
        "url": None
    },
    "Slovak Super Liga": {
        "name": "Slovak Super Liga",
        "country": "Slovakia",
        "tier": 1,
        "url": None
    },
    "Liga 1": {
        "name": "Liga 1",
        "country": "Bulgaria",
        "tier": 1,
        "url": None
    },
    
    # Celtic Nations
    "Scottish Premiership": {
        "name": "Scottish Premiership",
        "country": "Scotland",
        "tier": 1,
        "url": None
    },
    "League of Ireland Premier Division": {
        "name": "League of Ireland Premier Division",
        "country": "Ireland",
        "tier": 1,
        "url": None
    },
    "Cymru Premier": {
        "name": "Cymru Premier",
        "country": "Wales",
        "tier": 1,
        "url": None
    }
}

# --- 5. Helper Functions ---
def get_league_env_var_name(league_key: str) -> str:
    """Convert league key to environment variable name."""
    # Replace spaces and special characters with underscores
    var_name = league_key.upper().replace(" ", "_").replace(".", "").replace("-", "_")
    return f"{var_name}_URL"


def get_leagues_by_tier(leagues_dict: dict, tier: int) -> dict:
    """Filter leagues by tier (1 for top tier, 2 for second tier, etc.)."""
    return {k: v for k, v in leagues_dict.items() if v.get("tier") == tier}


# --- 6. Main Function ---
async def main():
    """
    Main function to scrape European league tables.
    In a production system, this would integrate with Kafka or a job queue.
    """
    # Configuration for scraping
    # Allow LLM provider to be overridden via environment variable
    llm_provider = os.environ.get("LLM_PROVIDER", "openai/gpt-4o")
    custom_config = ScraperConfig(
        max_depth=1,  # Reduced depth for more focused scraping (league tables are usually on main pages)
        max_pages=5,  # Reduced pages since we're targeting specific league tables
        headless=True,
        use_proxy=True,
        llm_provider=llm_provider,  # Allow custom LLM provider
        output_dir="output"
    )
    
    # Get configuration from environment
    # Filter by tier if specified (default: 1 for top tier)
    target_tier = int(os.environ.get("LEAGUE_TIER", "1"))
    
    # Get base URL pattern
    base_url = os.environ.get("SPORTS_BASE_URL", "")
    
    # Filter leagues by tier
    if target_tier > 0:
        leagues_to_scrape = get_leagues_by_tier(EUROPEAN_LEAGUES, target_tier)
        logger.info(f"Filtering to Tier {target_tier} leagues")
    else:
        leagues_to_scrape = EUROPEAN_LEAGUES
        logger.info("Scraping all leagues")
    
    # Check if user wants to scrape specific leagues only
    selected_leagues = os.environ.get("SELECTED_LEAGUES", "").strip()
    if selected_leagues:
        # Comma-separated list of league names
        league_names = [name.strip() for name in selected_leagues.split(",")]
        leagues_to_scrape = {
            k: v for k, v in leagues_to_scrape.items() 
            if k in league_names or v["name"] in league_names
        }
        logger.info(f"Scraping selected leagues: {', '.join(leagues_to_scrape.keys())}")
    
    results = {}
    
    logger.info("=" * 70)
    logger.info(f"Starting scrape of European League Tables")
    logger.info(f"Total leagues to scrape: {len(leagues_to_scrape)}")
    logger.info("=" * 70)
    
    for league_key, league_info in leagues_to_scrape.items():
        league_name = league_info["name"]
        country = league_info["country"]
        tier = league_info["tier"]
        
        # Try to get URL from environment variable
        env_var_name = get_league_env_var_name(league_key)
        url = os.environ.get(env_var_name, "")
        
        # If no specific URL, try to construct from base URL
        if not url:
            if base_url:
                # Construct URL from base URL (example pattern)
                # Adjust this pattern based on your target website
                url = f"{base_url.rstrip('/')}/{league_name.lower().replace(' ', '-').replace('.', '')}"
            else:
                logger.warning(f"⚠ No URL configured for {league_name} ({country}). Skipping...")
                logger.info(f"  Set {env_var_name} environment variable or SPORTS_BASE_URL")
                continue
        
        logger.info("")
        logger.info(f"🏆 Scraping {league_name}")
        logger.info(f"   Country: {country} | Tier: {tier}")
        logger.info("-" * 70)
        
        result = await scrape_league_table(
            start_url=url,
            league_name=league_name,
            config=custom_config,
            retries=3,
            save_to_file=True
        )
        
        if result:
            results[league_key] = result
            logger.info(f"✅ Successfully scraped {league_name}")
            
            # Here you would typically send to Kafka:
            # kafka_producer.send('league-tables-topic', value=result)
        else:
            logger.error(f"❌ Failed to scrape {league_name}")
            results[league_key] = None
        
        # Delay between leagues to be respectful to the website
        if league_key != list(leagues_to_scrape.keys())[-1]:  # Don't wait after last league
            await asyncio.sleep(3)
    
    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("SCRAPING SUMMARY")
    logger.info("=" * 70)
    successful = sum(1 for r in results.values() if r is not None)
    total = len(leagues_to_scrape)
    logger.info(f"Successfully scraped: {successful}/{total} leagues")
    
    # Group by tier for better visibility
    tier_groups = {}
    for league_key, result in results.items():
        tier = EUROPEAN_LEAGUES[league_key]["tier"]
        if tier not in tier_groups:
            tier_groups[tier] = []
        tier_groups[tier].append((league_key, result))
    
    for tier in sorted(tier_groups.keys()):
        logger.info(f"\nTier {tier} Leagues:")
        for league_key, result in tier_groups[tier]:
            status = "✅" if result else "❌"
            logger.info(f"  {status} {EUROPEAN_LEAGUES[league_key]['name']} ({EUROPEAN_LEAGUES[league_key]['country']})")
    
    logger.info("=" * 70)
    
    return results


if __name__ == "__main__":
    """
    Run the league table scraper for European Leagues.
    
    Required Environment Variables:
    - OPENAI_API_KEY: Your OpenAI API key for GPT-4o
    
    Optional Environment Variables:
    - PROXY_URL: Proxy server URL (optional, but recommended)
    - SPORTS_BASE_URL: Base URL for sports website (if URLs follow a pattern)
    
    League-Specific URLs (Optional):
    - Set individual league URLs like: PREMIER_LEAGUE_URL, LA_LIGA_URL, etc.
    - Or use SPORTS_BASE_URL pattern for automatic URL construction
    
    Filtering Options:
    - LEAGUE_TIER: Filter by tier (1, 2, etc.). Default: 1
    - SELECTED_LEAGUES: Comma-separated list of specific leagues to scrape
    
    Example .env file:
    OPENAI_API_KEY=your_api_key_here
    PROXY_URL=http://user:pass@proxy-server.com:8080
    SPORTS_BASE_URL=https://www.example.com
    
    # Optional: Filter to specific leagues
    LEAGUE_TIER=1
    SELECTED_LEAGUES=Premier League,La Liga,Bundesliga
    
    # Optional: Set specific URLs
    PREMIER_LEAGUE_URL=https://www.example.com/premier-league/table
    EREDIVISIE_URL=https://www.example.com/eredivisie/table
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)