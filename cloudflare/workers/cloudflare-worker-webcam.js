/**
 * Cloudflare Worker: Webcam Image Cache
 * ======================================
 *
 * Caches webcam images at the edge for instant global delivery.
 * Updates from origin every 30 seconds via cron trigger.
 *
 * Deployment:
 *   npm create cloudflare@latest grokmon-webcam
 *   wrangler deploy
 *
 * Setup:
 *   1. Create KV namespace: wrangler kv:namespace create WEBCAM_CACHE
 *   2. Add to wrangler.toml:
 *      [[kv_namespaces]]
 *      binding = "WEBCAM_CACHE"
 *      id = "your-kv-id"
 *
 *   3. Add cron trigger:
 *      [triggers]
 *      crons = ["* * * * *"]  # Every minute (Cloudflare minimum)
 *
 *   4. Set secret:
 *      wrangler secret put ORIGIN_URL
 *      # Value: http://chromebook.lan:8000 (or your actual origin)
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Health check endpoint
    if (url.pathname === '/health') {
      const lastUpdate = await env.WEBCAM_CACHE.get('last_update');
      const age = lastUpdate ? Math.floor((Date.now() - parseInt(lastUpdate)) / 1000) : null;

      return new Response(JSON.stringify({
        status: 'healthy',
        cache_age_seconds: age,
        worker_version: '1.0.0',
        last_update: lastUpdate ? new Date(parseInt(lastUpdate)).toISOString() : null
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Serve webcam image from cache
    if (url.pathname === '/api/webcam/latest' || url.pathname === '/') {
      // Get cached image
      const cachedImage = await env.WEBCAM_CACHE.get('webcam_latest', 'arrayBuffer');
      const lastUpdate = await env.WEBCAM_CACHE.get('last_update');

      if (!cachedImage) {
        return new Response('Webcam cache warming up...', {
          status: 503,
          headers: { 'Retry-After': '30' }
        });
      }

      const age = lastUpdate ? Math.floor((Date.now() - parseInt(lastUpdate)) / 1000) : 0;

      return new Response(cachedImage, {
        headers: {
          'Content-Type': 'image/jpeg',
          'Cache-Control': 'public, max-age=30, s-maxage=30',
          'X-Cache': 'HIT',
          'X-Frame-Age': `${age}s`,
          'X-Worker-Version': '1.0.0',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }

    // Fallback
    return new Response('Not Found', { status: 404 });
  },

  // Cron trigger to update cache from origin
  async scheduled(event, env, ctx) {
    try {
      // Fetch latest webcam image from origin
      const originUrl = env.ORIGIN_URL || 'http://chromebook.lan:8000';
      const response = await fetch(`${originUrl}/api/webcam/latest`, {
        headers: { 'User-Agent': 'Cloudflare-Worker-Webcam-Cache/1.0' }
      });

      if (!response.ok) {
        console.error(`Origin fetch failed: ${response.status} ${response.statusText}`);
        return;
      }

      // Store in KV
      const imageBuffer = await response.arrayBuffer();
      await env.WEBCAM_CACHE.put('webcam_latest', imageBuffer);
      await env.WEBCAM_CACHE.put('last_update', Date.now().toString());

      console.log(`Webcam cache updated successfully (${imageBuffer.byteLength} bytes)`);
    } catch (error) {
      console.error('Webcam cache update failed:', error);
    }
  }
};
