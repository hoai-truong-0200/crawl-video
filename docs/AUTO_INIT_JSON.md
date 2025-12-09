# Auto-Initialization of JSON Files

## Overview

ContentManager now automatically initializes JSON files with the correct structure when they are empty, invalid, or missing. This eliminates the need to manually create or fix JSON files before crawling.

## Features

### 1. Auto-Detection of File Type

ContentManager automatically detects whether it's working with:
- **learn-content.json**: Creates `{"language": "...", "last_updated": "", "categories": []}`
- **explore-content.json**: Creates `{"series": []}`

Detection is based on the file path - if the path contains "explore-content", it's treated as a series file.

### 2. Handles Multiple Scenarios

The auto-initialization kicks in when:

1. **File doesn't exist**: Creates new file with correct structure
2. **File is empty** (0 bytes or < 3 bytes): Initializes with correct structure
3. **File contains invalid JSON** (e.g., `[]` array instead of object): Fixes and reinitializes
4. **File has parse errors**: Catches exception and reinitializes

### 3. Automatic Language Support

For **learn-content.json**:
```json
{
  "language": "ja",
  "last_updated": "",
  "categories": []
}
```

For **explore-content.json**:
```json
{
  "series": []
}
```

## Usage

Simply use ContentManager as normal - no special setup needed:

```python
from src.crawler.content_manager import ContentManager

# Will auto-create if missing or invalid
manager = ContentManager(Path("data/courses/ja/learn-content.json"), language="ja")
manager.load()  # Auto-initializes if needed

# Now ready to use
print(len(manager.categories))  # 0 (empty, ready for crawling)
```

## Benefits

1. **No manual file creation**: Just run `init` command for any language
2. **Error recovery**: Automatically fixes corrupted JSON files
3. **Consistent structure**: Ensures all files have the correct format
4. **Multi-language ready**: Works for EN, JA, and any future languages

## Examples

### Before (Manual Creation Required)

```bash
# Had to manually create files first
echo '{"language": "ja", "last_updated": "", "categories": []}' > data/courses/ja/learn-content.json
echo '{"series": []}' > data/courses/ja/explore-content.json

# Then run init
python3 run_browser.py init ja
```

### After (Automatic)

```bash
# Just run init - files created automatically
python3 run_browser.py init ja
```

## Implementation Details

### ContentManager Changes

1. **Added `series` property**: `self.series: List[Series] = []`
2. **Added `is_explore_content` flag**: Auto-detects file type
3. **Enhanced `load()` method**:
   - Checks file size
   - Validates JSON structure
   - Auto-initializes on error
4. **New `_initialize_empty_file()` method**: Creates correct structure based on file type
5. **Enhanced `save()` method**: Saves correct structure (categories vs series)

### Load Flow

```
load()
  → File missing? → Initialize empty structure
  → File too small? → Initialize empty structure
  → Load JSON → Is array instead of object? → Initialize empty structure
  → Parse error? → Initialize empty structure
  → Success! → Load categories/series
```

## Testing

Test the auto-initialization:

```bash
# Remove JSON files
rm -f data/courses/ja/*.json

# Run init - files will be created automatically
python3 run_browser.py init ja

# Check structure
cat data/courses/ja/learn-content.json
# Should show: {"language": "ja", "last_updated": "", "categories": []}

cat data/courses/ja/explore-content.json
# Should show: {"series": []}
```

## Notes

- Files are created immediately when first loaded
- Directory structure (`data/courses/{lang}/`) is auto-created
- UTF-8 encoding is used for all files
- Pretty-printed with 2-space indentation

## Related Files

- **Implementation**: `src/crawler/content_manager.py`
- **Used by**:
  - `src/crawler/category_crawler.py`
  - `src/crawler/series_crawler.py`
  - `src/crawler/course_crawler.py`
