# 🌍 Init Feature - Multi-Language Initialization

## Tính năng mới: `init` command

Tính năng này cho phép tự động crawl categories và series cho tất cả các ngôn ngữ được định nghĩa trong file `sites.json`.

## 📋 Cách sử dụng

### 1. Khởi tạo tất cả ngôn ngữ

```bash
python run_browser.py init
```

Lệnh này sẽ:
- Đọc file `data/courses/sites.json`
- Tự động crawl **tất cả ngôn ngữ** (EN + JA)
- Lưu kết quả vào các file JSON tương ứng:
  - `data/courses/en/learn-content.json`
  - `data/courses/en/explore-content.json`
  - `data/courses/ja/learn-content.json`
  - `data/courses/ja/explore-content.json`

### 2. Khởi tạo một ngôn ngữ cụ thể

```bash
# Chỉ crawl English
python run_browser.py init en

# Chỉ crawl Japanese
python run_browser.py init ja
```

## 📁 File sites.json

File `data/courses/sites.json` định nghĩa các URL cho từng ngôn ngữ:

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

## 🔄 Quy trình thực hiện

Khi chạy `init`, hệ thống sẽ:

1. **Load sites.json** - Đọc danh sách ngôn ngữ và URLs
2. **Tạo thư mục** - Tự động tạo `data/courses/{lang}/` nếu chưa có
3. **Duyệt qua từng ngôn ngữ**:
   - Crawl **categories** (learn-content)
   - Đợi 10 giây
   - Crawl **series** (explore-content)
   - Đợi 15 giây trước khi chuyển sang ngôn ngữ tiếp theo
4. **Lưu kết quả** - Ghi vào file JSON theo ngôn ngữ

## ⏱️ Thời gian thực hiện

- **Mỗi ngôn ngữ**: ~5-10 phút (tùy số lượng categories/series)
- **Tất cả ngôn ngữ** (EN + JA): ~15-25 phút

## 📊 Kết quả

Sau khi chạy xong, bạn sẽ có:

```
data/courses/
├── en/
│   ├── learn-content.json    ✅ Categories EN
│   └── explore-content.json  ✅ Series EN
└── ja/
    ├── learn-content.json    ✅ Categories JA
    └── explore-content.json  ✅ Series JA
```

## 🎯 Khi nào sử dụng?

### ✅ Sử dụng `init` khi:
- Lần đầu tiên setup project
- Muốn refresh toàn bộ danh sách categories/series
- Thêm ngôn ngữ mới vào sites.json
- Cần đồng bộ lại data từ đầu

### ❌ KHÔNG sử dụng `init` khi:
- Chỉ cần update một số courses cụ thể (dùng `courses`, `videos` thay thế)
- Đã có data và chỉ muốn download video (dùng `downloads`)
- Đang test một category (dùng `test`)

## 🔧 So sánh với các commands khác

| Command | Scope | Input | Output |
|---------|-------|-------|--------|
| `init` | Multi-language | sites.json | All categories + series |
| `categories` | Single language | Default EN | learn-content.json |
| `series` | Single language | Default EN | explore-content.json |
| `all` | Full workflow | Default EN | Categories + series + courses + videos |

## 💡 Tips

1. **Chạy init trước tiên**: Nên chạy `init` trước các commands khác để có danh sách đầy đủ

2. **Kiểm tra sites.json**: Đảm bảo file sites.json có đúng URLs trước khi chạy

3. **Login một lần**: Session được lưu trong Chrome profile, không cần login lại

4. **Monitor logs**: Theo dõi logs để xem tiến độ crawling

## 🐛 Troubleshooting

### Lỗi: "Language 'xx' not found in sites.json"
→ Kiểm tra lại file sites.json, đảm bảo ngôn ngữ đã được định nghĩa

### Lỗi: "Failed to crawl categories/series"
→ Kiểm tra:
- Internet connection
- Login session còn hiệu lực
- URLs trong sites.json còn hợp lệ

### Một số ngôn ngữ fail, một số success
→ Không sao, kết quả của các ngôn ngữ success vẫn được lưu. Chạy lại với ngôn ngữ cụ thể:
```bash
python run_browser.py init ja  # Chỉ retry Japanese
```

## 📝 Examples

### Example 1: First time setup
```bash
# Step 1: Test and login
python run_browser.py test

# Step 2: Initialize all languages
python run_browser.py init

# Step 3: Crawl course details for all languages
python run_browser.py courses
```

### Example 2: Update only Japanese content
```bash
# Update Japanese categories and series only
python run_browser.py init ja
```

### Example 3: Full workflow
```bash
# Initialize all languages
python run_browser.py init

# Then run full workflow for each language
python run_browser.py all
```

## 🔗 Related

- [SitesManager](../src/utils/sites_manager.py) - Class quản lý sites.json
- [CategoryCrawler](../src/crawler/category_crawler.py) - Crawler cho categories
- [SeriesCrawler](../src/crawler/series_crawler.py) - Crawler cho series

---

**Last Updated**: 2025-11-24  
**Status**: ✅ Production Ready
