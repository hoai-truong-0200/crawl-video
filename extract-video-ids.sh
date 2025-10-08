#!/bin/bash
# Extract Vimeo Video IDs từ HTML files
# Không cần truy cập trực tiếp web chủ

set -e

usage() {
    cat <<EOF
📖 Extract Vimeo Video IDs from HTML files

Usage:
  $0 <html_file> [output_file]
  $0 --batch <html_files_pattern>

Examples:
  $0 video-course.html
  $0 video-course.html video_ids.txt
  $0 --batch "pages/*.html"

Features:
  ✅ Extract từ iframe src
  ✅ Extract từ canonical URL
  ✅ Extract từ window.playerConfig
  ✅ Không cần truy cập web chủ

EOF
}

# Main extraction function
extract_video_ids() {
    local html_file="$1"

    if [ ! -f "$html_file" ]; then
        echo "❌ File not found: $html_file" >&2
        return 1
    fi

    echo "🔍 Extracting from: $html_file" >&2

    # Method 1: Extract from iframe src
    grep -oP 'player\.vimeo\.com/video/\K\d+' "$html_file" 2>/dev/null || true

    # Method 2: Extract from canonical URL
    grep -oP '<link rel="canonical" href="https://player\.vimeo\.com/video/\K\d+' "$html_file" 2>/dev/null || true

    # Method 3: Extract from playerConfig
    grep -oP '"video":\s*{\s*"id":\s*\K\d+' "$html_file" 2>/dev/null || true
}

# Batch extraction
extract_batch() {
    local pattern="$1"

    echo "📦 Batch extraction: $pattern" >&2

    for file in $pattern; do
        if [ -f "$file" ]; then
            extract_video_ids "$file"
        fi
    done
}

# Main
main() {
    if [ $# -eq 0 ]; then
        usage
        exit 1
    fi

    if [ "$1" = "--batch" ]; then
        if [ -z "$2" ]; then
            echo "❌ Missing pattern for --batch" >&2
            exit 1
        fi

        extract_batch "$2" | sort -u
    else
        local html_file="$1"
        local output_file="${2:-}"

        if [ -n "$output_file" ]; then
            extract_video_ids "$html_file" | sort -u > "$output_file"
            echo "✅ Video IDs saved to: $output_file" >&2
            echo "📊 Total IDs: $(wc -l < "$output_file")" >&2
        else
            extract_video_ids "$html_file" | sort -u
        fi
    fi
}

main "$@"
