/**
 * Cloudflare Worker: API Cache Layer
 * ====================================
 *
 * Caches API responses (sensors, AI, grow data) at the edge.
 * Reduces origin load by 90-95% during traffic spikes.
 *
 * Routes:
 *   /api/sensors/latest   → Cache 30s
 *   /api/ai/latest        → Cache 5min
 *   /api/grow/stage       → Cache 1min
 *   /api/devices/latest   → Cache 30s
 *   /api/token/metrics    → Cache 1min
 *   /api/stats            → Cache 5min
 *
 * Deployment:
 *   npm create cloudflare@latest grokmon-api
 *   wrangler deploy
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const cache = caches.default;

    // Define cache TTLs for different endpoints (in seconds)
    const cacheTTLs = {
      '/api/sensors/latest': 30,
      '/api/ai/latest': 300,        // 5 minutes
      '/api/grow/stage': 60,
      '/api/devices/latest': 30,
      '/api/token/metrics': 60,
      '/api/stats': 300,
      '/api/health': 10
    };

    // Check if this endpoint should be cached
    const ttl = cacheTTLs[url.pathname];

    if (!ttl) {
      // Not a cached endpoint, proxy to origin
      return fetch(request);
    }

    // Try to serve from cache
    let response = await cache.match(request);

    if (response) {
      // Cache hit - add header and return
      const newHeaders = new Headers(response.headers);
      newHeaders.set('X-Cache', 'HIT');
      newHeaders.set('X-Cache-TTL', `${ttl}s`);

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders
      });
    }

    // Cache miss - fetch from origin
    const originUrl = env.ORIGIN_URL || 'http://chromebook.lan:8000';
    const originRequest = new Request(`${originUrl}${url.pathname}`, {
      method: request.method,
      headers: request.headers
    });

    response = await fetch(originRequest);

    // Clone response for caching (can only read body once)
    const responseToCache = response.clone();

    // Only cache successful responses
    if (response.status === 200) {
      // Add cache headers
      const cacheHeaders = new Headers(responseToCache.headers);
      cacheHeaders.set('Cache-Control', `public, max-age=${ttl}, s-maxage=${ttl}`);
      cacheHeaders.set('X-Cache', 'MISS');
      cacheHeaders.set('X-Cache-TTL', `${ttl}s`);

      const cachedResponse = new Response(responseToCache.body, {
        status: responseToCache.status,
        statusText: responseToCache.statusText,
        headers: cacheHeaders
      });

      // Store in cache (fire and forget)
      ctx.waitUntil(cache.put(request, cachedResponse));

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: cacheHeaders
      });
    }

    // Don't cache errors
    const headers = new Headers(response.headers);
    headers.set('X-Cache', 'BYPASS');

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: headers
    });
  }
};
