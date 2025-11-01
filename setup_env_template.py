"""
Generate a template .env file with proxy configuration and all league settings.
Run this script to create a .env file template that you can customize.
"""

import os

ENV_TEMPLATE = """# ============================================
# European League Table Scraper Configuration
# ============================================

# Required: OpenAI API Key
# Get your key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# ============================================
# Proxy Configuration
# ============================================
# Format: http://username:password@host:port
# For WebShare.io proxy
PROXY_URL=http://ajakltvs-1:ujychf8guhna@p.webshare.io:80

# ============================================
# League Filtering Options
# ============================================
# LEAGUE_TIER=1  # Filter by tier: 1 (top tier), 2 (second tier), 0 (all tiers)
# SELECTED_LEAGUES=Premier League,La Liga,Bundesliga  # Comma-separated list of specific leagues

# ============================================
# Target Website Configuration
# ============================================

# Option 1: Set a base URL pattern (recommended if all URLs follow same pattern)
SPORTS_BASE_URL=https://www.your-sports-website.com

# Option 2: Set individual league URLs (uncomment and configure as needed)
# ----- Top 5 Leagues (Big 5) -----
# PREMIER_LEAGUE_URL=https://www.your-site.com/premier-league/table
# LA_LIGA_URL=https://www.your-site.com/la-liga/table
# BUNDESLIGA_URL=https://www.your-site.com/bundesliga/table
# SERIE_A_URL=https://www.your-site.com/serie-a/table
# LIGUE_1_URL=https://www.your-site.com/ligue-1/table

# ----- Other Major European Leagues -----
# EREDIVISIE_URL=https://www.your-site.com/eredivisie/table
# PRIMEIRA_LIGA_URL=https://www.your-site.com/primeira-liga/table
# SUPER_LIG_URL=https://www.your-site.com/super-lig/table
# PREMIER_LIGA_URL=https://www.your-site.com/premier-liga/table
# BELGIAN_FIRST_DIVISION_A_URL=https://www.your-site.com/belgian-first-division-a/table
# SUPER_LEAGUE_URL=https://www.your-site.com/super-league/table
# AUSTRIAN_BUNDESLIGA_URL=https://www.your-site.com/austrian-bundesliga/table
# SUPER_LIGA_URL=https://www.your-site.com/super-liga/table
# UKRAINIAN_PREMIER_LEAGUE_URL=https://www.your-site.com/ukrainian-premier-league/table
# FIRST_LEAGUE_URL=https://www.your-site.com/first-league/table
# SWISS_SUPER_LEAGUE_URL=https://www.your-site.com/swiss-super-league/table

# ----- Championship/Second Tier Leagues -----
# EFL_CHAMPIONSHIP_URL=https://www.your-site.com/efl-championship/table
# LA_LIGA_2_URL=https://www.your-site.com/la-liga-2/table
# 2_BUNDESLIGA_URL=https://www.your-site.com/2-bundesliga/table
# SERIE_B_URL=https://www.your-site.com/serie-b/table
# LIGUE_2_URL=https://www.your-site.com/ligue-2/table

# ----- Scandinavian Leagues -----
# ALLSVENSKAN_URL=https://www.your-site.com/allsvenskan/table
# ELITESERIEN_URL=https://www.your-site.com/eliteserien/table
# DANISH_SUPERLIGA_URL=https://www.your-site.com/danish-superliga/table
# VEIKKAUSLIIGA_URL=https://www.your-site.com/veikkausliiga/table

# ----- Eastern European Leagues -----
# EKSTRAKLASA_URL=https://www.your-site.com/ekstraklasa/table
# LIGA_I_URL=https://www.your-site.com/liga-i/table
# PRVA_HNL_URL=https://www.your-site.com/prva-hnl/table
# HNL_URL=https://www.your-site.com/hnl/table
# SLOVAK_SUPER_LIGA_URL=https://www.your-site.com/slovak-super-liga/table
# LIGA_1_URL=https://www.your-site.com/liga-1/table

# ----- Celtic Nations -----
# SCOTTISH_PREMIERSHIP_URL=https://www.your-site.com/scottish-premiership/table
# LEAGUE_OF_IRELAND_PREMIER_DIVISION_URL=https://www.your-site.com/league-of-ireland-premier-division/table
# CYMRU_PREMIER_URL=https://www.your-site.com/cymru-premier/table

# ============================================
# Tips
# ============================================
# 1. Keep your OpenAI API key secure and never commit it to version control
# 2. The proxy URL is already configured for WebShare.io
# 3. Start with SPORTS_BASE_URL if your target site follows consistent URL patterns
# 4. Uncomment and configure individual league URLs for custom configurations
# 5. Use LEAGUE_TIER to filter which tier of leagues to scrape
# 6. Use SELECTED_LEAGUES to scrape only specific leagues
"""

def create_env_file():
    """Create a .env file from the template."""
    if os.path.exists('.env'):
        print("⚠️  Warning: .env file already exists!")
        response = input("Do you want to overwrite it? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Aborted. Existing .env file preserved.")
            return
    
    with open('.env', 'w') as f:
        f.write(ENV_TEMPLATE)
    
    print("✅ Created .env file successfully!")
    print("\n📝 Next steps:")
    print("   1. Open .env file and add your OPENAI_API_KEY")
    print("   2. Configure your target website URLs")
    print("   3. Adjust filtering options as needed")
    print("\n💡 The proxy is already configured for WebShare.io")

if __name__ == "__main__":
    create_env_file()

