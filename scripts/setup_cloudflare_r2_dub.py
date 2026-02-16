#!/usr/bin/env python3
"""
Setup Cloudflare R2 for Dub Playlist
=====================================

Uploads dub tracks to Cloudflare R2 bucket for free, unlimited bandwidth hosting.
Requires: wrangler CLI installed and authenticated
"""

import subprocess
import sys
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).parent.parent
DUB_PLAYLIST_DIR = PROJECT_ROOT / "research" / "dub_playlist" / "dub_mixes"
BUCKET_NAME = "grokmon-dub-tracks"


def check_wrangler():
    """Check if wrangler is installed and authenticated."""
    try:
        result = subprocess.run(
            ["wrangler", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Wrangler installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("❌ Wrangler not found. Install with: npm install -g wrangler")
        return False


def create_r2_bucket():
    """Create R2 bucket for dub tracks."""
    print(f"\n📦 Creating R2 bucket: {BUCKET_NAME}")
    
    try:
        result = subprocess.run(
            ["wrangler", "r2", "bucket", "create", BUCKET_NAME],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Bucket created: {BUCKET_NAME}")
            return True
        elif "already exists" in result.stderr.lower():
            print(f"ℹ️  Bucket already exists: {BUCKET_NAME}")
            return True
        else:
            print(f"❌ Error creating bucket: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def upload_tracks():
    """Upload all MP3 files to R2 bucket."""
    if not DUB_PLAYLIST_DIR.exists():
        print(f"❌ Dub playlist directory not found: {DUB_PLAYLIST_DIR}")
        return False
    
    mp3_files = list(DUB_PLAYLIST_DIR.glob("*.mp3"))
    
    if not mp3_files:
        print("❌ No MP3 files found")
        return False
    
    print(f"\n📤 Uploading {len(mp3_files)} tracks to R2...")
    
    uploaded = 0
    failed = 0
    
    for i, mp3_file in enumerate(mp3_files, 1):
        filename = mp3_file.name
        size_mb = mp3_file.stat().st_size / (1024 * 1024)
        
        print(f"[{i}/{len(mp3_files)}] Uploading: {filename} ({size_mb:.1f} MB)")
        
        try:
            result = subprocess.run(
                [
                    "wrangler", "r2", "object", "put",
                    f"{BUCKET_NAME}/{filename}",
                    "--file", str(mp3_file)
                ],
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout per file
            )
            
            if result.returncode == 0:
                uploaded += 1
                print(f"  ✅ Uploaded: {filename}")
            else:
                failed += 1
                print(f"  ❌ Failed: {filename} - {result.stderr}")
        
        except subprocess.TimeoutExpired:
            failed += 1
            print(f"  ⏰ Timeout: {filename}")
        except Exception as e:
            failed += 1
            print(f"  ❌ Error: {filename} - {e}")
    
    print(f"\n📊 Upload Summary:")
    print(f"  ✅ Uploaded: {uploaded}")
    print(f"  ❌ Failed: {failed}")
    
    return failed == 0


def generate_worker_code():
    """Generate Cloudflare Worker code for streaming."""
    worker_code = '''/**
 * Cloudflare Worker: Dub Track Streaming
 * ======================================
 * 
 * Streams dub tracks from R2 with range request support.
 * 
 * Setup:
 *   1. Add to wrangler.toml:
 *      [[r2_buckets]]
 *      binding = "DUB_TRACKS"
 *      bucket_name = "grokmon-dub-tracks"
 * 
 *   2. Deploy:
 *      wrangler deploy cloudflare-worker-dub-stream.js --name grokmon-dub-stream
 * 
 *   3. Add route in Cloudflare Dashboard:
 *      grokandmon.com/api/playlist/dub/stream/*
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const pathParts = url.pathname.split('/');
    const filename = decodeURIComponent(pathParts[pathParts.length - 1]);
    
    if (!filename || !filename.endsWith('.mp3')) {
      return new Response('Invalid filename', { status: 400 });
    }
    
    try {
      // Get range header for partial content
      const range = request.headers.get('range');
      
      // Get object from R2
      const object = await env.DUB_TRACKS.get(filename, {
        range: range || undefined
      });
      
      if (!object) {
        return new Response('Track not found', { status: 404 });
      }
      
      // Prepare headers
      const headers = {
        'Content-Type': 'audio/mpeg',
        'Cache-Control': 'public, max-age=3600, s-maxage=86400',
        'Accept-Ranges': 'bytes',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
        'Access-Control-Allow-Headers': 'Range'
      };
      
      // Handle range requests
      if (range && object.range) {
        headers['Content-Range'] = `bytes ${object.range.offset}-${object.range.offset + object.range.length - 1}/${object.size}`;
        headers['Content-Length'] = object.range.length.toString();
        
        return new Response(object.body, {
          status: 206,
          headers: headers
        });
      }
      
      // Full file response
      headers['Content-Length'] = object.size.toString();
      
      return new Response(object.body, {
        status: 200,
        headers: headers
      });
      
    } catch (error) {
      console.error('Error streaming track:', error);
      return new Response('Internal server error', { status: 500 });
    }
  }
};
'''
    
    worker_path = PROJECT_ROOT / "cloudflare-worker-dub-stream.js"
    worker_path.write_text(worker_code)
    print(f"\n✅ Generated worker code: {worker_path}")
    return True


def update_wrangler_toml():
    """Add R2 bucket to wrangler.toml."""
    wrangler_path = PROJECT_ROOT / "wrangler.toml"
    
    if not wrangler_path.exists():
        print("⚠️  wrangler.toml not found, creating...")
        # Create basic wrangler.toml
        content = f'''# Cloudflare Workers Configuration
name = "grokmon-dub-stream"
main = "cloudflare-worker-dub-stream.js"
compatibility_date = "2024-01-01"
account_id = "a33a705d5aebbca59de7eb146029869a"

[[r2_buckets]]
binding = "DUB_TRACKS"
bucket_name = "{BUCKET_NAME}"

[[routes]]
pattern = "grokandmon.com/api/playlist/dub/stream/*"
zone_id = "97e79defaee450aa65217568dbf2f835"
'''
        wrangler_path.write_text(content)
        print(f"✅ Created {wrangler_path}")
        return True
    
    # Read existing config
    content = wrangler_path.read_text()
    
    # Check if R2 bucket already configured
    if f'bucket_name = "{BUCKET_NAME}"' in content:
        print("ℹ️  R2 bucket already in wrangler.toml")
        return True
    
    # Add R2 bucket configuration
    if "[[r2_buckets]]" not in content:
        content += f"\n[[r2_buckets]]\nbinding = \"DUB_TRACKS\"\nbucket_name = \"{BUCKET_NAME}\"\n"
        wrangler_path.write_text(content)
        print(f"✅ Added R2 bucket to {wrangler_path}")
        return True
    
    return True


def main():
    """Main setup function."""
    print("=" * 60)
    print("Cloudflare R2 Dub Playlist Setup")
    print("=" * 60)
    
    # Check prerequisites
    if not check_wrangler():
        print("\n❌ Please install wrangler first:")
        print("   npm install -g wrangler")
        print("   wrangler login")
        sys.exit(1)
    
    # Create bucket
    if not create_r2_bucket():
        print("\n❌ Failed to create bucket")
        sys.exit(1)
    
    # Upload tracks
    if not upload_tracks():
        print("\n⚠️  Some uploads failed, but continuing...")
    
    # Generate worker code
    generate_worker_code()
    
    # Update wrangler.toml
    update_wrangler_toml()
    
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Deploy worker:")
    print("   wrangler deploy cloudflare-worker-dub-stream.js --name grokmon-dub-stream")
    print("\n2. Add route in Cloudflare Dashboard:")
    print("   Workers & Pages → Routes → Add route")
    print("   Pattern: grokandmon.com/api/playlist/dub/stream/*")
    print("   Worker: grokmon-dub-stream")
    print("\n3. Update API to use R2 URLs:")
    print("   Change /api/playlist/dub/stream/{filename} to use R2")
    print("\n4. Test:")
    print("   curl https://grokandmon.com/api/playlist/dub/stream/King%20Tubby%20-%20Dub%20From%20The%20Roots.mp3")


if __name__ == "__main__":
    main()
