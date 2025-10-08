#!/usr/bin/env node
/**
 * Simple Vimeo Downloader - Từ config.json
 * Test script để download video với config thủ công
 *
 * Usage:
 *   node simple-download.js config.json output.mp4
 */

const fs = require('fs');
const { spawn } = require('child_process');
const https = require('https');

// Download với yt-dlp
async function downloadWithYtDlp(url, output) {
  return new Promise((resolve, reject) => {
    console.log('🚀 Using yt-dlp...');
    const proc = spawn('yt-dlp', [url, '-o', output, '--no-warnings'], { stdio: 'inherit' });
    proc.on('close', code => code === 0 ? resolve() : reject(new Error(`yt-dlp exit ${code}`)));
    proc.on('error', err => reject(new Error(`yt-dlp not found: ${err.message}`)));
  });
}

// Download progressive MP4
async function downloadProgressive(url, output) {
  return new Promise((resolve, reject) => {
    console.log('📥 Downloading progressive MP4...');
    const file = fs.createWriteStream(output);

    https.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        console.log('🔀 Following redirect...');
        return downloadProgressive(res.headers.location, output).then(resolve).catch(reject);
      }

      if (res.statusCode !== 200) {
        return reject(new Error(`HTTP ${res.statusCode}`));
      }

      const total = parseInt(res.headers['content-length'], 10) || 0;
      let downloaded = 0;

      res.on('data', chunk => {
        downloaded += chunk.length;
        if (total) {
          const percent = ((downloaded / total) * 100).toFixed(1);
          process.stdout.write(`\r⏬ Progress: ${percent}%`);
        }
      });

      res.pipe(file);
      file.on('finish', () => {
        file.close();
        console.log('\n✅ Download completed!');
        resolve();
      });
    }).on('error', err => {
      fs.unlink(output, () => reject(err));
    });
  });
}

// Extract URLs từ config
function extractUrls(config) {
  const files = config.request.files;
  const urls = [];

  // Progressive (best)
  if (files.progressive && files.progressive.length > 0) {
    const best = files.progressive.sort((a, b) => {
      return (parseInt(b.quality) || 0) - (parseInt(a.quality) || 0);
    })[0];
    urls.push({ type: 'progressive', quality: best.quality, url: best.url });
  }

  // HLS
  if (files.hls && files.hls.cdns) {
    const cdn = files.hls.cdns.akfire_interconnect_quic ||
                files.hls.cdns.fastly_skyfire ||
                Object.values(files.hls.cdns)[0];
    if (cdn && cdn.url) {
      urls.push({ type: 'hls', quality: 'adaptive', url: cdn.url });
    }
  }

  // DASH
  if (files.dash && files.dash.cdns) {
    const cdn = files.dash.cdns.akfire_interconnect_quic ||
                files.dash.cdns.fastly_skyfire ||
                Object.values(files.dash.cdns)[0];
    if (cdn && cdn.url) {
      urls.push({ type: 'dash', quality: 'adaptive', url: cdn.url });
    }
  }

  return urls;
}

// Check expiry
function checkExpiry(url) {
  const match = url.match(/exp=(\d+)/);
  if (!match) return { valid: true };

  const exp = parseInt(match[1]);
  const now = Math.floor(Date.now() / 1000);

  return {
    valid: exp > now,
    expired: exp < now,
    expiryTime: new Date(exp * 1000),
    minutesLeft: Math.floor((exp - now) / 60)
  };
}

// Main
async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.log(`
📦 Simple Vimeo Downloader

Usage:
  node simple-download.js <config.json> <output.mp4>

Example:
  node simple-download.js player_config.json video.mp4
    `);
    process.exit(1);
  }

  const configFile = args[0];
  const outputFile = args[1];

  try {
    // Read config
    console.log('📖 Reading config:', configFile);
    const config = JSON.parse(fs.readFileSync(configFile, 'utf8'));

    // Video info
    const video = config.video || {};
    console.log('\n📹 Video Info:');
    console.log('   Title:', video.title || 'Unknown');
    console.log('   ID:', video.id);
    console.log('   Duration:', video.duration + 's');
    console.log('   Resolution:', `${video.width}x${video.height}`);

    // Extract URLs
    const urls = extractUrls(config);

    if (urls.length === 0) {
      throw new Error('No video URLs found in config');
    }

    console.log('\n✅ Found video URLs:');
    urls.forEach((u, i) => {
      console.log(`   ${i + 1}. [${u.type.toUpperCase()}] ${u.quality}`);
    });

    // Select best
    const best = urls[0];
    console.log(`\n⭐ Selected: [${best.type.toUpperCase()}] ${best.quality}`);

    // Check expiry
    const expiry = checkExpiry(best.url);
    if (expiry.expired) {
      console.log('\n❌ URLs EXPIRED!');
      console.log('   Expired at:', expiry.expiryTime.toLocaleString());
      console.log('\n💡 Get fresh config from browser:');
      console.log('   1. Open Vimeo video in browser');
      console.log('   2. F12 → Console → copy(JSON.stringify(window.playerConfig, null, 2))');
      console.log('   3. Save to new config.json');
      process.exit(1);
    }

    if (expiry.minutesLeft !== undefined) {
      console.log(`⏰ URLs valid for ${expiry.minutesLeft} minutes`);
    }

    console.log(`📁 Output: ${outputFile}\n`);

    // Download
    if (best.type === 'progressive') {
      await downloadProgressive(best.url, outputFile);
    } else {
      await downloadWithYtDlp(best.url, outputFile);
    }

    console.log('\n🎉 Success!');
    console.log('📁 Saved to:', outputFile);

  } catch (err) {
    console.error('\n❌ Error:', err.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}
