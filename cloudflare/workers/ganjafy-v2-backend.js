// Ganjafy V2 Backend Routes - Cloudflare Worker API handlers

// ═══════════════════════════════════════════════════════════════
// CLOUDFLARE WORKER - API ROUTES
// ═══════════════════════════════════════════════════════════════

export default {
    async fetch(request, env) {
        const url = new URL(request.url);
        const p = url.pathname;
        if (p === '/ganjafy' || p === '/ganjafy/') {
            return new Response(DASHBOARD_HTML, { headers: { 'Content-Type': 'text/html; charset=UTF-8' } });
        }
        if (p === '/ganjafy/api/login' && request.method === 'POST') return handleLogin(request, env);
        if (p === '/ganjafy/api/transform' && request.method === 'POST') return handleTransform(request, env);
        if (p === '/ganjafy/api/gallery') return handleGallery(request, env);
        if (p.startsWith('/ganjafy/api/image/')) return handleImageFetch(p, env);
        if (p === '/ganjafy/api/debug-refs') return handleDebugRefs(request, env);
        return new Response('Not found', { status: 404 });
    }
};

async function handleLogin(request, env) {
    try {
        const { password } = await request.json();
        if (password === (env.DASHBOARD_PASSWORD || DASHBOARD_PASSWORD)) {
            return Response.json({ sessionId: 'sess_' + crypto.randomUUID() });
        }
        return Response.json({ error: 'Wrong password!' }, { status: 401 });
    } catch (e) { return Response.json({ error: 'Invalid request' }, { status: 400 }); }
}

async function handleTransform(request, env) {
    try {
        const formData = await request.formData();
        const selectedModel = formData.get('model') || 'gemini-3-pro-image-preview';
        const userApiKey = formData.get('userApiKey');
        const apiProvider = formData.get('apiProvider') || 'gemini';
        const recipe = formData.get('recipe') || 'irie_portrait';
        const alchemyOpts = {
            intensity: parseInt(formData.get('intensity') || '3'),
            era: formData.get('era') || null,
            mood: formData.get('mood') || null,
            figure: formData.get('figure') || null,
            strain: formData.get('strain') || null,
            custom: formData.get('custom') || null
        };

        // V2: Collect all images dynamically (image_0, role_0, image_1, role_1, ...)
        const images = [];
        const ROLE_LABELS = {
            subject: 'PRIMARY SUBJECT IMAGE (transform this person/object)',
            character: 'CHARACTER REFERENCE IMAGE (include this person in the scene)',
            style_match: 'STYLE REFERENCE (match this art style)',
            color_palette: 'COLOR PALETTE REFERENCE (use these colors)',
            texture_ref: 'TEXTURE REFERENCE (apply this texture/pattern)',
            composition_ref: 'COMPOSITION REFERENCE (follow this layout)',
            background: 'BACKGROUND IMAGE (place subjects here)',
            environment: 'ENVIRONMENT REFERENCE (place subjects in this setting)',
            blend: 'BLEND/COMPOSITE IMAGE (merge with subjects)',
            inpaint: 'INPAINT TARGET (insert subjects into this scene)',
            object_ref: 'OBJECT REFERENCE (include this object)',
            pose_ref: 'POSE / BODY REFERENCE (use this pose)'
        };
        const imageCount = parseInt(formData.get('image_count') || '0');
        for (let i = 0; i < imageCount; i++) {
            const file = formData.get('image_' + i);
            const role = formData.get('role_' + i) || 'subject';
            if (file && file.size) {
                images.push({ file, role, label: ROLE_LABELS[role] || ('IMAGE INPUT #' + (i + 1)) });
            }
        }
        // Backward compat: if no indexed images, check legacy 'image' field
        if (images.length === 0) {
            const legacyFile = formData.get('image');
            if (legacyFile && legacyFile.size) images.push({ file: legacyFile, role: 'subject', label: 'PRIMARY SUBJECT IMAGE' });
        }

        const prompt = buildPrompt(recipe, alchemyOpts);
        const metadata = buildMetadata(recipe, alchemyOpts);
        metadata.imageCount = images.length;
        const apiKey = userApiKey || env.GEMINI_API_KEY;
        if (!apiKey) return Response.json({ error: 'No API key available' }, { status: 400 });

        // ─── REFERENCE IMAGE GROUNDING ─────────────────────────────
        // Fetch real photos from KV to show the model what cultural objects look like
        const refSpecs = getRecipeRefs(recipe, alchemyOpts);
        const refImages = [];
        console.log('REF GROUNDING: recipe=' + recipe + ' specs=' + refSpecs.length + ' keys=' + refSpecs.map(s => s.key).join(','));
        if (env.GANJAFY_GALLERY && refSpecs.length > 0) {
            const refFetches = refSpecs.map(async (spec) => {
                try {
                    const { value, metadata: refMeta } = await env.GANJAFY_GALLERY.getWithMetadata(spec.key, { type: 'arrayBuffer' });
                    console.log('REF FETCH: ' + spec.key + ' value=' + (value ? value.byteLength + 'B' : 'null') + ' meta=' + JSON.stringify(refMeta));
                    if (value && value.byteLength > 500) {
                        // Chunked base64 encoding to avoid stack overflow on large images
                        const bytes = new Uint8Array(value);
                        let binary = '';
                        const chunkSize = 8192;
                        for (let i = 0; i < bytes.length; i += chunkSize) {
                            binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
                        }
                        const base64 = btoa(binary);
                        const mimeType = refMeta?.mime || 'image/jpeg';
                        return { base64, mimeType, label: spec.label, key: spec.key };
                    }
                } catch (e) {
                    console.log('REF ERR: ' + spec.key + ' => ' + e.message);
                }
                return null;
            });
            const results = await Promise.all(refFetches);
            for (const r of results) {
                if (r) refImages.push(r);
            }
        }
        metadata.refCount = refImages.length;
        console.log('REF RESULT: loaded ' + refImages.length + ' reference images, keys=' + refImages.map(r => r.key).join(','));
        // ─── END REFERENCE IMAGE GROUNDING ─────────────────────────

        const recipeData = RECIPES[recipe];
        const needsImage = recipeData ? recipeData.needs_image : true;
        let imageData;

        if (selectedModel.startsWith('openrouter-')) {
            imageData = await callOpenRouter(apiKey, selectedModel, prompt, images, needsImage);
        } else if (selectedModel.startsWith('imagen-')) {
            imageData = await callImagen(apiKey, prompt);
        } else {
            imageData = await callGemini(apiKey, selectedModel, prompt, images, needsImage, refImages);
        }

        let saveStatus = 'disabled';
        if (env.GANJAFY_GALLERY && imageData) {
            try {
                const key = 'ganjafy_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
                const imgBuffer = Uint8Array.from(atob(imageData), c => c.charCodeAt(0));
                await env.GANJAFY_GALLERY.put(key, imgBuffer, { metadata: { timestamp: Date.now(), recipe, ...metadata } });
                saveStatus = 'saved';
            } catch (e) { saveStatus = e.message; }
        }
        return Response.json({ imageData, saveStatus, metadata });
    } catch (e) {
        console.error('Transform error:', e);
        return Response.json({ error: 'Transform failed: ' + e.message }, { status: 500 });
    }
}

async function callGemini(apiKey, model, prompt, images, needsImage, refImages) {
    // Map frontend model selector values to actual API model names
    // Only image-capable models: gemini-3-pro-image-preview, gemini-2.5-flash-image
    const MODEL_MAP = {
        'gemini-3-pro-image-preview': 'gemini-3-pro-image-preview',
        'gemini-2.5-flash-image-preview': 'gemini-2.5-flash-image',
        'gemini-2.0-flash': 'gemini-2.0-flash'
    };
    const modelName = MODEL_MAP[model] || model;
    const url = 'https://generativelanguage.googleapis.com/v1beta/models/' + modelName + ':generateContent?key=' + apiKey;
    const parts = [];

    // Helper: convert ArrayBuffer to base64 without stack overflow
    function arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        const chunkSize = 8192;
        for (let i = 0; i < bytes.length; i += chunkSize) {
            binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
        }
        return btoa(binary);
    }

    // 1. Inject reference images FIRST (visual grounding)
    if (refImages && refImages.length > 0) {
        for (const ref of refImages) {
            parts.push({ text: '[' + ref.label + ']:' });
            parts.push({ inline_data: { mime_type: ref.mimeType, data: ref.base64 } });
        }
    }

    // 2. Add user-uploaded images with their role labels
    if (images && images.length > 0) {
        for (const img of images) {
            parts.push({ text: '[' + img.label + ']:' });
            const arrayBuffer = await img.file.arrayBuffer();
            const base64 = arrayBufferToBase64(arrayBuffer);
            parts.push({ inline_data: { mime_type: img.file.type, data: base64 } });
        }
    }

    // 3. Add the text prompt last
    parts.push({ text: prompt });
    const res = await fetch(url, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contents: [{ parts }], generationConfig: { responseModalities: ['Text', 'Image'] } })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error?.message || 'Gemini API error (' + modelName + ')');
    for (const c of (data.candidates || [])) {
        for (const p of (c.content?.parts || [])) {
            // Gemini API may return either camelCase or snake_case
            if (p.inline_data?.data) return p.inline_data.data;
            if (p.inlineData?.data) return p.inlineData.data;
        }
    }
    // Log what we got for debugging
    const partInfo = [];
    for (const c of (data.candidates || [])) {
        for (const p of (c.content?.parts || [])) {
            if (p.text) partInfo.push('text:' + p.text.slice(0, 50));
            else if (p.inline_data) partInfo.push('inline_data:{mime:' + (p.inline_data.mime_type || '?') + ', hasData:' + !!(p.inline_data.data) + ', dataLen:' + (p.inline_data.data?.length || 0) + '}');
            else if (p.inlineData) partInfo.push('inlineData:{mime:' + (p.inlineData.mimeType || p.inlineData.mime_type || '?') + ', hasData:' + !!(p.inlineData.data) + ', dataLen:' + (p.inlineData.data?.length || 0) + '}');
            else partInfo.push('unknown:' + JSON.stringify(Object.keys(p)));
        }
    }
    const blockReason = data.candidates?.[0]?.finishReason || 'unknown';
    throw new Error('No image generated (model: ' + modelName + ', finishReason: ' + blockReason + ', parts: ' + partInfo.join(' | ').slice(0, 400) + ')');
}

async function callImagen(apiKey, prompt) {
    const url = 'https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key=' + apiKey;
    const res = await fetch(url, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instances: [{ prompt }], parameters: { sampleCount: 1 } })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error?.message || 'Imagen API error');
    if (data.predictions?.[0]?.bytesBase64Encoded) return data.predictions[0].bytesBase64Encoded;
    throw new Error('No image generated');
}

async function callOpenRouter(apiKey, model, prompt, images, needsImage) {
    const modelMap = {
        'openrouter-gemini-3-pro': 'google/gemini-2.0-flash-exp:free',
        'openrouter-gemini-2.5-flash': 'google/gemini-2.5-flash-preview',
        'openrouter-gemini-2.0-free': 'google/gemini-2.0-flash-exp:free',
        'openrouter-flux-pro': 'black-forest-labs/flux-1.1-pro',
        'openrouter-flux-max': 'black-forest-labs/flux-pro',
        'openrouter-flux-klein': 'black-forest-labs/flux-schnell'
    };
    const orModel = modelMap[model] || 'google/gemini-2.0-flash-exp:free';
    const isFlux = model.includes('flux');

    if (isFlux) {
        const res = await fetch('https://openrouter.ai/api/v1/images/generations', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + apiKey, 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: orModel, prompt, n: 1, size: '1024x1024' })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error?.message || 'FLUX error');
        if (data.data?.[0]?.b64_json) return data.data[0].b64_json;
        throw new Error('No image generated');
    }

    const content = [];
    // Add all images with role labels
    if (images && images.length > 0) {
        for (const img of images) {
            content.push({ type: 'text', text: '[' + img.label + ']:' });
            const arrayBuffer = await img.file.arrayBuffer();
            const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
            content.push({ type: 'image_url', image_url: { url: 'data:' + img.file.type + ';base64,' + base64 } });
        }
    }
    content.push({ type: 'text', text: prompt });
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + apiKey, 'Content-Type': 'application/json', 'HTTP-Referer': 'https://grokandmon.com', 'X-Title': 'Ganjafy V2' },
        body: JSON.stringify({ model: orModel, messages: [{ role: 'user', content }], response_format: { type: 'image' } })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error?.message || 'OpenRouter error');
    for (const choice of (data.choices || [])) {
        const msgContent = choice.message?.content;
        if (typeof msgContent === 'string' && msgContent.length > 1000) return msgContent;
        if (Array.isArray(msgContent)) {
            for (const part of msgContent) {
                if (part.type === 'image_url') {
                    const imgData = part.image_url?.url?.replace(/^data:image\/[^;]+;base64,/, '');
                    if (imgData) return imgData;
                }
            }
        }
    }
    throw new Error('No image in response');
}

async function handleGallery(request, env) {
    if (!env.GANJAFY_GALLERY) return Response.json({ images: [], total: 0 });
    try {
        const url = new URL(request.url);
        const cursor = url.searchParams.get('cursor') || undefined;
        const list = await env.GANJAFY_GALLERY.list({ limit: 50, cursor });
        // Filter out reference images (ref_ prefix) from gallery display
        const images = list.keys
            .filter(k => !k.name.startsWith('ref_'))
            .map(k => ({ name: k.name, metadata: k.metadata }))
            .slice(0, 20);
        const response = { images, total: list.keys.length };
        if (!list.list_complete && list.cursor) response.nextCursor = list.cursor;
        return Response.json(response);
    } catch (e) { return Response.json({ error: 'Gallery error: ' + e.message }, { status: 500 }); }
}

async function handleImageFetch(reqPath, env) {
    if (!env.GANJAFY_GALLERY) return new Response('Gallery not configured', { status: 500 });
    const key = reqPath.replace('/ganjafy/api/image/', '');
    // Don't serve reference images as gallery items
    if (key.startsWith('ref_')) return new Response('Not a gallery image', { status: 404 });
    try {
        const value = await env.GANJAFY_GALLERY.get(key, { type: 'arrayBuffer' });
        if (!value) return new Response('Image not found', { status: 404 });

        // Check if this is raw binary (PNG/JPEG) or old JSON format
        const firstByte = new Uint8Array(value)[0];

        if (firstByte === 0x7B) {
            // Starts with '{' — old JSON format: { id, timestamp, imageData (base64), prompt }
            const text = new TextDecoder().decode(value);
            const data = JSON.parse(text);
            if (data.imageData) {
                const binary = atob(data.imageData);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                // Detect content type from base64 header
                const contentType = data.imageData.startsWith('/9j/') ? 'image/jpeg' : 'image/png';
                return new Response(bytes, {
                    headers: { 'Content-Type': contentType, 'Cache-Control': 'public, max-age=86400', 'Access-Control-Allow-Origin': '*' }
                });
            }
            return new Response('No image data in record', { status: 404 });
        }

        // Raw binary image (new format) — detect type from magic bytes
        const magic = new Uint8Array(value.slice(0, 4));
        const contentType = (magic[0] === 0xFF && magic[1] === 0xD8) ? 'image/jpeg'
            : (magic[0] === 0x89 && magic[1] === 0x50) ? 'image/png'
                : 'image/png';
        return new Response(value, {
            headers: { 'Content-Type': contentType, 'Cache-Control': 'public, max-age=86400', 'Access-Control-Allow-Origin': '*' }
        });
    } catch (e) { return new Response('Error: ' + e.message, { status: 500 }); }
}

async function handleDebugRefs(request, env) {
    const url = new URL(request.url);
    const recipe = url.searchParams.get('recipe') || 'dub_dreamscape';
    const results = {};

    // 1. Check if getRecipeRefs works
    try {
        const specs = getRecipeRefs(recipe);
        results.specs = specs.map(s => ({ key: s.key, labelLen: s.label.length }));
    } catch (e) {
        results.specsError = e.message;
    }

    // 2. Check if KV is accessible
    results.kvAvailable = !!env.GANJAFY_GALLERY;

    // 3. Try to fetch a known key - multiple methods
    if (env.GANJAFY_GALLERY) {
        const testKey = 'ref_chalice_wisdom';

        // Try arrayBuffer
        try {
            const { value, metadata } = await env.GANJAFY_GALLERY.getWithMetadata(testKey, { type: 'arrayBuffer' });
            results.arrayBuffer = { found: !!value, size: value ? value.byteLength : 0, metadata };
        } catch (e) { results.arrayBufferError = e.message; }

        // Try text
        try {
            const val = await env.GANJAFY_GALLERY.get(testKey, { type: 'text' });
            results.text = { found: !!val, len: val ? val.length : 0, preview: val ? val.substring(0, 50) : null };
        } catch (e) { results.textError = e.message; }

        // Try stream
        try {
            const val = await env.GANJAFY_GALLERY.get(testKey, { type: 'stream' });
            results.stream = { found: !!val, type: typeof val };
        } catch (e) { results.streamError = e.message; }

        // Try default (no type)
        try {
            const val = await env.GANJAFY_GALLERY.get(testKey);
            results.default = { found: !!val, type: typeof val, len: val ? val.length : 0 };
        } catch (e) { results.defaultError = e.message; }

        // 4. List all ref_ keys
        try {
            const list = await env.GANJAFY_GALLERY.list({ prefix: 'ref_', limit: 50 });
            results.refKeys = list.keys.map(k => ({ name: k.name, metadata: k.metadata }));
        } catch (e) {
            results.listError = e.message;
        }
    }

    return Response.json(results, { headers: { 'Access-Control-Allow-Origin': '*' } });
}
