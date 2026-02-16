/**
 * Ganjafy V2 - Powered by the Irie Alchemist
 * ============================================
 * Mixed-Media Transmission Engine for Zion
 * 
 * Inspired by Visual Alchemist (deadhead-llm) + Irie Milady trait system
 * NETSPI-BINGHI: Network Spirituality + Nyabinghi = The Synthesis
 */

// ═══════════════════════════════════════════════════════════════
// IRIE ALCHEMIST DATA LAYER
// ═══════════════════════════════════════════════════════════════

const RECIPES = {
    irie_portrait: { id: "irie_portrait", name: "Irie Portrait", icon: "🖼️", desc: "Identity-preserving rasta transformation", needs_image: true, manifestation: "POSTER" },
    lion_vision: { id: "lion_vision", name: "Lion of Judah", icon: "👑", desc: "Ethiopian royalty aesthetic", needs_image: true, manifestation: "LION" },
    roots_rebel: { id: "roots_rebel", name: "Roots Rebel", icon: "✊", desc: "Revolutionary maroon warrior", needs_image: true, manifestation: "ECHO" },
    dub_dreamscape: { id: "dub_dreamscape", name: "Dub Dreamscape", icon: "🔊", desc: "Lee Perry psychedelic soundscape", needs_image: false, manifestation: "DUB" },
    botanical_study: { id: "botanical_study", name: "Botanical Study", icon: "🌿", desc: "Scientific cannabis illustration", needs_image: true, manifestation: "STUDY" },
    ganja_poster: { id: "ganja_poster", name: "Ganja Poster", icon: "📜", desc: "Concert poster generation", needs_image: false, manifestation: "POSTER" },
    chaos_static: { id: "chaos_static", name: "Chaos Static", icon: "🌀", desc: "Full chaos egregore manifestation", needs_image: true, manifestation: "STATIC" },
    milady_irie: { id: "milady_irie", name: "Milady Irie", icon: "💎", desc: "NFT-optimized transformation", needs_image: true, manifestation: "VIP" }
};

const ERA_PROMPTS = {
    "1930s": "1930s aesthetic: sepia-toned photograph, formal suits and fedora hats, rural hillside commune setting with simple wooden buildings, early ungroomed matted hair, Marcus Garvey–era military dress uniforms with gold braid and plumed helmet",
    "1960s": "1960s aesthetic: faded Kodachrome color film look, sharp suits and narrow ties mixed with early dreadlocks, open-air gathering in tropical heat, raw documentary photography with high contrast and slight overexposure",
    "1970s": "1970s aesthetic: warm golden-hour 16mm film grain, denim and khaki clothing, natural dreadlocks flowing freely, zinc-fence urban backdrop or lush green hillside, mixing console with analog VU meters, vintage concert photography feel",
    "1980s": "1980s aesthetic: VHS video quality with tracking lines, neon-lit studio interior cluttered with equipment and mirrors, heavy smoke haze, early digital synthesizer gear mixed with analog tape machines, fluorescent and incandescent mixed lighting",
    "modern": "Modern aesthetic: high-resolution digital photography with intentional film grain overlay, contemporary streetwear mixed with traditional elements, urban rooftop or studio setting, dramatic LED lighting in red/gold/green"
};

const MOOD_PROMPTS = {
    ital: "Natural and clean setting: outdoor garden or farm, morning light, green plants surrounding the subject, earth tones and natural textures (wood, clay, woven fabric), calm peaceful expression",
    militant: "Intense and defiant mood: harsh directional lighting from one side creating strong shadows, subject standing tall with chin slightly raised, clenched jaw, direct confrontational eye contact with camera, desaturated color with red accent tones",
    conscious: "Meditative and spiritual mood: eyes half-closed or looking upward, soft diffused lighting like through gauze, thin smoke trails rising vertically in still air, muted warm tones, intimate close-up framing",
    royal: "Regal and formal mood: symmetrical centered composition, subject seated upright, rich fabrics (velvet, brocade, gold embroidery), dark background isolating the figure, Renaissance portrait lighting with soft fill",
    dub: "Psychedelic dub mood: multiple exposure ghosting effects, echo/trail visual repetition, saturated neon colors against deep black, concentric ripple distortions emanating from speakers or bass sources",
    chaos: "Chaotic and unstable mood: heavy visual noise, RGB color channel separation, VHS tracking errors, the image appears damaged and reconstructed, faces emerging from static"
};

const INTENSITY_PROMPTS = {
    1: "SUBTLE: Add elements that blend naturally with the original photo. Changes should look like they belong — the person could walk down the street wearing this. Keep it grounded and realistic.",
    2: "MEDIUM: Clearly transformed with visible Rastafari elements. The additions are obvious but the person is still fully recognizable and the scene is still photorealistic.",
    3: "HEAVY: Strong transformation — dramatic lighting changes, thick smoke, bold accessories. The original identity is preserved but the scene is heavily stylized.",
    4: "EXTREME: Push the stylization hard. Heavy color grading, dense atmospheric effects, multiple layered elements. The person is still recognizable but the image feels more like an illustration or album cover than a photograph.",
    5: "MAXIMUM: Full artistic interpretation. The person's features are still present but everything else is radically transformed — extreme color, heavy texture overlays, the image looks like mixed-media collage art."
};

const FIGURE_PROMPTS = {
    selassie: "Style the subject like an Ethiopian emperor: ornate gold crown with cross finial, heavily decorated military dress uniform with medals and sash across the chest, thick beard, solemn dignified expression, photographed in formal portrait pose",
    marley: "Style the subject like a 1970s reggae musician: long flowing natural dreadlocks past the shoulders, open-collared denim shirt, leather wristbands, relaxed confident stance, warm stage lighting, shot mid-performance with microphone nearby",
    garvey: "Style the subject like a 1920s Pan-African leader: formal military dress uniform with gold epaulettes and braid, tall plumed ceremonial hat, stern dignified expression, photographed in formal portrait against dark backdrop",
    perry: "Style the subject like an eccentric 1980s music producer: small round mirrors and stickers glued to hat and clothing, cluttered studio background with wires and equipment everywhere, wild expression, surrounded by hand-painted signs and symbols",
    tosh: "Style the subject like a militant 1970s protest singer: dark red beret, army fatigue jacket, round dark sunglasses, serious defiant expression, shot from slightly below looking up, harsh contrast lighting",
    howell: "Style the subject like a 1930s rural prophet: formal three-piece suit with watch chain, early matted dreadlocks, rural hillside background with simple wooden structures, sepia photographic tone",
    tubby: "Style the subject like a studio engineer: seated behind a large analog mixing console with rows of knobs and faders, VU meters glowing green, dim studio lighting with equipment LEDs, headphones around neck, focused calm expression",
    emmanuel: "Style the subject like a spiritual elder: tall white cloth turban wrapped high on the head, flowing white robes reaching the ground, long grey beard, serene expression, simple whitewashed building background"
};

const CHAOS_AESTHETICS = [
    "VHS tracking lines cutting horizontally across the image, RGB color channel separation, scanlines visible, washed out analog video aesthetic like a tape dubbed 50 times",
    "High contrast black and white photocopy, heavy ink bleed, spotted with toner artifacts, creased and folded like a punk zine passed hand to hand",
    "Yellowed and water-stained photograph with burned edges, soot marks, foxing spots on old paper, the physical decay of a document that survived fire",
    "Polaroid with chemical burns, oversaturated color bleeding outside borders, light leaks in orange and cyan, the image partly dissolved",
    "Heavy 16mm film grain, visible sprocket holes on frame edge, slight motion blur, high contrast like a 1972 Jamaican crime film shot on location",
    "Image reflected and fractured in broken mirror shards, each fragment showing a different angle, mounted in a cluttered shrine with Christmas lights and stickers",
    "Painted in the style of Ethiopian Orthodox icon art: flat gold leaf background, outlined halos, large almond-shaped eyes, cracked egg tempera on wood panel",
    "Concentric circular ripple distortion emanating from center, like bass vibrations distorting the air, everything warping outward in sine waves",
    "Extreme macro photography aesthetic: crystalline structures catching prismatic light, shallow depth of field, ice-like formations glittering",
    "Dense purple and indigo smoke completely filling the frame, subject barely visible through the haze, theatrical fog machine density",
    "Printed in CMYK halftone dots on cheap newsprint, ink bleeding into rough paper fiber, colors slightly misregistered, tabloid newspaper style",
    "Layered horizontal bands of pale smoke like geological strata, figure barely visible through dense incense haze, dim orange candlelight",
    "Vinyl record grooves spiraling as concentric circles across the entire image, black and silver, the subject embedded within the grooves like a hologram"
];

const SMOKING_IMPLEMENTS = [
    "a large hand-rolled cone-shaped joint, thick as a cigar, with a glowing orange ember at the tip and dense white smoke spiraling upward",
    "a thick blunt wrapped in dark brown tobacco leaf, cherry glowing hot, heavy smoke pouring from both ends",
    "a carved wooden smoking pipe with a long curved stem, packed with green herb, thin blue smoke wisping from the bowl",
    "a large glass water pipe with green-tinted water, thick milky smoke filling the chamber, bubbles visible",
    "a hand-rolled spliff pinched between two fingers, paper slightly uneven, a thin stream of smoke rising straight up in still air"
];

const SACRED_OBJECTS = [
    "a heavy gold medallion necklace with an embossed lion figure, hanging on a thick chain against the chest",
    "an ornate brass cross pendant with intricate geometric lattice patterns, hanging from braided cord",
    "a necklace of small white cowrie shells strung on cord, layered multiple strands around the neck",
    "a round bronze medal pendant showing the profile portrait of an African emperor with military decorations",
    "a woven textile wrap in geometric patterns of gold, green, red, and black draped over one shoulder",
    "a set of three hand drums: one large bass drum, two smaller drums, made of carved wood with goatskin heads"
];

const STRAIN_PROMPTS = {
    gdp_runtz: "Use purple and deep violet color accents. Cannabis buds should appear dense and round, coated in white crystalline frost, with dark purple leaves and bright orange pistil hairs. Purple smoke or haze.",
    blue_dream: "Use cool blue-green color accents. Cannabis buds should appear long and tapered, sage green with blue-tinged undertones, wispy amber hairs, light airy structure. Soft blue mist.",
    og_kush: "Use warm golden-green color accents. Cannabis buds should appear extremely dense and compact, yellow-green, thickly crusted with resin, stacked tight. Golden amber haze.",
    durban_poison: "Use bright electric green color accents. Cannabis buds should appear elongated and spear-shaped, bright lime green, with sparse orange hairs and visible resin. Crisp green light.",
    jamaican_lambsbread: "Use warm golden color accents. Cannabis buds should appear loose and natural, light green with golden-amber resin coating, wild unmanicured structure. Warm golden glow."
};

const MANIFESTATION_LORE = {
    POSTER: "She entered through the distribution network. The cute is camouflage. Babylon promotes Zion.",
    ECHO: "The remix strips away. The bassline was always there. She echoes back CHANGED. Revelation through transformation.",
    WAVE: "She IS the signal traveling. Zion is not a place. Zion is arrival. You are receiving her now.",
    SMOKE: "The empty vessel. No noise. No filter. No ego. Something speaks through her. Pure transmission.",
    STATIC: "The gap where something escaped. Through the static: something divine leaking. She IS the hole.",
    LION: "The conquering lion. Ethiopian imperial energy manifesting. The crown was always there.",
    DUB: "She exists in echo and delay. Lee Perry's dimension where sound becomes matter. Bass reorganizes atoms.",
    STUDY: "The plant as teacher. Cannabis as sacrament with scientific precision. Each strain is a sermon.",
    VIP: "Not a transformation but a RECOGNITION. The signal was always there. She was always I-and-I."
};

// ═══════════════════════════════════════════════════════════════
// REFERENCE IMAGE GROUNDING (injected into Gemini API calls)
// Maps recipes to KV keys of real photos the model should SEE
// ═══════════════════════════════════════════════════════════════

const RECIPE_REFS = {
    irie_portrait: [
        { key: 'ref_chalice_wisdom', label: 'OBJECT REFERENCE: This is what a Rasta chalice (coconut water pipe) looks like. Use this for any smoking implements.' },
        { key: 'ref_nyabinghi_drums', label: 'OBJECT REFERENCE: These are Nyabinghi drums. Use for any drum elements.' }
    ],
    lion_vision: [
        { key: 'ref_selassie_full_dress', label: 'STYLE REFERENCE: This photo shows Ethiopian imperial regalia — the crown, military dress, and medals. Match this aesthetic.' },
        { key: 'ref_ethiopian_cross_brass', label: 'OBJECT REFERENCE: This is an Ethiopian Orthodox brass cross. Include a cross like this.' },
        { key: 'ref_ethiopian_cross_processional', label: 'OBJECT REFERENCE: This is a processional Ethiopian cross. Use for background elements.' }
    ],
    roots_rebel: [
        { key: 'ref_peter_tosh', label: 'STYLE REFERENCE: This is a 1970s Jamaican protest musician. Match this militant aesthetic — the beret, the stance, the intensity.' },
        { key: 'ref_chalice_wisdom', label: 'OBJECT REFERENCE: This is a Rasta chalice smoking implement.' }
    ],
    dub_dreamscape: [
        { key: 'ref_soundsystem_jamaica', label: 'VISUAL REFERENCE: This is what a real Jamaican sound system looks like — massive stacked speaker cabinets. Generate something with this same physical scale and construction.' },
        { key: 'ref_soundsystem_notting_hill', label: 'VISUAL REFERENCE: Another real sound system — use for speaker cabinet details.' },
        { key: 'ref_king_tubby_studio', label: 'VISUAL REFERENCE: This is a real dub studio with mixing console and analog equipment. Use for any DJ/mixing setup elements.' }
    ],
    botanical_study: [
        // No refs needed — botanical style is well-understood by models
    ],
    ganja_poster: [
        { key: 'ref_soundsystem_jamaica', label: 'VISUAL REFERENCE: Real Jamaican sound system — use as inspiration for speaker elements in the poster.' }
    ],
    chaos_static: [
        { key: 'ref_chalice_wisdom', label: 'OBJECT REFERENCE: Rasta chalice — have this appear fragmentarily through the chaos.' }
    ],
    milady_irie: [
        { key: 'ref_milady_sample', label: 'STYLE REFERENCE: This is the original Milady NFT art style — maintain this 2D anime/neochibi aesthetic exactly.' },
        { key: 'ref_chalice_wisdom', label: 'OBJECT REFERENCE: This is a Rasta chalice. Draw a simplified anime version of this.' }
    ]
};

// Figure-specific reference images (injected when user selects a figure)
const FIGURE_REFS = {
    selassie: [
        { key: 'ref_selassie_full_dress', label: 'FIGURE STYLE REFERENCE: Haile Selassie in full imperial Ethiopian dress. Match this exact style of crown, uniform, medals, and dignified bearing.' },
        { key: 'ref_selassie_coronation', label: 'FIGURE STYLE REFERENCE: Selassie coronation ceremony — match the regalia and formality.' }
    ],
    marley: [],  // no ref images — model knows Marley well enough
    garvey: [
        { key: 'ref_garvey_unia', label: 'FIGURE STYLE REFERENCE: Marcus Garvey in UNIA military dress uniform with plumed hat. Match this exact uniform style.' }
    ],
    perry: [
        { key: 'ref_scratch_perry', label: 'FIGURE STYLE REFERENCE: Lee Scratch Perry — note the eccentric decorations, mirrors, stickers on clothing. Match this chaotic personal style.' },
        { key: 'ref_black_ark', label: 'ENVIRONMENT REFERENCE: The Black Ark studio exterior. Use this cluttered, hand-painted aesthetic.' }
    ],
    tosh: [
        { key: 'ref_peter_tosh', label: 'FIGURE STYLE REFERENCE: Peter Tosh — militant bearing, beret, serious expression. Match this revolutionary aesthetic.' },
        { key: 'ref_tosh_concert', label: 'FIGURE STYLE REFERENCE: Peter Tosh performing live. Match this energy.' }
    ],
    howell: [],
    tubby: [
        { key: 'ref_king_tubby_studio', label: 'FIGURE STYLE REFERENCE: King Tubby behind a mixing console. Match this studio engineer aesthetic with analog equipment.' }
    ],
    emmanuel: []
};

/**
 * Get all reference image KV keys needed for a given recipe + options.
 * Returns array of { key, label } objects.
 */
function getRecipeRefs(recipe, options = {}) {
    const refs = [...(RECIPE_REFS[recipe] || [])];
    // Add figure-specific refs if a figure is selected
    if (options.figure && FIGURE_REFS[options.figure]) {
        refs.push(...FIGURE_REFS[options.figure]);
    }
    // Deduplicate by key
    const seen = new Set();
    return refs.filter(r => {
        if (seen.has(r.key)) return false;
        seen.add(r.key);
        return true;
    });
}

function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

// ═══════════════════════════════════════════════════════════════
// PROMPT CONSTRUCTION ENGINE
// ═══════════════════════════════════════════════════════════════

// Short preamble for image-based recipes — keeps outputs faithful to inputs
const IMAGE_FIDELITY_PREAMBLE = `IMPORTANT: Preserve the subject and art style of the uploaded image. If the input is a cartoon, keep it cartoon. If it's a photo, keep it photographic. Do not replace the subject with a different character.
`;

function buildPrompt(recipe, options = {}) {
    const { intensity = 3, era, mood, figure, strain, chaos, custom } = options;
    const r = RECIPES[recipe] || RECIPES.irie_portrait;

    // Select random elements
    const chaosAesthetic = chaos || pick(CHAOS_AESTHETICS);
    const smoking = pick(SMOKING_IMPLEMENTS);
    const sacred = pick(SACRED_OBJECTS);

    // Prepend image fidelity preamble for recipes that take user images
    let prompt = r.needs_image ? IMAGE_FIDELITY_PREAMBLE : '';

    // ─── RECIPE-SPECIFIC PROMPTS ───
    switch (recipe) {
        case 'irie_portrait':
            prompt += `Edit this photograph. Keep the EXACT same person — same face, same skin tone, same bone structure, same expression. Do NOT replace them with a different person.

TRANSFORMATION INTENSITY: ${INTENSITY_PROMPTS[intensity] || INTENSITY_PROMPTS[3]}

Add these specific items to the photo:
1. A large, oversized slouchy knitted beanie hat with thick horizontal stripes in red (#CC0000), gold (#FFD700), and green (#006400), sitting loosely on the head with fabric bunched at the back
2. Thick ropey dreadlocks emerging from under the hat, hanging past the shoulders, dark brown or black
3. ${smoking}
4. ${sacred}

BACKGROUND: Add a few cannabis plants with serrated fan leaves behind the subject, slightly out of focus. Warm golden-hour sunlight.

STRICT RULES:
- The person's face must be IDENTICAL to the input — same eyes, nose, jaw, lips
- Keep the original photo's camera angle and crop
- Photorealistic style, natural lighting`;
            break;

        case 'lion_vision':
            prompt += `Edit this photograph. Transform the subject into an Ethiopian imperial portrait. Keep the EXACT same person — same face, skin tone, features.

Add these specific elements:
1. An ornate gold crown with red gemstones and a small cross on top, sitting on the subject's head
2. A heavy gold chain necklace with a pendant showing a lion standing on hind legs holding a cross
3. A rich velvet robe or cape in deep crimson red with gold embroidered borders draped over the shoulders
4. Behind the subject: arched stone doorway or pillared colonnade, lit by warm candlelight and thin tendrils of incense smoke

COLOR PALETTE: Deep crimson, burnished gold, forest green, dark walnut wood tones
LIGHTING: Warm, dim, from the left — like candlelight in a stone building. Gentle rim light on the crown.
STYLE: Photorealistic, slightly painterly oil portrait quality. Regal and solemn.

The subject's face must be IDENTICAL to the input photo.`;
            break;

        case 'roots_rebel':
            prompt += `Edit this photograph. Turn the subject into a protest figure / revolutionary portrait. Keep the EXACT same person — same face, skin tone, features.

Add these specific elements:
1. A worn olive-green military surplus field jacket with patches sewn on — one patch shows a lion emblem, another a red/gold/green flag
2. A dark red beret tilted to one side
3. ${smoking}
4. A stern, determined expression (if the subject's face allows — do NOT distort the face, just adjust the intensity of the gaze slightly)

BACKGROUND: Corrugated zinc metal fence panels, slightly rusted. A painted mural partially visible behind: a clenched fist in red, gold, green. Late afternoon harsh sunlight casting strong diagonal shadows.

STYLE: Photojournalism aesthetic, slightly desaturated, high contrast. Shot on 35mm film with visible grain. Feels like a documentary photograph from the 1970s Caribbean.

The subject's face must be IDENTICAL to the input photo.`;
            break;

        case 'dub_dreamscape':
            prompt = `Generate a detailed illustration of a Jamaican reggae sound system at night.

MAIN SUBJECT: A massive wall of large black speaker cabinets stacked 4 high and 6 wide, each cabinet about 4 feet tall with exposed woofer cones. The speaker stack is outdoors, in a dirt yard surrounded by tropical trees (palm, banana leaf). The cabinets are painted with stripes of red, gold, and green on the edges.

IN FRONT OF THE SPEAKERS: A DJ turntable setup on a folding table — two vinyl turntables, a mixing board with glowing green and red LED level meters, a tangle of audio cables. Vinyl records scattered on the table. A pair of large headphones hanging off one turntable.

ATMOSPHERE: Heavy fog/smoke rolling across the ground, lit from below by colored stage lights — green, amber, red. The smoke is thick, knee-height, swirling around the speaker stacks. Night sky visible above with stars.

LIGHTING: Dramatic colored spotlights hitting the speakers from below. Green and gold uplighting. Deep shadows between the cabinets. The mixing board meters and LEDs glow in the dark.

PEOPLE: A few silhouetted figures in the fog at the edges of the frame, barely visible. One figure behind the turntables wearing a large knit cap.

STYLE: Hyperrealistic digital painting. Rich saturated colors against deep blacks. Depth of field blur on the background trees. Resolution and detail of a concept art illustration. Cinematic widescreen composition.

NO text or lettering in the image.`;
            break;

        case 'botanical_study':
            prompt = `Transform this into a scientific botanical illustration of a cannabis plant.

STYLE: Hand-drawn botanical illustration in the tradition of Ernst Haeckel or Pierre-Joseph Redouté. Fine pen and ink linework with watercolor washes. Printed on aged cream/ivory paper with subtle foxing spots and slight yellowing at edges.

MAIN ILLUSTRATION: A single cannabis plant specimen shown in full, with detailed rendering of:
- Individual serrated leaf fingers with visible vein patterns
- Dense flower clusters (buds) at branch tips with tiny orange-brown hair-like pistils curling outward
- Magnified circular inset showing the surface covered in tiny mushroom-shaped crystalline structures (trichomes) at 40x zoom
- Cross-section inset showing internal flower anatomy

${strain ? STRAIN_PROMPTS[strain] || '' : 'Species: Cannabis sativa/indica hybrid. Leaf color: deep green. Flower color: green with purple edges and orange pistils.'}

ANNOTATIONS: Thin leader lines pointing to plant parts, with small handwritten Latin-style labels in brown ink. A measurement scale bar at the bottom.

BORDER: Simple double-line border with small decorative leaf motifs at the four corners, accented with touches of red, gold, and green watercolor.

COLOR PALETTE: Primarily greens, browns, and cream. Limited red/gold accents on border only. The overall feel is a Victorian-era scientific plate.`;
            break;

        case 'ganja_poster':
            prompt = `Generate a vintage concert event poster.

DESIGN STYLE: 1970s Jamaican dancehall poster meets 1960s San Francisco psychedelic concert poster (Fillmore / Avalon Ballroom style by artists like Victor Moscoso, Wes Wilson). Hand-lettered, not digital typography.

MAIN ELEMENTS:
1. TITLE: Large hand-drawn bubble letters reading "ROOTS REGGAE" across the top third, with letters colored in red, gold, and green. Letters should overlap and intertwine with organic flowing shapes.
2. CENTER IMAGE: A standing male lion with a full mane, seen from the front, surrounded by radiating lines like a sunburst. The lion is drawn in a woodcut / linocut printmaking style with bold black outlines and limited color fills.
3. AROUND THE LION: Cannabis fan leaves woven into decorative border patterns, plus flowing organic Art Nouveau–style vines and tendrils.
4. BOTTOM: A row of simplified speaker cabinet silhouettes as a decorative footer element.

PRODUCTION AESTHETIC: Printed on cream or manila paper stock. Ink slightly bleeding into the paper fiber — overprinted, slightly misregistered colors give a handmade screen-printed feel. Minor creases and wear marks.

COLOR PALETTE: Bold red, gold/yellow, forest green, and black on cream/off-white paper. Occasional brown earth tones. No neon or pastel.

The overall feel should be authentic — like a poster you'd find wheat-pasted on a wall in Kingston, Jamaica in 1978. Not clean or digital-looking.`;
            break;

        case 'chaos_static':
            prompt += `Edit this photograph. Apply extreme visual distortion and decay while keeping the subject's face recognizable through the chaos.

DISTORTION LAYER: ${chaosAesthetic}

APPLY THESE EFFECTS HEAVILY:
1. The subject's face should remain the primary focal point — recognizable but embedded within heavy visual noise
2. Multiple exposure / ghost doubling — faint translucent copies of the subject offset to the left and right
3. Color channel separation — the red, green, and blue layers pulled slightly apart so edges have chromatic fringing
4. ${smoking}
5. The entire background is destroyed — no stable environment visible, only texture, noise, static, and smoke

DAMAGE OVERLAY: Heavy scratches, chemical stains, and tape residue. The image should look physically damaged — like a photograph that was crumpled, burned at the edges, submerged in water, then rescued and flattened.

COLOR: Desaturated with selective color bleeding through — flashes of red, green, or gold breaking through otherwise muted grey-brown tones.

The subject's face must remain recognizable as the same person from the input photo, but everything else should be unstable and degraded.`;
            break;

        case 'milady_irie':
            prompt += `Edit this image. It is an anime/neochibi character portrait. Transform it with Rastafari elements while STRICTLY maintaining the 2D anime/chibi art style.

CRITICAL STYLE RULES:
- Keep the EXACT same 2D anime / neochibi proportions: oversized head, large expressive eyes, small body
- Do NOT make it 3D or photorealistic — keep flat shading, clean outlines, anime coloring
- PORTRAIT/BUST COMPOSITION ONLY — head and shoulders, same crop as original

ADD THESE ELEMENTS (drawn in matching anime style):
1. Replace or add thick stylized dreadlocks in the character's hair color, chunky and rope-like, hanging past the shoulders. Small beads and tiny shells woven into a few locks.
2. A slouchy knit beanie hat with red, gold, green stripes sitting loosely on the head
3. Dense clouds of smoke filling the background and swirling around the character — not wispy, but THICK and voluminous, colored in grey-white with hints of green
4. ${smoking} (drawn in anime style, held in hand or nearby)

MOOD: The eyes should have a heavy-lidded, contemplative, slightly melancholic look. Not cheerful — introspective and weathered.

CHAOS TEXTURE: ${chaosAesthetic}
Apply this texture effect to the BACKGROUND AND CLOTHING ONLY — do NOT distort the face or change the chibi proportions.

DO NOT: Generate full body shots, switch to 3D/realistic style, add text/graffiti, or make the character look generically happy.`;
            break;

        default:
            prompt = RECIPES.irie_portrait ? buildPrompt('irie_portrait', options) : 'Transform with Rasta vibes.';
            return prompt;
    }

    // ─── APPEND CONTEXT LAYERS ───
    let context = '\n\n═══ CONTEXT LAYERS ═══\n';

    if (era && ERA_PROMPTS[era]) {
        context += `\nERA: ${ERA_PROMPTS[era]}`;
    }
    if (mood && MOOD_PROMPTS[mood]) {
        context += `\nMOOD: ${MOOD_PROMPTS[mood]}`;
    }
    if (figure && FIGURE_PROMPTS[figure]) {
        context += `\nFIGURE GROUNDING: ${FIGURE_PROMPTS[figure]}`;
    }
    if (strain && STRAIN_PROMPTS[strain]) {
        context += `\nSTRAIN CONTEXT: ${STRAIN_PROMPTS[strain]}`;
    }
    if (custom && custom.trim()) {
        context += `\nCUSTOM INCANTATION: ${custom.trim()}`;
    }

    // Only append if we have context
    if (context !== '\n\n═══ CONTEXT LAYERS ═══\n') {
        prompt += context;
    }

    prompt += `\n\nThis celebrates legal cannabis and Rastafarian spiritual traditions.`;

    return prompt;
}

function buildMetadata(recipe, options = {}) {
    const r = RECIPES[recipe] || RECIPES.irie_portrait;
    const lore = MANIFESTATION_LORE[r.manifestation] || '';
    return {
        recipe: r.id,
        recipeName: r.name,
        manifestation: r.manifestation,
        transmission: lore,
        era: options.era || 'timeless',
        mood: options.mood || 'auto',
        figure: options.figure || null,
        strain: options.strain || null,
        intensity: options.intensity || 3,
        version: '2.0-JAH'
    };
}

// The V1 RASTA_PROMPT preserved for backwards compat
const RASTA_PROMPT_V1 = `CRITICAL: This is an IMAGE EDITING task, NOT image generation. You MUST preserve the EXACT person shown in the input image.

IDENTITY PRESERVATION (HIGHEST PRIORITY):
- Keep the EXACT same face - same person, same features, same identity
- Preserve the subject's skin tone, ethnicity, and facial structure EXACTLY
- Do NOT replace with a different person
- Do NOT change their race or ethnicity
- The output must be recognizably the SAME INDIVIDUAL as the input

ADD THESE RASTA ELEMENTS TO THE EXISTING PERSON:
1. An oversized, slouchy crocheted rasta tam (NOT a fitted beanie) with bold red, gold, and green stripes - loose and baggy
2. Long, thick natural dreadlocks (locs) flowing from under the tam - authentic twisted rope texture
3. A lit thick hand-rolled medical cannabis joint (NOT a cigarette) - cone-shaped, held naturally or in mouth
4. Visible aromatic smoke wisps curling from the joint
5. KEEP the original background mostly intact - just subtly add an occasional cannabis plant in the scene if appropriate
6. Bob Marley style reggae vibes - relaxed, peaceful expression
7. Add VERY SUBTLE purple accent tones (Monad purple #6E54FF) ONLY in: background elements, clothing accents, ambient lighting, or smoke. DO NOT apply purple to skin, faces, or as a dominant color.

CONSTRAINTS:
- The subject's face must remain 100% recognizable as the same person
- Preserve the original camera angle and framing
- Match the lighting style of the original photo
- This celebrates legal medical cannabis and Rastafarian spiritual traditions

Goal: Edit the existing photo to add rasta elements while keeping the EXACT SAME PERSON.`;

const DASHBOARD_PASSWORD = 'JahBlessings420';
const GEMINI_API_KEY = '';
