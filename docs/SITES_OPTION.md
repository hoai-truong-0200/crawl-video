# Sites Option - Parse Initial Categories and Series

## Overview

The **`sites`** option crawls the initial list of categories and series from the main learn-content and explore-content pages, then saves them to JSON files.

This is the **FIRST STEP** in the crawling workflow - it parses the LIST of categories/series, not the details within them.

## Prerequisites

**IMPORTANT**: You must run the command inside the virtual environment (venv):

```bash
# Activate venv first
source venv/bin/activate

# Then run the command
python run_browser.py sites [language]
```

## What It Does

1. **Reads sites.json** to get URLs for each language:
   ```json
   {
       "en": [
           "https://unlimited.globis.co.jp/en/learn-content",
           "https://unlimited.globis.co.jp/en/explore-content"
       ],
       "ja": [
           "https://unlimited.globis.co.jp/ja/learn-content",
           "https://unlimited.globis.co.jp/ja/explore-content"
       ]
   }
   ```

2. **For each language**:
   - Navigates to `learn-content` URL
   - **Clicks "Show More" / "もっと見る" button** until all categories are visible
   - Parses all category links (e.g., `/categories/critical-thinking-communication`)
   - Saves to `data/courses/{lang}/learn-content.json`

   - Navigates to `explore-content` URL
   - **Clicks "Show More" / "もっと見る" button** until all series are visible
   - Parses all series links (e.g., `/series/d884adf8`)
   - Saves to `data/courses/{lang}/explore-content.json`

3. **Auto-creates files/folders** if they don't exist

## Show More Button Handling

The parser automatically handles the "Show More" button that lazy-loads content:
- **English pages**: Looks for "Show More" button
- **Japanese pages**: Looks for "もっと見る" button
- **Clicks repeatedly** until button disappears (all content loaded)
- **Safety limit**: Max 50 clicks to prevent infinite loops
- **Wait time**: 1.5 seconds between clicks for content to load

This ensures all categories and series are captured, not just the initially visible ones.

## Usage

### Parse All Languages

```bash
source venv/bin/activate
python run_browser.py sites
```

This will:
- Parse EN learn-content → Save categories to `data/courses/en/learn-content.json`
- Parse EN explore-content → Save series to `data/courses/en/explore-content.json`
- Wait 10 seconds
- Parse JA learn-content → Save categories to `data/courses/ja/learn-content.json`
- Parse JA explore-content → Save series to `data/courses/ja/explore-content.json`

### Parse Specific Language

#### English Only
```bash
source venv/bin/activate
python run_browser.py sites en
```

#### Japanese Only
```bash
source venv/bin/activate
python run_browser.py sites ja
```

## Output Structure

### learn-content.json (Categories)

```json
{
  "language": "en",
  "last_updated": "2025-11-24T23:30:00.000000",
  "categories": [
    {
      "title": "Critical Thinking and Communication",
      "url": "https://unlimited.globis.co.jp/en/categories/critical-thinking-communication",
      "last_updated": "2025-11-24T23:30:00.000000",
      "courses": []
    },
    {
      "title": "Strategy and Marketing",
      "url": "https://unlimited.globis.co.jp/en/categories/strategy-marketing",
      "last_updated": "2025-11-24T23:30:00.000000",
      "courses": []
    }
  ]
}
```

### explore-content.json (Series)

```json
{
  "series": [
    {
      "title": "Leader's Challenges",
      "url": "https://unlimited.globis.co.jp/en/series/d884adf8",
      "last_updated": "2025-11-24T23:30:00.000000",
      "courses": []
    },
    {
      "title": "GLOBIS Insights",
      "url": "https://unlimited.globis.co.jp/en/series/abc123",
      "last_updated": "2025-11-24T23:30:00.000000",
      "courses": []
    }
  ]
}
```

Note: `courses` array is empty at this stage - it will be filled by subsequent crawling steps.

## Workflow

The complete crawling workflow is:

1. **`sites`** - Parse initial categories/series (THIS OPTION)
2. **`categories`** - Crawl course details within each category
3. **`series`** - Crawl course details within each series
4. **`courses`** - Crawl overview, transcript, duration
5. **`videos`** - Crawl video URLs and LearnPoints
6. **`downloads`** - Download all videos

## Error Handling

### No Categories Found

If no categories are found, the parser will log a warning but continue:

```
⚠️  No categories found for EN
```

This could happen if:
- The HTML structure has changed
- The page didn't load properly
- You're not logged in

### Auto-Initialization

If the JSON files don't exist or are invalid, ContentManager will automatically create them with the correct structure:

- Missing file → Creates new file
- Empty file → Initializes with correct structure
- Invalid JSON → Fixes and reinitializes

## Technical Details

### Parser Implementation

**File**: `src/crawler/category_parser.py`

#### Methods Added

1. **`parse_initial_categories(page)`**
   - Extracts all links matching `a[href*="/categories/"]`
   - Returns list of `CategoryInfo` objects

2. **`parse_initial_series(page)`**
   - Extracts all links matching `a[href*="/series/"]`
   - Returns list of `CategoryInfo` objects

#### Selector Logic

The parser looks for:
- **Categories**: Any `<a>` tag with `href` containing `/categories/`
- **Series**: Any `<a>` tag with `href` containing `/series/`

Automatically:
- Removes duplicates (same URL)
- Converts relative URLs to absolute
- Cleans up whitespace in titles

### Function Implementation

**File**: `run_browser.py`

**Function**: `crawl_sites_initial(page, target_language=None)`

#### Process Flow

```
1. Load sites.json via SitesManager
2. Filter languages (all or specific)
3. Create parser = CategoryParser()
4. For each language:
   a. Navigate to learn-content URL
   b. Parse categories → Save to learn-content.json
   c. Wait 5 seconds
   d. Navigate to explore-content URL
   e. Parse series → Save to explore-content.json
   f. Wait 10 seconds before next language
5. Show summary statistics
```

## Troubleshooting

### Error: ModuleNotFoundError: No module named 'playwright'

**Solution**: Activate venv first:
```bash
source venv/bin/activate
python run_browser.py sites
```

### Error: Language 'xx' not found in sites.json

**Solution**: Check `data/courses/sites.json` for available languages. Currently supports: `en`, `ja`

### No categories/series found

**Possible causes**:
1. Not logged in - The browser automation will prompt for manual login
2. HTML structure changed - Check and update selectors in `category_parser.py`
3. Network issues - Check internet connection

**Debug**: Run with `test` mode to inspect the page:
```bash
source venv/bin/activate
python run_browser.py test
# Browser stays open for manual inspection
```

## Examples

### Complete Fresh Start

```bash
# 1. Activate venv
source venv/bin/activate

# 2. Parse all categories and series
python run_browser.py sites

# 3. Crawl category details (English)
python run_browser.py categories en

# 4. Crawl series details (English)
python run_browser.py series en

# 5. Crawl course details
python run_browser.py courses en

# 6. Crawl videos
python run_browser.py videos en

# 7. Download videos
python run_browser.py downloads en
```

### Parse Only Japanese

```bash
source venv/bin/activate
python run_browser.py sites ja
```

Output:
```
🌍 CRAWLING SITES FOR JA
📚 Part 1: Parsing categories from learn-content...
   URL: https://unlimited.globis.co.jp/ja/learn-content
✅ Found 12 categories
💾 Saved 12 categories to data/courses/ja/learn-content.json

🎬 Part 2: Parsing series from explore-content...
   URL: https://unlimited.globis.co.jp/ja/explore-content
✅ Found 8 series
💾 Saved 8 series to data/courses/ja/explore-content.json

✅ SITES CRAWLING COMPLETE - ALL SUCCESS
```

## Differences from Old `init` Option

### Old `init` Option (Deprecated)
- Attempted to crawl categories AND their course details in one go
- Required existing JSON files with category data
- Complex error handling
- Mixed responsibilities

### New `sites` Option (Current)
- **Single responsibility**: Parse category/series LISTS only
- Auto-creates files if missing
- Clear separation of concerns
- Simpler error handling
- Faster execution (only parses links, not course details)

### New `init` Option (Under Development)
- Will only copy Chrome profile for authentication
- Simplified to single purpose
- Not yet implemented

## Related Documentation

- [AUTO_INIT_JSON.md](./AUTO_INIT_JSON.md) - Auto-initialization of JSON files
- [INCREMENTAL_SAVE.md](./INCREMENTAL_SAVE.md) - Incremental saving feature
- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Project setup and venv installation
