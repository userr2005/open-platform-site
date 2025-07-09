import pandas as pd
from pathlib import Path
import re


def parse_float(value):
    """Parse a string to float, ignoring commas and other non-numeric characters."""
    if pd.isna(value):
        return None
    try:
        return float(re.sub(r"[^0-9.]+", "", str(value)))
    except ValueError:
        return None


def score_row(row, deal_size, geography, sector_keywords, esg_keywords, has_esg):
    """Return a relevance score for an investor row."""
    score = 0.0

    # Sector focus match
    sector_text = str(row.get('sector focus', '')).lower()
    sector_hits = sum(kw in sector_text for kw in sector_keywords)
    score += 3 * sector_hits  # weight sector matches heavily

    # ESG relevance
    if has_esg:
        esg_hits = sum(kw in sector_text for kw in esg_keywords)
        score += esg_hits

    # Geography match
    geo_text = str(row.get('geographical focus', '')).lower()
    if geography.lower() in geo_text:
        score += 2

    # Investment size closeness
    inv_size = parse_float(row.get('average investment size'))
    if inv_size is not None and deal_size > 0:
        diff = abs(inv_size - deal_size)
        size_score = max(0, 1 - (diff / deal_size))
        score += size_score

    return score


def main():
    input_filename = 'Test Investor Tracker.xlsx'

    # --- Deal metadata input ---
    deal_name = input('Deal Name: ').strip()
    size_text = input('Deal Size (in millions USD): ').strip().replace(',', '')
    try:
        deal_size = float(size_text)
    except ValueError:
        print('Could not parse deal size, defaulting to 0.')
        deal_size = 0.0

    geography = input('Geographical Region: ').strip()

    primary_sectors = {
        1: 'energy', 2: 'industrials', 3: 'utilities', 4: 'healthcare',
        5: 'financials', 6: 'consumer', 7: 'technology', 8: 'real estate',
        9: 'mining', 10: 'agriculture'
    }
    print('\nSelect the primary sector for the deal:')
    for num, name in primary_sectors.items():
        print(f"{num}. {name.title()}")
    while True:
        try:
            choice = int(input('Enter a number (1-10): '))
            if choice in primary_sectors:
                selected_sector = primary_sectors[choice]
                break
        except ValueError:
            pass
        print('Invalid selection.')

    while True:
        esg_input = input('Any ESG/Sustainability relation? (yes/no): ').strip().lower()
        if esg_input in ('yes', 'no'):
            has_esg = esg_input == 'yes'
            break
        print("Please answer 'yes' or 'no'.")

    # --- Load investor tracker ---
    if not Path(input_filename).exists():
        print(f"Input file '{input_filename}' not found.")
        return
    df = pd.read_excel(input_filename)
    print(f"Loaded {len(df)} investors from {input_filename}")

    # --- Sector word banks ---
    sector_word_bank = {
        'energy': ['oil', 'gas', 'lng', 'renewables', 'solar', 'wind', 'hydro', 'geothermal',
                   'nuclear', 'biofuels', 'energy infrastructure', 'power', 'power generation',
                   'electricity', 'storage', 'batteries', 'energy transition', 'energy trading',
                   'offshore', 'onshore', 'drilling', 'exploration', 'pipeline', 'refining',
                   'hydrocarbons', 'upstream', 'midstream', 'downstream', 'carbon capture',
                   'natural resources', 'resource extraction', 'resource development'],
        'industrials': ['manufacturing', 'engineering', 'construction', 'automation', 'aerospace',
                        'defense', 'machinery', 'capital goods', 'heavy equipment', 'transport equipment',
                        'industrial services', 'robotics', 'supply chain', 'logistics', 'aviation',
                        'rail', 'marine', 'shipbuilding', 'welding', 'industrial materials', 'industrial automation'],
        'utilities': ['electricity', 'grid', 'water', 'waste', 'recycling', 'sewage', 'stormwater',
                      'smart grid', 'district heating', 'public utilities', 'power distribution',
                      'utility services', 'smart metering', 'clean water', 'energy efficiency',
                      'urban infrastructure', 'infrastructure finance'],
        'healthcare': ['pharma', 'pharmaceuticals', 'biotech', 'life sciences', 'medtech', 'healthtech',
                       'clinical trials', 'oncology', 'vaccines', 'drug development', 'therapeutics',
                       'genomics', 'medical devices', 'hospitals', 'health insurance', 'telemedicine',
                       'elder care', 'diagnostics', 'healthcare it', 'e-health', 'personalized medicine',
                       'mental health', 'neuroscience', 'nursing homes'],
        'financials': ['banking', 'insurance', 'asset management', 'wealth management', 'venture capital',
                       'private equity', 'hedge fund', 'fintech', 'capital markets', 'financial services',
                       'credit', 'lending', 'mortgage', 'investment management', 'trading', 'payment systems',
                       'blockchain finance', 'custody', 'reinsurance', 'financial data', 'microfinance', 'actuarial'],
        'consumer': ['retail', 'ecommerce', 'fmcg', 'apparel', 'fashion', 'food & beverage', 'restaurants',
                     'hospitality', 'luxury', 'lifestyle', 'personal care', 'cosmetics', 'home goods',
                     'kitchenware', 'toys', 'wellness', 'travel', 'alcoholic beverages', 'sportswear',
                     'gyms', 'convenience', 'd2c', 'consumer goods'],
        'technology': ['tech', 'technology', 'software', 'hardware', 'cybersecurity', 'saas', 'cloud',
                       'infrastructure', 'ai', 'artificial intelligence', 'machine learning', 'iot',
                       'big data', 'ar', 'vr', 'robotics', 'web3', 'blockchain', 'platforms', 'semiconductors',
                       'data centers', 'it services', 'edtech', 'greentech', 'quantum computing',
                       'mobile apps', 'natural language processing'],
        'real estate': ['real estate', 'residential', 'commercial', 'reit', 'property development', 'mixed use',
                        'retail property', 'office space', 'logistics real estate', 'senior living',
                        'student housing', 'hospitality property', 'rental housing', 'vacation homes',
                        'leasing', 'co-living', 'co-working', 'zoning', 'property management', 'green buildings',
                        'affordable housing'],
        'mining': ['mining', 'metals', 'copper', 'gold', 'iron', 'coal', 'zinc', 'silver', 'aluminum',
                   'nickel', 'uranium', 'lithium', 'rare earths', 'quarrying', 'exploration', 'drilling',
                   'geology', 'extraction', 'mineral processing', 'smelting', 'precious metals',
                   'base metals', 'ore', 'refining', 'commodities', 'natural resources',
                   'resource extraction', 'resource development'],
        'agriculture': ['agriculture', 'farming', 'agribusiness', 'livestock', 'crops', 'seeds', 'irrigation',
                        'greenhouse', 'organic', 'food production', 'agritech', 'fertilizer',
                        'sustainable farming', 'pesticides', 'rural investment', 'aquaculture',
                        'vertical farming', 'precision agriculture'],
        'esg': ['esg', 'sustainability', 'sustainable', 'carbon', 'climate', 'net zero', 'green', 'impact',
                'social impact', 'governance', 'environmental', 'clean energy', 'cleantech',
                'responsible investment', 'csr', 'decarbonisation', 'scope 1', 'scope 2', 'scope 3',
                'carbon neutral', 'biodiversity', 'water stewardship', 'energy efficiency',
                'social responsibility']
    }

    sector_keywords = sector_word_bank.get(selected_sector, [])
    esg_keywords = sector_word_bank['esg']

    # --- Score investors ---
    scores = []
    for _, row in df.iterrows():
        score = score_row(row, deal_size, geography, sector_keywords, esg_keywords, has_esg)
        scores.append(score)
    df['relevance_score'] = scores
    df_sorted = df.sort_values(by='relevance_score', ascending=False)

    # --- Output ---
    output_filename = f"{deal_name.replace(' ', '_')}_{int(deal_size)}M_matches.xlsx"
    df_sorted.to_excel(output_filename, index=False)
    print(f"Results written to {output_filename}")


if __name__ == '__main__':
    main()
