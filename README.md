# AI-Powered European League Table Scraper

An intelligent web scraper that uses GPT-4o and Crawl4AI to extract league table/standings data from 40+ European football leagues. The scraper uses AI to understand page structure and extract data, making it resilient to website layout changes.

## Supported Leagues

The scraper automatically extracts league tables for **40+ European leagues** including:

**Top 5 Leagues (Big 5)**
- 🏴 **Premier League** (England)
- 🇪🇸 **La Liga** (Spain)
- 🇩🇪 **Bundesliga** (Germany)
- 🇮🇹 **Serie A** (Italy)
- 🇫🇷 **Ligue 1** (France)

**Other Major Leagues**
- 🇳🇱 Eredivisie, 🇵🇹 Primeira Liga, 🇹🇷 Süper Lig, 🇷🇺 Premier Liga, 🇧🇪 Belgian First Division A, 🇬🇷 Super League, 🇦🇹 Austrian Bundesliga, 🇷🇸 Super Liga, 🇺🇦 Ukrainian Premier League, 🇨🇿 First League, 🇨🇭 Swiss Super League

**Second Tier**
- 🇬🇧 EFL Championship, 🇪🇸 La Liga 2, 🇩🇪 2. Bundesliga, 🇮🇹 Serie B, 🇫🇷 Ligue 2

**Scandinavian**
- 🇸🇪 Allsvenskan, 🇳🇴 Eliteserien, 🇩🇰 Danish Superliga, 🇫🇮 Veikkausliiga

**Eastern European**
- 🇵🇱 Ekstraklasa, 🇷🇴 Liga I, 🇭🇷 Prva HNL, 🇸🇮 HNL, 🇸🇰 Slovak Super Liga, 🇧🇬 Liga 1

**Celtic Nations**
- 🇸🇪 Scottish Premiership, 🇮🇪 League of Ireland, 🇼🇪 Cymru Premier

And more!

## Features

- 🤖 **AI-Powered Extraction**: Uses GPT-4o to intelligently extract league table data regardless of HTML structure
- 🏆 **Multi-League Support**: Scrapes 40+ European leagues in one run
- 🎯 **Flexible Filtering**: Filter by tier or select specific leagues
- 🔄 **Retry Logic**: Automatic retry with exponential backoff on failures
- 📊 **Data Validation**: Pydantic models ensure data quality and completeness
- 📝 **Comprehensive Logging**: Detailed logs for debugging and monitoring
- 💾 **File Persistence**: Automatically saves extracted data to JSON files (one per league)
- ⚙️ **Configurable**: Flexible configuration for different scraping scenarios
- 🔒 **Proxy Support**: Built-in proxy configuration for production use
- 🎯 **Focused Crawling**: Optimized for league table extraction

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd scrapping
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:

Create a `.env` file in the project root:
```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Proxy Configuration (recommended for production)
# Format: http://username:password@host:port
PROXY_URL=http://ajakltvs-1:ujychf8guhna@p.webshare.io:80

# Filtering Options
# LEAGUE_TIER=1  # Filter by tier (1 for top tier, 2 for second tier, 0 for all)
# SELECTED_LEAGUES=Premier League,La Liga,Bundesliga  # Scrape specific leagues only

# League Table URLs (set these based on your target website)
# Either set individual URLs:
PREMIER_LEAGUE_URL=https://www.example.com/premier-league/table
LA_LIGA_URL=https://www.example.com/la-liga/table
BUNDESLIGA_URL=https://www.example.com/bundesliga/table
SERIE_A_URL=https://www.example.com/serie-a/table
LIGUE_1_URL=https://www.example.com/ligue-1/table

# Or use a base URL pattern (will construct URLs automatically):
SPORTS_BASE_URL=https://www.example.com
```

**Note**: The scraper now supports 40+ European leagues. Individual URLs can be set for each league, or you can use `SPORTS_BASE_URL` if all URLs follow a consistent pattern.

## Usage

### Basic Usage

Run the scraper with default settings:
```bash
python web_scrapping.py
```

### Configuration

You can customize the scraper behavior:

```python
from web_scrapping import ScraperConfig, scrape_site

# Custom configuration
config = ScraperConfig(
    max_depth=3,           # Crawl deeper (default: 2)
    max_pages=20,          # Crawl more pages (default: 10)
    headless=True,         # Run browser in background
    use_proxy=True,        # Enable proxy
    output_dir="results"   # Where to save results
)

# Run with custom config
result = await scrape_site("https://example.com", config=config)
```

### Integration with Kafka

The scraper is designed to integrate with Kafka. Uncomment and configure the Kafka producer in the `main()` function:

```python
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# In main() function:
producer.send('odds-topic', value=result)
```

## Project Structure

```
scrapping/
├── web_scrapping.py     # Main scraper code
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── .env                 # Environment variables (create this)
├── scraper.log          # Log file (generated at runtime)
└── output/              # Extracted data directory (created at runtime)
    ├── premier_league_table_YYYYMMDD_HHMMSS.json
    ├── la_liga_table_YYYYMMDD_HHMMSS.json
    ├── bundesliga_table_YYYYMMDD_HHMMSS.json
    ├── serie_a_table_YYYYMMDD_HHMMSS.json
    └── ligue_1_table_YYYYMMDD_HHMMSS.json
```

## How It Works

1. **Schema Definition**: Pydantic models define the expected data structure
2. **Deep Crawling**: BFS algorithm explores the website structure
3. **AI Extraction**: GPT-4o analyzes pages and extracts structured data
4. **Validation**: Extracted data is validated against the schema
5. **Persistence**: Validated data is saved to JSON files

## Data Model

The scraper extracts complete league tables with the following structure:

```json
{
  "sport": "Football",
  "league": "Premier League",
  "season": "2024-25",
  "standings": [
    {
      "position": 1,
      "team_name": "Manchester City",
      "matches_played": 20,
      "wins": 15,
      "draws": 3,
      "losses": 2,
      "goals_for": 48,
      "goals_against": 20,
      "goal_difference": 28,
      "points": 48
    },
    {
      "position": 2,
      "team_name": "Liverpool",
      "matches_played": 20,
      "wins": 14,
      "draws": 4,
      "losses": 2,
      "goals_for": 45,
      "goals_against": 22,
      "goal_difference": 23,
      "points": 46
    }
    // ... all teams in the league
  ]
}
```

Each league's data is saved to a separate JSON file in the `output/` directory with a timestamp.

## Improving Results

### 1. Provide Correct URLs
Ensure you set the correct URLs for each league in your `.env` file. The URLs should point directly to the league table/standings page.

### 2. Adjust Crawl Configuration
If tables are on different pages:
- Increase `max_depth` (default: 1)
- Increase `max_pages` (default: 5)

### 3. Verify League Names
The scraper uses league names in its extraction instructions. Make sure your target website displays league names clearly (e.g., "Premier League", "La Liga").

### 4. Change LLM Provider
If results are inconsistent, try different providers:
- `openai/gpt-4o` (default)
- `anthropic/claude-3-opus`
- `google/gemini-pro`

### 5. Use Proxies
Rotate proxies to avoid rate limiting and IP bans, especially when scraping multiple leagues.

### 6. Check Output Files
If extraction fails, check the `debug_raw_*.json` files in the output directory to see what the LLM extracted before validation.

## Troubleshooting

### No data extracted
- Check if the URLs are accessible and correct
- Verify your OPENAI_API_KEY is valid and has sufficient credits
- Check if the page actually contains a league table
- Increase `max_pages` and `max_depth` if needed
- Review `scraper.log` for detailed error messages

### Validation errors
- The LLM might not be extracting data in the expected format
- Check the `debug_raw_*.json` files in the output directory
- Verify that the league table on the page has all required fields (position, team, points, etc.)
- Some tables might use different column names or formats

### Partial data extraction
- If only some teams are extracted, the table might be paginated
- Try increasing `max_pages` in the configuration
- Check if the website requires JavaScript rendering (should work with Crawl4AI's browser automation)

### API Rate Limits
- Implement rate limiting in production
- Use exponential backoff (already implemented)
- Consider using multiple API keys

## Production Considerations

1. **Rate Limiting**: Add rate limiting to respect target website policies
2. **Monitoring**: Integrate with monitoring tools (Prometheus, Grafana)
3. **Error Alerting**: Set up alerts for failed scrapes
4. **Cost Management**: Monitor OpenAI API usage and costs
5. **Scalability**: Use job queues (Celery, RQ) for parallel scraping
6. **Caching**: Cache results to avoid re-scraping

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

#   s c r a p p i n g  
 