/**
 * Cloudflare Worker to serve R2 objects publicly
 * Routes: grokandmon.com/r2/* -> R2 bucket
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Only handle /r2/* paths
    if (!path.startsWith('/r2/')) {
      return new Response('Not Found', { status: 404 });
    }

    // Get the object key from the path (remove /r2/ prefix)
    const key = path.replace('/r2/', '');

    if (!key) {
      return new Response('No key specified', { status: 400 });
    }

    // Get the object from R2
    const object = await env.GANJAMON1.get(key);

    if (!object) {
      return new Response('Not Found', { status: 404 });
    }

    // Set appropriate headers
    const headers = new Headers();
    headers.set('Content-Type', object.httpMetadata?.contentType || 'application/octet-stream');
    headers.set('Cache-Control', 'public, max-age=31536000, immutable'); // 1 year cache
    headers.set('Access-Control-Allow-Origin', '*');

    // Add ETag for caching
    if (object.etag) {
      headers.set('ETag', object.etag);
    }

    return new Response(object.body, { headers });
  }
};
