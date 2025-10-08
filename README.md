# 🎥 Vimeo Video Downloader

Tool để download videos từ Vimeo embed URLs một cách đơn giản.

---

## 🚀 Cách sử dụng nhanh

### **Download 1 video:**

```bash
# Bước 1: Lấy config từ browser
# Mở https://player.vimeo.com/video/708055782
# F12 → Console → copy(JSON.stringify(window.playerConfig, null, 2))
# Paste vào my_config.json

# Bước 2: Download
node simple-download.js my_config.json video.mp4
```

### **Download nhiều videos:**

```bash
# Bước 1: Tạo file danh sách
cat > vimeo_links.txt <<EOF
https://player.vimeo.com/video/708055782
https://player.vimeo.com/video/708055907
https://player.vimeo.com/video/708055881
EOF

# Bước 2: Download batch
for i in {1..3}; do
  # Lấy config cho mỗi video từ browser
  # Copy vào config$i.json
  node simple-download.js "config$i.json" "video_$i.mp4"
done
```

---

## 📁 Files chính

| File | Mục đích |
|------|----------|
| **`simple-download.js`** | ⭐ Script chính - Download từ config JSON |
| `config_template.json` | Template để tạo config |
| `vimeo_links.txt` | Danh sách video IDs |
| `download-from-html.js` | Download từ HTML file đã save |

---

## 📝 Cách lấy config từ browser

1. Mở video Vimeo trong browser:
   ```
   https://player.vimeo.com/video/708055782
   ```

2. Mở Console (F12)

3. Copy config:
   ```javascript
   copy(JSON.stringify(window.playerConfig, null, 2))
   ```

4. Paste vào file `my_config.json`

5. Download:
   ```bash
   node simple-download.js my_config.json video.mp4
   ```

---

## ⚠️ Lỗi thường gặp

### **1. URLs expired**

Config có thời hạn ~1 giờ. Nếu gặp lỗi:
```
❌ URLs EXPIRED!
   Expired at: 10/7/2025, 10:06:45 AM
```

**Giải pháp:** Lấy config mới từ browser (xem bước trên)

### **2. yt-dlp not found**

```bash
# Cài yt-dlp
pip install yt-dlp
```

### **3. Config không hợp lệ**

Check file JSON có đúng format không:
```bash
cat my_config.json | jq '.' > /dev/null && echo "✅ Valid JSON" || echo "❌ Invalid JSON"
```

---

## 💡 Workflow đề xuất cho nhiều videos

```bash
# Bước 1: Lấy tất cả configs (trong browser)
# Mở nhiều tabs, mỗi tab 1 video
# Copy config từ mỗi tab vào config1.json, config2.json, ...

# Bước 2: Batch download
for i in {1..10}; do
  echo "Downloading video $i..."
  node simple-download.js "config$i.json" "video_$i.mp4"
  sleep 2
done

echo "✅ All done!"
```

**Ước tính thời gian:**
- Lấy 10 configs: ~5-10 phút
- Download 10 videos: ~5-10 phút
- **Total: ~15-20 phút**

---

## 🔑 Phân tích kỹ thuật

### **Vimeo Embed là Public**

Videos được embed với `embed_permission: "whitelist"` nghĩa là:
- ✅ Video có thể truy cập từ `player.vimeo.com`
- ✅ Không cần authentication với Vimeo
- ✅ URLs có trong `window.playerConfig`

### **Video ID là đủ**

Chỉ cần biết Vimeo Video ID (VD: `708055907`), bạn có thể:
```
https://player.vimeo.com/video/708055907
→ window.playerConfig
→ HLS/DASH URLs
→ Download
```

### **Config có thời hạn**

URLs trong config có parameter `exp=` (expiry timestamp):
- Thời hạn: ~1 giờ từ khi lấy config
- Sau khi expired: cần lấy config mới
- **→ Download ngay sau khi lấy config!**

---

## ❓ Câu hỏi thường gặp

### **Q: Có thể dùng 1 config để download nhiều videos không?**

**A: KHÔNG** ❌

Mỗi Vimeo video có `playerConfig` riêng. Config của video A không chứa URLs của video B.

### **Q: Config hết hạn phải làm sao?**

**A:** Lấy config mới từ browser. URLs trong config chỉ valid ~1 giờ.

### **Q: Có thể tự động lấy config không cần browser?**

**A:** Có thể dùng Playwright nhưng phức tạp hơn. Script `simple-download.js` dùng config thủ công là đơn giản và ổn định nhất.

---

## 📦 So sánh các scripts

| Script | Input | Cần Playwright? | Độ phức tạp |
|--------|-------|----------------|-------------|
| **simple-download.js** | Config JSON | ❌ | ⭐ Dễ nhất |
| download-from-html.js | HTML file | ❌ | ⭐⭐ |
| batch-download-vimeo.js | URL list | ✅ | ⭐⭐⭐ Phức tạp |

**→ Dùng `simple-download.js` cho đơn giản!**

---

## ⚙️ Cài đặt

```bash
# Clone project
git clone <repo-url>
cd crawl-video

# Cài Node.js packages
npm install

# Cài yt-dlp
pip install yt-dlp
```

---

## ✅ Checklist

- [ ] Đã cài `yt-dlp`: `pip install yt-dlp`
- [ ] Có file `simple-download.js`
- [ ] Lấy được config từ browser
- [ ] Config chưa expired (< 1 giờ)
- [ ] Run script: `node simple-download.js config.json video.mp4`
- [ ] Video download thành công!

---

## 🆘 Cần giúp?

1. Check file config có đúng format không
2. Check URLs còn valid không (< 1 giờ)
3. Check `yt-dlp` đã cài chưa
4. Xem log lỗi để biết vấn đề

---

**Kết luận:** Tool này ĐƠN GIẢN, HOẠT ĐỘNG, và DỄ DEBUG nhất! ✅
