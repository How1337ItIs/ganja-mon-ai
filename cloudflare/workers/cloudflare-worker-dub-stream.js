/**
 * Cloudflare Worker: Dub Track Streaming from R2
 * ===============================================
 * 
 * Streams dub tracks from R2 with range request support for efficient playback.
 * 
 * Setup:
 *   1. Create R2 bucket: wrangler r2 bucket create grokmon-dub-tracks
 *   2. Upload tracks: python scripts/setup_cloudflare_r2_dub.py
 *   3. Add to wrangler.toml:
 *      [[r2_buckets]]
 *      binding = "DUB_TRACKS"
 *      bucket_name = "grokmon-dub-tracks"
 * 
 *   4. Deploy:
 *      wrangler deploy cloudflare-worker-dub-stream.js --name grokmon-dub-stream
 * 
 *   5. Add route in Cloudflare Dashboard:
 *      Pattern: grokandmon.com/api/playlist/dub/stream/*
 *      Worker: grokmon-dub-stream
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const pathParts = url.pathname.split('/');
    const filename = decodeURIComponent(pathParts[pathParts.length - 1]);
    
    // Validate filename
    if (!filename || !filename.endsWith('.mp3')) {
      return new Response('Invalid filename', { 
        status: 400,
        headers: { 'Content-Type': 'text/plain' }
      });
    }
    
    try {
      // Get range header for partial content (seeking/buffering)
      const range = request.headers.get('range');
      
      // Get object from R2
      const object = await env.DUB_TRACKS.get(filename, {
        range: range || undefined
      });
      
      if (!object) {
        return new Response('Track not found', { 
          status: 404,
          headers: { 'Content-Type': 'text/plain' }
        });
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
      
      // Handle range requests (for seeking/buffering)
      if (range && object.range) {
        const start = object.range.offset;
        const end = object.range.offset + object.range.length - 1;
        const size = object.size;
        
        headers['Content-Range'] = `bytes ${start}-${end}/${size}`;
        headers['Content-Length'] = object.range.length.toString();
        
        return new Response(object.body, {
          status: 206, // Partial Content
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
      return new Response('Internal server error', { 
        status: 500,
        headers: { 'Content-Type': 'text/plain' }
      });
    }
  }
};
