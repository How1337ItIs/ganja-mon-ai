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


// ═══════════════════════════════════════════════════════════════
// HTML DASHBOARD (V2)
// ═══════════════════════════════════════════════════════════════

const DASHBOARD_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🌿 Ganjafy V2 - Powered by Irie Alchemist</title>
  <meta name="description" content="Transform any image with authentic Jamaican Rasta vibes - powered by the Irie Alchemist engine">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --rasta-red: #C8102E;
      --rasta-gold: #FFB81C;
      --rasta-green: #009639;
      --rasta-black: #0D0D0D;
      --bg-dark: #0a0f0a;
      --bg-card: #141a14;
      --text-primary: #f0f5f0;
      --text-secondary: #8fa88f;
      --text-muted: #5a6b5a;
      --rasta-gradient: linear-gradient(135deg, var(--rasta-green), var(--rasta-gold), var(--rasta-red));
      --glow-green: rgba(0, 150, 57, 0.4);
      --border-radius: 16px;
      --font-display: 'Permanent Marker', cursive;
      --font-body: 'Outfit', sans-serif;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: var(--font-body); background: var(--bg-dark); color: var(--text-primary); min-height: 100vh; }
    .screen { display: none; min-height: 100vh; }
    .screen.active { display: block; }
    .hidden { display: none !important; }

    /* ═══ LOGIN (preserved from V1) ═══ */
    .login-container {
      min-height: 100vh; display: flex; align-items: center; justify-content: center;
      background: radial-gradient(ellipse at 20% 80%, var(--glow-green) 0%, transparent 50%),
                  radial-gradient(ellipse at 80% 20%, rgba(255, 184, 28, 0.3) 0%, transparent 50%),
                  var(--bg-dark);
    }
    .login-card {
      background: var(--bg-card); border: 1px solid rgba(0, 150, 57, 0.3);
      border-radius: var(--border-radius); padding: 3rem; width: 100%; max-width: 420px;
      box-shadow: 0 0 60px rgba(0, 150, 57, 0.2), 0 20px 40px rgba(0, 0, 0, 0.5);
    }
    .login-header { text-align: center; margin-bottom: 2rem; }
    .login-header h1 {
      font-family: var(--font-display); font-size: 2.5rem;
      background: var(--rasta-gradient); -webkit-background-clip: text;
      -webkit-text-fill-color: transparent; background-clip: text;
    }
    .login-header .v2-badge {
      display: inline-block; background: linear-gradient(135deg, #6E54FF, #9F7AEA);
      color: white; font-size: 0.7rem; padding: 2px 8px; border-radius: 4px;
      font-family: var(--font-body); font-weight: 600; margin-left: 4px; vertical-align: super;
    }
    .tagline { color: var(--text-secondary); font-size: 1.1rem; }
    .cannabis-decoration { display: flex; justify-content: center; gap: 1.5rem; margin-bottom: 2rem; font-size: 2rem; animation: sway 3s ease-in-out infinite; }
    @keyframes sway { 0%, 100% { transform: rotate(-5deg); } 50% { transform: rotate(5deg); } }
    .input-group { margin-bottom: 1rem; }
    .input-group input {
      width: 100%; padding: 1rem; font-size: 1rem; font-family: var(--font-body);
      background: rgba(0, 0, 0, 0.4); border: 2px solid rgba(0, 150, 57, 0.3);
      border-radius: 8px; color: var(--text-primary); transition: all 0.3s ease;
    }
    .input-group input:focus { outline: none; border-color: var(--rasta-green); box-shadow: 0 0 20px rgba(0, 150, 57, 0.3); }
    .login-btn {
      width: 100%; padding: 1rem; font-size: 1.1rem; font-family: var(--font-body); font-weight: 600;
      background: var(--rasta-gradient); border: none; border-radius: 8px; color: white; cursor: pointer; transition: all 0.3s ease;
    }
    .login-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(0, 150, 57, 0.4); }
    .error-msg { color: var(--rasta-red); text-align: center; margin-top: 1rem; min-height: 1.5rem; }

    /* ═══ DASHBOARD (preserved + enhanced) ═══ */
    #dashboard-screen {
      background: radial-gradient(ellipse at 20% 30%, rgba(0, 150, 57, 0.12) 0%, transparent 50%),
                  radial-gradient(ellipse at 80% 70%, rgba(255, 184, 28, 0.08) 0%, transparent 50%),
                  radial-gradient(ellipse at 50% 100%, rgba(200, 16, 46, 0.06) 0%, transparent 40%),
                  var(--bg-dark);
    }
    .dashboard-header {
      background: rgba(20, 26, 20, 0.9); border-bottom: 1px solid rgba(0, 150, 57, 0.3);
      padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center;
      flex-wrap: wrap; gap: 1rem; position: sticky; top: 0; z-index: 100; backdrop-filter: blur(20px);
    }
    .header-content h1 { font-family: var(--font-display); font-size: 1.8rem; background: var(--rasta-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .header-content p { color: var(--text-secondary); font-size: 0.9rem; }
    .logout-btn { background: transparent; border: 2px solid var(--rasta-red); color: var(--rasta-red); padding: 0.5rem 1rem; border-radius: 8px; font-family: var(--font-body); font-weight: 500; cursor: pointer; transition: all 0.3s ease; }
    .logout-btn:hover { background: var(--rasta-red); color: white; transform: translateY(-2px); }
    .dashboard-main { max-width: 1200px; margin: 0 auto; padding: 2rem; }

    /* ═══ RECIPE SELECTOR (NEW V2) ═══ */
    .recipe-grid {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
      gap: 0.75rem; margin-bottom: 2rem; max-width: 700px; margin-left: auto; margin-right: auto;
    }
    .recipe-card {
      background: var(--bg-card); border: 2px solid rgba(255,255,255,0.1); border-radius: 12px;
      padding: 0.75rem; text-align: center; cursor: pointer; transition: all 0.3s ease;
    }
    .recipe-card:hover { border-color: var(--rasta-gold); transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,150,57,0.2); }
    .recipe-card.active { border-color: var(--rasta-green); background: rgba(0,150,57,0.15); box-shadow: 0 0 20px rgba(0,150,57,0.3); }
    .recipe-icon { font-size: 1.8rem; margin-bottom: 0.25rem; }
    .recipe-name { font-size: 0.75rem; font-weight: 600; color: var(--text-primary); }
    .recipe-desc { font-size: 0.65rem; color: var(--text-muted); margin-top: 2px; }

    /* ═══ ALCHEMY CONTROLS (NEW V2) ═══ */
    .alchemy-controls {
      max-width: 700px; margin: 0 auto 2rem; background: var(--bg-card);
      border: 1px solid rgba(0,150,57,0.2); border-radius: var(--border-radius); padding: 1.5rem;
    }
    .alchemy-section { margin-bottom: 1.25rem; }
    .alchemy-section:last-child { margin-bottom: 0; }
    .alchemy-label { font-size: 0.85rem; font-weight: 600; color: var(--rasta-gold); margin-bottom: 0.5rem; display: block; }
    .chip-row { display: flex; flex-wrap: wrap; gap: 0.5rem; }
    .chip {
      padding: 0.4rem 0.85rem; border-radius: 20px; font-size: 0.8rem; font-family: var(--font-body);
      background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.15); color: var(--text-secondary);
      cursor: pointer; transition: all 0.25s ease; user-select: none;
    }
    .chip:hover { border-color: var(--rasta-gold); color: var(--text-primary); }
    .chip.active { background: rgba(0,150,57,0.2); border-color: var(--rasta-green); color: var(--rasta-green); }
    .intensity-bar { display: flex; gap: 0.5rem; align-items: center; }
    .intensity-dot {
      width: 28px; height: 28px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.2);
      background: rgba(0,0,0,0.3); cursor: pointer; transition: all 0.25s ease;
      display: flex; align-items: center; justify-content: center; font-size: 0.65rem; color: var(--text-muted);
    }
    .intensity-dot:hover { border-color: var(--rasta-gold); }
    .intensity-dot.active { background: var(--rasta-green); border-color: var(--rasta-green); color: white; }
    .intensity-label { font-size: 0.75rem; color: var(--text-muted); margin-left: 0.5rem; }
    .alchemy-select {
      background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.15); color: var(--text-primary);
      padding: 0.5rem 1rem; border-radius: 8px; font-family: var(--font-body); font-size: 0.85rem;
      cursor: pointer; width: 100%; max-width: 300px;
    }
    .alchemy-select option { background: var(--bg-dark); }
    .alchemy-input {
      width: 100%; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.15);
      color: var(--text-primary); padding: 0.5rem 1rem; border-radius: 8px;
      font-family: var(--font-body); font-size: 0.85rem; resize: vertical; min-height: 50px;
    }
    .alchemy-input:focus, .alchemy-select:focus { outline: none; border-color: var(--rasta-green); box-shadow: 0 0 10px rgba(0,150,57,0.2); }
    .alchemy-toggle { display: none; }
    .alchemy-toggle-btn {
      display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border-radius: 8px;
      background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary);
      cursor: pointer; font-family: var(--font-body); font-size: 0.85rem; transition: all 0.3s; margin-bottom: 1rem;
    }
    .alchemy-toggle-btn:hover { border-color: var(--rasta-gold); }
    .help-text { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; margin-bottom: 0.4rem; line-height: 1.4; font-style: italic; }
    /* ═══ MULTI-IMAGE UPLOAD (V2) ═══ */
    .image-slots { max-width: 760px; margin: 0 auto 2rem; }
    .image-slots-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
    @media (max-width: 768px) { .image-slots-grid { grid-template-columns: 1fr 1fr; } }
    @media (max-width: 480px) { .image-slots-grid { grid-template-columns: 1fr; } }
    .image-slot {
      border: 2px dashed rgba(0, 150, 57, 0.4); border-radius: 12px;
      background: rgba(20, 26, 20, 0.6); padding: 1rem; text-align: center;
      cursor: pointer; transition: all 0.3s ease; min-height: 170px;
      display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative;
    }
    .image-slot:hover { border-color: var(--rasta-green); background: rgba(0, 150, 57, 0.1); }
    .image-slot.has-image { border-style: solid; border-color: var(--rasta-green); }
    .image-slot.primary { border-color: var(--rasta-gold); border-width: 3px; }
    .image-slot.primary.has-image { border-color: var(--rasta-gold); background: rgba(255,184,28,0.05); }
    .slot-icon { font-size: 2.2rem; margin-bottom: 0.4rem; }
    .slot-label { font-weight: 600; font-size: 0.8rem; color: var(--text-primary); margin-bottom: 0.2rem; }
    .slot-desc { font-size: 0.65rem; color: var(--text-muted); line-height: 1.3; }
    .slot-badge { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.2rem; }
    .slot-badge.required { color: var(--rasta-gold); }
    .slot-badge.optional { color: var(--text-muted); }
    .slot-preview { width: 100%; max-height: 110px; object-fit: contain; border-radius: 8px; margin-bottom: 0.4rem; }
    .slot-remove { position: absolute; top: 6px; right: 8px; background: rgba(200,16,46,0.7); color: white; border: none; border-radius: 50%; width: 22px; height: 22px; font-size: 0.75rem; cursor: pointer; display: none; align-items: center; justify-content: center; z-index: 5; }
    .image-slot.has-image .slot-remove { display: flex; }
    .slot-role-select {
      background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.15); color: var(--text-primary);
      padding: 0.25rem 0.5rem; border-radius: 6px; font-family: var(--font-body); font-size: 0.7rem; margin-top: 0.4rem; width: 100%;
    }
    .slot-role-select option { background: var(--bg-dark); }
    .add-slot-btn {
      border: 2px dashed rgba(255,255,255,0.15); border-radius: 12px; background: transparent;
      color: var(--text-muted); font-family: var(--font-body); font-size: 0.85rem;
      cursor: pointer; transition: all 0.3s; min-height: 170px; display: flex;
      flex-direction: column; align-items: center; justify-content: center; gap: 0.5rem;
    }
    .add-slot-btn:hover { border-color: var(--rasta-gold); color: var(--rasta-gold); background: rgba(255,184,28,0.05); }
    .add-slot-icon { font-size: 2rem; }
    .no-image-note { text-align: center; color: var(--rasta-gold); font-size: 0.9rem; margin-bottom: 1.5rem; padding: 0.75rem; background: rgba(255,184,28,0.1); border-radius: 8px; max-width: 760px; margin-left: auto; margin-right: auto; }
    .upload-icon { font-size: 3.5rem; margin-bottom: 0.75rem; }

    /* ═══ PREVIEW (preserved from V1) ═══ */
    .preview-container { display: grid; grid-template-columns: 1fr auto 1fr; gap: 1.5rem; align-items: center; margin-bottom: 2rem; }
    .preview-card { background: var(--bg-card); border-radius: var(--border-radius); padding: 1rem; border: 1px solid rgba(255, 255, 255, 0.1); }
    .preview-card h3 { text-align: center; margin-bottom: 0.75rem; font-size: 1rem; color: var(--text-secondary); }
    .preview-card.transformed h3 { color: var(--rasta-gold); }
    .image-wrapper { border-radius: 8px; overflow: hidden; background: rgba(0, 0, 0, 0.3); min-height: 250px; display: flex; align-items: center; justify-content: center; }
    .image-wrapper img { max-width: 100%; max-height: 350px; object-fit: contain; }
    .transform-arrow { text-align: center; }
    .transform-arrow .arrow { font-size: 2.5rem; color: var(--rasta-green); }
    .transform-text { font-size: 0.8rem; color: var(--text-muted); display: block; }

    /* ═══ LOADING (preserved from V1) ═══ */
    .loading { text-align: center; padding: 2rem; }
    .loading-smoke { font-size: 2rem; margin-bottom: 0.5rem; }
    .loading-smoke span { display: inline-block; animation: float-smoke 1.5s ease-in-out infinite; }
    .loading-smoke span:nth-child(2) { animation-delay: 0.2s; }
    .loading-smoke span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes float-smoke { 0%, 100% { transform: translateY(0) scale(1); opacity: 0.7; } 50% { transform: translateY(-10px) scale(1.2); opacity: 1; } }
    .loading p { color: var(--rasta-gold); }
    .loading-sub { color: var(--text-muted); font-size: 0.9rem; }

    /* ═══ BUTTONS (preserved from V1) ═══ */
    .btn-container { text-align: center; margin-bottom: 2rem; }
    .transform-btn {
      background: var(--rasta-gradient); border: none; padding: 1rem 2.5rem; font-size: 1.2rem;
      font-family: var(--font-body); font-weight: 600; color: white; border-radius: 8px;
      cursor: pointer; transition: all 0.3s ease; display: inline-flex; align-items: center; gap: 0.75rem;
    }
    .transform-btn:hover { transform: translateY(-3px); box-shadow: 0 15px 40px rgba(0, 150, 57, 0.4); }
    .transform-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .download-btn {
      background: var(--bg-card); border: 2px solid var(--rasta-gold); color: var(--rasta-gold);
      padding: 0.75rem 1.5rem; font-size: 1rem; font-weight: 600; border-radius: 8px; cursor: pointer;
      transition: all 0.3s ease; text-decoration: none; display: inline-flex; align-items: center; margin-left: 1rem;
    }
    .download-btn:hover { background: var(--rasta-gold); color: var(--bg-dark); }

    /* ═══ MODEL SELECTOR (preserved from V1) ═══ */
    .model-selector { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
    .model-selector label { color: var(--text-secondary); font-size: 0.9rem; font-weight: 500; }
    .model-selector select {
      background: var(--bg-card); border: 2px solid var(--rasta-green); color: var(--text-primary);
      padding: 0.5rem 1rem; font-size: 0.9rem; border-radius: 8px; font-family: var(--font-body); cursor: pointer; transition: all 0.3s ease;
    }
    .model-selector select:hover { border-color: var(--rasta-gold); box-shadow: 0 0 15px rgba(255, 184, 28, 0.2); }
    .model-selector select:focus { outline: none; border-color: var(--rasta-gold); box-shadow: 0 0 20px rgba(255, 184, 28, 0.3); }
    .model-selector select option { background: var(--bg-dark); color: var(--text-primary); }

    /* ═══ INFO + GALLERY + MODAL + FOOTER (preserved from V1) ═══ */
    .info-section { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-top: 2rem; }
    .info-card { background: var(--bg-card); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: var(--border-radius); padding: 1.25rem; }
    .info-card h3 { color: var(--rasta-gold); margin-bottom: 0.75rem; font-size: 1.1rem; }
    .info-card ul { list-style: none; }
    .info-card li { padding: 0.4rem 0; color: var(--text-secondary); border-bottom: 1px solid rgba(255,255,255,0.05); }
    .info-card li:last-child { border-bottom: none; }
    .info-card p { color: var(--text-secondary); line-height: 1.6; }
    .info-card .small { font-size: 0.85rem; color: var(--text-muted); }
    .gallery-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1.5rem; padding: 1rem 0; }
    .gallery-item { background: var(--bg-card); border-radius: var(--border-radius); overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.1); transition: all 0.3s ease; cursor: pointer; }
    .gallery-item:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0, 150, 57, 0.2); border-color: var(--rasta-gold); }
    .gallery-img-container { width: 100%; height: 250px; overflow: hidden; background: #000; }
    .gallery-img-container img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease; }
    .gallery-item:hover img { transform: scale(1.05); }
    .gallery-info { padding: 1rem; }
    .gallery-date { font-size: 0.8rem; color: var(--rasta-gold); margin-bottom: 0.25rem; }
    .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); display: flex; align-items: center; justify-content: center; z-index: 1000; opacity: 0; pointer-events: none; transition: opacity 0.3s; }
    .modal.active { opacity: 1; pointer-events: all; }
    .modal-content { max-width: 90%; max-height: 90vh; position: relative; }
    .modal-img { max-width: 100%; max-height: 85vh; border-radius: 8px; box-shadow: 0 0 30px rgba(0,0,0,0.5); }
    .modal-close { position: absolute; top: -40px; right: 0; color: white; font-size: 2rem; cursor: pointer; }
    .modal-close:hover { color: var(--rasta-red); }
    .dashboard-footer { text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.9rem; }
    .dashboard-footer a { color: var(--rasta-green); text-decoration: none; }
    .dashboard-footer a:hover { text-decoration: underline; }

    /* ═══ METADATA DISPLAY (NEW V2) ═══ */
    .transmission-card {
      background: var(--bg-card); border: 1px solid rgba(0,150,57,0.3); border-radius: var(--border-radius);
      padding: 1.25rem; margin-top: 1rem; max-width: 700px; margin-left: auto; margin-right: auto;
    }
    .transmission-card h4 { color: var(--rasta-gold); font-family: var(--font-display); font-size: 1rem; margin-bottom: 0.5rem; }
    .transmission-text { color: var(--text-secondary); font-size: 0.85rem; font-style: italic; line-height: 1.5; }
    .meta-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.5rem; }
    .meta-chip { font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; background: rgba(0,150,57,0.15); color: var(--rasta-green); border: 1px solid rgba(0,150,57,0.3); }

    @media (max-width: 768px) {
      .preview-container { grid-template-columns: 1fr; }
      .transform-arrow { transform: rotate(90deg); padding: 1rem 0; }
      .dashboard-header { flex-direction: column; text-align: center; }
      .recipe-grid { grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); }
    }
  </style>
</head>
<body>
  <!-- Modal -->
  <div id="image-modal" class="modal">
    <div class="modal-content">
      <div class="modal-close" id="modal-close">&times;</div>
      <img id="modal-img" class="modal-img" src="">
      <div style="text-align: center; margin-top: 1rem;">
        <a id="modal-download" class="download-btn" href="#" download style="display: inline-flex;">Download High Res</a>
      </div>
    </div>
  </div>

  <!-- Login Screen (preserved from V1) -->
  <div id="login-screen" class="screen active">
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <h1>🌿 Ganjafy <span class="v2-badge">V2</span></h1>
          <p class="tagline">Powered by the Irie Alchemist</p>
        </div>
        <div class="cannabis-decoration"><span>🍃</span><span>🌿</span><span>🍃</span></div>
        <form id="login-form">
          <div class="input-group">
            <input type="password" id="password-input" placeholder="Secret Password (uses our AI)" autocomplete="off">
          </div>
          <button type="submit" class="login-btn"><span>Enter di Vibes</span> <span>💨</span></button>
        </form>
        <div style="text-align: center; margin: 1.5rem 0 0.5rem; color: var(--text-muted); font-size: 0.9rem;">— OR —</div>
        <button id="byok-btn" class="login-btn" style="background: linear-gradient(135deg, #6B46C1, #9F7AEA); margin-top: 0;">
          <span>🔑 Bring Your Own API Key</span>
        </button>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.75rem; text-align: center;">Use your own Gemini or OpenRouter key</p>
        <p id="login-error" class="error-msg"></p>
      </div>
    </div>
  </div>

  <!-- Dashboard -->
  <div id="dashboard-screen" class="screen">
    <header class="dashboard-header">
      <div class="header-content">
        <h1>🌿 Ganjafy V2</h1>
        <p>Powered by Irie Alchemist • NETSPI-BINGHI Engine</p>
      </div>
      <div style="display: flex; gap: 10px; flex-wrap: wrap; justify-content: center;">
        <button id="gallery-btn" class="logout-btn" style="border-color: var(--rasta-gold); color: var(--rasta-gold);">Gallery 🖼️</button>
        <button id="create-btn" class="logout-btn hidden" style="border-color: var(--rasta-green); color: var(--rasta-green);">Create 🎨</button>
        <button id="text-translator-btn" class="logout-btn" onclick="window.location.href='https://grokandmon.com/ganjamontexttranslator'">Text Translator 💬</button>
        <button id="logout-btn" class="logout-btn">Bless Out 🚪</button>
      </div>
    </header>

    <main class="dashboard-main" id="create-view">
      <!-- Recipe Selector (NEW V2) -->
      <div class="recipe-grid" id="recipe-grid"></div>

      <!-- No-image recipe note -->
      <div id="no-image-note" class="no-image-note hidden">✨ This recipe generates from text only - no image needed! Adjust alchemy controls below or hit Transmit.</div>

      <!-- Multi-Image Upload (V2 - Dynamic Slots) -->
      <div class="image-slots" id="image-slots">
        <div class="image-slots-grid" id="image-slots-grid">
          <!-- Slots are built dynamically by JS -->
        </div>
        <p style="text-align: center; font-size: 0.75rem; color: var(--text-muted); margin-top: 0.75rem;">JPEG, PNG, WebP • Max 10MB each • Drop or click to add • Multiple subjects supported</p>
      </div>

      <!-- Alchemy Controls (NEW V2) -->
      <button class="alchemy-toggle-btn" id="alchemy-toggle-btn" onclick="document.getElementById('alchemy-controls').classList.toggle('hidden'); this.querySelector('.toggle-arrow').textContent = document.getElementById('alchemy-controls').classList.contains('hidden') ? '▶' : '▼';">
        <span class="toggle-arrow">▶</span> 🔮 Alchemy Controls <span style="font-size:0.7rem; color:var(--text-muted);">(optional)</span>
      </button>
      <div class="alchemy-controls hidden" id="alchemy-controls">
        <div class="alchemy-section">
          <span class="alchemy-label">⚡ Intensity</span>
          <p class="help-text">How heavily the recipe transforms the image. Low = subtle accents, High = full visual possession.</p>
          <div class="intensity-bar" id="intensity-bar">
            <div class="intensity-dot active" data-val="1">1</div>
            <div class="intensity-dot active" data-val="2">2</div>
            <div class="intensity-dot active" data-val="3">3</div>
            <div class="intensity-dot" data-val="4">4</div>
            <div class="intensity-dot" data-val="5">5</div>
            <span class="intensity-label" id="intensity-label">Heavy</span>
          </div>
        </div>
        <div class="alchemy-section">
          <span class="alchemy-label">🕰️ Era</span>
          <p class="help-text">Sets the visual time period. Affects color grading, film grain, typography, and cultural references in the output.</p>
          <div class="chip-row" id="era-chips">
            <div class="chip" data-val="1930s" title="Sepia tone, Pinnacle commune era, early Rasta movement. Hand-tinted photography aesthetic.">1930s</div>
            <div class="chip" data-val="1960s" title="Civil rights era, Ska music, independence movement. Vintage Kodachrome colors.">1960s</div>
            <div class="chip" data-val="1970s" title="Peak roots reggae, dub experiments, Haile Selassie imagery. Warm analog film tones.">1970s</div>
            <div class="chip" data-val="1980s" title="Dancehall emergence, digital riddims, international spread. VHS aesthetic.">1980s</div>
            <div class="chip" data-val="modern" title="Contemporary clean look, digital art fusion, modern Rasta culture.">Modern</div>
          </div>
        </div>
        <div class="alchemy-section">
          <span class="alchemy-label">🎭 Mood</span>
          <p class="help-text">Emotional tone that shapes the color palette, atmosphere, and symbolic elements in your transformation.</p>
          <div class="chip-row" id="mood-chips">
            <div class="chip" data-val="ital" title="Pure, natural, earth-connected. Clean greens, meditation, farm-to-table sacrament. Peaceful vibration.">🌿 Ital</div>
            <div class="chip" data-val="militant" title="Righteous anger, revolution, resistance. High contrast, bold reds, raised fists, fire imagery.">⚡ Militant</div>
            <div class="chip" data-val="conscious" title="Awareness, education, reasoning. Warm gold tones, books, scrolls, third-eye symbolism.">🕊️ Conscious</div>
            <div class="chip" data-val="royal" title="Ethiopian royalty, Lion of Judah, imperial majesty. Purple, gold, crowns, velvet texture.">👑 Royal</div>
            <div class="chip" data-val="dub" title="Sound system culture, bass frequencies made visible. Echo effects, speaker stacks, reverb trails.">🔊 Dub</div>
            <div class="chip" data-val="chaos" title="Egregore mode. Unhinged visual static, psychedelic distortion, glitch aesthetics, Black Ark madness.">🌀 Chaos</div>
          </div>
        </div>
        <div class="alchemy-section">
          <span class="alchemy-label">👤 Figure Grounding</span>
          <p class="help-text">Anchors the visual language to a specific Rasta prophet or figure. Their iconography, era, and philosophy influences the output.</p>
          <div class="chip-row" id="figure-chips">
            <div class="chip" data-val="selassie" title="Emperor Haile Selassie I — Ethiopian imperial regalia, Lion of Judah, Orthodox cross, formal portraiture.">👑 Selassie</div>
            <div class="chip" data-val="marley" title="Bob Marley — Trench Town roots, One Love energy, natural dreads, concert stage presence, acoustic warmth.">🎸 Marley</div>
            <div class="chip" data-val="perry" title="Lee 'Scratch' Perry — Black Ark studio chaos, hand-painted walls, sonic experimentation, raw DIY madness.">🔊 Perry</div>
            <div class="chip" data-val="tosh" title="Peter Tosh — Militant equal rights, machete imagery, Legalize It activism, uncompromising resistance.">⚔️ Tosh</div>
            <div class="chip" data-val="garvey" title="Marcus Garvey — Pan-African prophecy, UNIA movement, black star liner, formal oratory, nation-building.">📜 Garvey</div>
            <div class="chip" data-val="howell" title="Leonard Howell — The First Rasta, Pinnacle commune founder, ganja farmer prophet, colonial resistance.">🏔️ Howell</div>
          </div>
        </div>
        <div class="alchemy-section">
          <span class="alchemy-label">🌿 Strain Context</span>
          <p class="help-text">Infuses strain-specific color palette and terpene symbolism into the visual output. Each strain has unique visual DNA.</p>
          <select class="alchemy-select" id="strain-select">
            <option value="">None (no strain influence)</option>
            <option value="gdp_runtz" selected>GDP Runtz — Deep purples, dense trichomes, indica calm (Current Grow)</option>
            <option value="jamaican_lambsbread">Jamaican Lamb's Bread — Golden sativa glow, tropical energy, Marley's choice</option>
            <option value="durban_poison">Durban Poison — African landrace, bright sativa clarity, sharp greens</option>
            <option value="blue_dream">Blue Dream — Hazy blue-violet tones, dreamy clouds, balanced energy</option>
            <option value="og_kush">OG Kush — Earth tones, West Coast sunset, heavy resin, deep forest</option>
          </select>
        </div>
        <div class="alchemy-section">
          <span class="alchemy-label">📝 Custom Incantation</span>
          <p class="help-text">Free-form text appended to the prompt. Describe a scene, reference an artist, or add specific visual instructions.</p>
          <textarea class="alchemy-input" id="custom-prompt" placeholder="Additional prophecy... (e.g., 'walking through Bull Bay at dawn' or 'in the style of a 1970s Jamaican dancehall poster')"></textarea>
        </div>
      </div>

      <!-- Preview (preserved from V1) -->
      <div id="preview-container" class="preview-container hidden">
        <div class="preview-card original">
          <h3>Original Babylon Version</h3>
          <div class="image-wrapper"><img id="original-preview" src="" alt="Original"></div>
        </div>
        <div class="transform-arrow"><span class="arrow">→</span><span class="transform-text">Irie Transformation</span></div>
        <div class="preview-card transformed">
          <h3>Blessed Rasta Version</h3>
          <div class="image-wrapper" id="result-wrapper">
            <div id="loading-indicator" class="loading hidden">
              <div class="loading-smoke"><span>💨</span><span>💨</span><span>💨</span></div>
              <p>Jah is blessing your image...</p>
              <p class="loading-sub" id="loading-recipe-text">Adding tams, dreads & ganja vibes</p>
            </div>
            <img id="result-preview" src="" alt="Transformed" class="hidden">
          </div>
        </div>
      </div>

      <!-- Buttons (preserved from V1 + enhanced) -->
      <div class="btn-container">
        <div id="api-key-config" class="hidden" style="background: var(--bg-card); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1rem; margin-bottom: 1rem; max-width: 500px; margin-left: auto; margin-right: auto;">
          <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
            <span>🔑</span><label style="color: var(--text-secondary); font-weight: 500;">Your API Key</label>
          </div>
          <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            <select id="api-provider" style="background: var(--bg-dark); border: 2px solid var(--rasta-green); color: var(--text-primary); padding: 0.5rem; border-radius: 8px; font-family: var(--font-body);">
              <option value="gemini">Google Gemini</option>
              <option value="openrouter">OpenRouter</option>
            </select>
            <input type="password" id="user-api-key" placeholder="Paste your API key here" style="flex: 1; min-width: 200px; background: var(--bg-dark); border: 2px solid rgba(255,255,255,0.2); color: var(--text-primary); padding: 0.5rem 1rem; border-radius: 8px; font-family: var(--font-body);">
          </div>
          <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.75rem;">
            <input type="checkbox" id="save-key-checkbox" style="width: 18px; height: 18px; accent-color: var(--rasta-green);">
            <label for="save-key-checkbox" style="color: var(--text-muted); font-size: 0.85rem;">Save key locally (browser only)</label>
          </div>
          <p id="key-status" style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;"></p>
        </div>

        <div class="model-selector" id="model-selector" style="display: none;">
          <label for="model-select">🧠 AI Model:</label>
          <select id="model-select">
            <optgroup label="Direct Google API">
              <option value="gemini-3-pro-image-preview">Gemini 3 Pro (Best Quality)</option>
              <option value="gemini-2.5-flash-image">Gemini 2.5 Flash (Reliable)</option>
              <option value="imagen-4.0-generate-001">Imagen 4 (Text-to-Image)</option>
            </optgroup>
            <optgroup label="🌐 OpenRouter - Google">
              <option value="openrouter-gemini-3-pro">Nano Banana Pro 🍌</option>
              <option value="openrouter-gemini-2.5-flash">Nano Banana (2.5 Flash)</option>
              <option value="openrouter-gemini-2.0-free">Gemini 2.0 Flash (FREE) 🆓</option>
            </optgroup>
            <optgroup label="🌐 OpenRouter - FLUX">
              <option value="openrouter-flux-pro">FLUX.2 Pro (High Quality)</option>
              <option value="openrouter-flux-max">FLUX.2 Max (Best) 💰</option>
              <option value="openrouter-flux-klein">FLUX.2 Klein (Fast & Cheap)</option>
            </optgroup>
          </select>
        </div>
        <button id="transform-btn" class="transform-btn hidden">
          <span>🌿</span><span id="transform-btn-text">Transmit to Jah!</span><span>🌿</span>
        </button>
        <a id="download-btn" class="download-btn hidden" download><span>⬇️ Download Blessed Image</span></a>
        <div id="save-status" style="margin-top: 0.75rem; font-size: 0.9rem; text-align: center;"></div>
      </div>

      <!-- Transmission Metadata (NEW V2) -->
      <div id="transmission-card" class="transmission-card hidden">
        <h4>📡 Transmission Received</h4>
        <p class="transmission-text" id="transmission-text"></p>
        <div class="meta-chips" id="meta-chips"></div>
      </div>

      <section class="info-section">
        <div class="info-card">
          <h3>🔮 Recipe Guide</h3>
          <ul>
            <li><strong>🖼️ Irie Portrait</strong> — Identity-preserving rasta transformation. Adds dreads, tam, ganja, and cultural elements while keeping the subject's face intact.</li>
            <li><strong>👑 Lion of Judah</strong> — Ethiopian royalty aesthetic. Imperial regalia, Lion imagery, Solomonic dynasty styling.</li>
            <li><strong>✊ Roots Rebel</strong> — Revolutionary poster art. Protest energy, raised fists, militant typography, liberation movement vibes.</li>
            <li><strong>🔊 Dub Dreamscape</strong> — Sound system culture visualized. No input image needed. Generates speaker stacks, echo trails, bass frequencies.</li>
            <li><strong>🌿 Botanical Study</strong> — Sacred plant science. Transforms images with botanical illustration style, trichome details, and medicinal documentation aesthetic.</li>
            <li><strong>📜 Ganja Poster</strong> — Event/concert poster art. No input image needed. Generates vintage reggae show posters and promotional art.</li>
            <li><strong>🌀 Chaos Static</strong> — Egregore mode. Maximum psychedelic distortion, glitch art, Lee Perry Black Ark chaos energy.</li>
            <li><strong>💎 Milady Irie</strong> — NFT-style output. Combines Milady/Remilia aesthetic with Rasta elements for collectible digital art.</li>
          </ul>
        </div>
        <div class="info-card">
          <h3>📸 Multi-Image Input</h3>
          <p><strong>Primary / Character Images</strong> — The main subjects. Add one per person/character you want in the scene. Each gets transformed with the selected recipe.</p>
          <p style="margin-top: 0.5rem;"><strong>Style Reference</strong> — Optional. Upload any image whose visual style you want to borrow. Choose: match style, steal palette, apply texture, or follow composition.</p>
          <p style="margin-top: 0.5rem;"><strong>Scene / Background</strong> — Optional. An environment to place subjects in. Choose: use as background, place in environment, blend, or inpaint.</p>
          <p style="margin-top: 0.5rem;"><strong>+ Add Another</strong> — Need more? Add extra character refs, additional style refs, or more scene images. No limit.</p>
          <p class="small" style="margin-top: 0.75rem;">Irie Alchemist V2 • NETSPI-BINGHI Engine • Inspired by Irie Milady + Visual Alchemist</p>
        </div>
      </section>
    </main>

    <main class="dashboard-main hidden" id="gallery-view">
      <h2 style="font-family: var(--font-display); color: var(--rasta-gold); margin-bottom: 1.5rem; text-align: center;">Blessed Gallery</h2>
      <div id="gallery-grid" class="gallery-grid"></div>
      <div id="gallery-loading" class="loading hidden"><p>Loading di gallery...</p></div>
      <div id="pagination-container" style="text-align: center; margin-top: 2rem;">
        <button id="load-more-btn" class="transform-btn hidden" style="padding: 0.75rem 2rem; font-size: 1rem;">🌿 Load More Blessings 🌿</button>
        <p id="gallery-count" style="color: var(--text-muted); margin-top: 1rem;"></p>
      </div>
    </main>

    <footer class="dashboard-footer">
      <p>💚💛❤️ One Love • <a href="https://grokandmon.com">grokandmon.com</a> • Jah Bless 💚💛❤️</p>
    </footer>
  </div>

<script>
const RECIPE_DATA = {
  irie_portrait: { id:"irie_portrait", name:"Irie Portrait", icon:"🖼️", desc:"Identity-preserving rasta transformation", needs_image:true },
  lion_vision: { id:"lion_vision", name:"Lion of Judah", icon:"👑", desc:"Ethiopian royalty aesthetic", needs_image:true },
  roots_rebel: { id:"roots_rebel", name:"Roots Rebel", icon:"✊", desc:"Revolutionary poster art", needs_image:true },
  dub_dreamscape: { id:"dub_dreamscape", name:"Dub Dreamscape", icon:"🔊", desc:"Sound system visualization", needs_image:false },
  botanical_study: { id:"botanical_study", name:"Botanical Study", icon:"🌿", desc:"Sacred plant science", needs_image:true },
  ganja_poster: { id:"ganja_poster", name:"Ganja Poster", icon:"📜", desc:"Vintage event poster art", needs_image:false },
  chaos_static: { id:"chaos_static", name:"Chaos Static", icon:"🌀", desc:"Egregore psychedelic mode", needs_image:true },
  milady_irie: { id:"milady_irie", name:"Milady Irie", icon:"💎", desc:"NFT collectible style", needs_image:true }
};

const INTENSITY_NAMES = { 1:"Subtle", 2:"Medium", 3:"Heavy", 4:"Full Possession", 5:"Ego Death" };

// Slot definitions: the default set + roles for dynamic additions
const DEFAULT_SLOTS = [
  { id: 'primary', icon: '📷', label: 'Primary Subject', desc: 'The main character/subject to transform.', badge: 'required', isPrimary: true,
    role: 'subject', roleFixed: true },
  { id: 'style', icon: '🎨', label: 'Style Reference', desc: 'Visual style to borrow from.', badge: 'optional',
    role: 'style_match', roleOptions: [
      { val: 'style_match', text: 'Match this art style' },
      { val: 'color_palette', text: 'Use its color palette' },
      { val: 'texture_ref', text: 'Apply its texture/pattern' },
      { val: 'composition_ref', text: 'Follow its composition' }
    ]},
  { id: 'scene', icon: '🏞️', label: 'Scene / Background', desc: 'Environment to place subjects in.', badge: 'optional',
    role: 'background', roleOptions: [
      { val: 'background', text: 'Use as background' },
      { val: 'environment', text: 'Place subject in this environment' },
      { val: 'blend', text: 'Blend/composite with subject' },
      { val: 'inpaint', text: 'Inpaint subject into scene' }
    ]}
];

const EXTRA_SLOT_ROLES = [
  { val: 'character', text: 'Character / Person (subject #2, #3, etc.)' },
  { val: 'subject', text: 'Primary Subject' },
  { val: 'style_match', text: 'Style Reference (match art style)' },
  { val: 'color_palette', text: 'Color Palette Reference' },
  { val: 'texture_ref', text: 'Texture / Pattern Reference' },
  { val: 'composition_ref', text: 'Composition Reference' },
  { val: 'background', text: 'Background / Scene' },
  { val: 'environment', text: 'Environment Reference' },
  { val: 'blend', text: 'Blend / Composite' },
  { val: 'object_ref', text: 'Object Reference' },
  { val: 'pose_ref', text: 'Pose / Body Reference' }
];

let app;
let slotCounter = 0;

class Ganjafy {
  constructor() {
    this.sessionId = localStorage.getItem('ganjafySession');
    this.isByokMode = localStorage.getItem('ganjafyByok') === 'true';
    this.selectedRecipe = 'irie_portrait';
    this.intensity = 3;
    this.selectedEra = null;
    this.selectedMood = null;
    this.selectedFigure = null;
    // Dynamic image slots: { slotId: { file, role, label } }
    this.slots = {};
    this.init();
  }

  init() {
    // V1 event listeners (preserved)
    document.getElementById('login-form').addEventListener('submit', e => this.login(e));
    document.getElementById('byok-btn').addEventListener('click', () => this.enterByokMode());
    document.getElementById('logout-btn').addEventListener('click', () => this.logout());
    document.getElementById('gallery-btn').addEventListener('click', () => this.showGallery());
    document.getElementById('create-btn').addEventListener('click', () => this.showCreate());
    document.getElementById('transform-btn').addEventListener('click', () => this.transform());
    document.getElementById('user-api-key').addEventListener('input', () => this.onApiKeyChange());
    document.getElementById('save-key-checkbox').addEventListener('change', () => this.onSaveKeyToggle());
    document.getElementById('modal-close').addEventListener('click', () => document.getElementById('image-modal').classList.remove('active'));
    document.getElementById('image-modal').addEventListener('click', (e) => {
      if (e.target.id === 'image-modal') document.getElementById('image-modal').classList.remove('active');
    });

    // V2: Build recipe grid
    this.buildRecipeGrid();
    // V2: Setup alchemy controls
    this.setupAlchemyControls();
    // V2: Build dynamic image slots
    this.buildImageSlots();

    this.loadSavedApiKey();
    this.checkSession();
  }

  // ═══ V2: Dynamic Image Slots ═══
  buildImageSlots() {
    const grid = document.getElementById('image-slots-grid');
    grid.innerHTML = '';
    this.slots = {};

    // Create default slots
    DEFAULT_SLOTS.forEach(def => {
      this.createSlotElement(def.id, def.icon, def.label, def.desc, def.badge, def.isPrimary, def.roleFixed ? null : def.roleOptions, def.role);
    });

    // Add the "+ Add Another" button
    this.addPlusButton();
  }

  createSlotElement(slotId, icon, label, desc, badge, isPrimary, roleOptions, defaultRole) {
    const grid = document.getElementById('image-slots-grid');
    const plusBtn = document.getElementById('add-slot-btn');

    const slot = document.createElement('div');
    slot.className = 'image-slot' + (isPrimary ? ' primary' : '');
    slot.id = 'slot-' + slotId;
    slot.dataset.slot = slotId;

    const fileInputId = 'file-' + slotId;
    let inner = '<button class="slot-remove" id="remove-' + slotId + '">&times;</button>';
    inner += '<img class="slot-preview hidden" id="preview-' + slotId + '">';
    inner += '<div class="slot-icon" id="icon-' + slotId + '">' + icon + '</div>';
    inner += '<div class="slot-label">' + label + '</div>';
    inner += '<div class="slot-desc">' + desc + '</div>';
    inner += '<div class="slot-badge ' + badge + '">' + badge + '</div>';
    if (roleOptions && roleOptions.length) {
      inner += '<select class="slot-role-select" id="role-' + slotId + '">';
      roleOptions.forEach(opt => {
        inner += '<option value="' + opt.val + '"' + (opt.val === defaultRole ? ' selected' : '') + '>' + opt.text + '</option>';
      });
      inner += '</select>';
    }
    inner += '<input type="file" id="' + fileInputId + '" accept="image/*" hidden>';
    slot.innerHTML = inner;

    // Insert before the plus button if it exists, otherwise append
    if (plusBtn) grid.insertBefore(slot, plusBtn);
    else grid.appendChild(slot);

    // Event listeners
    slot.addEventListener('click', (e) => {
      if (e.target.tagName === 'SELECT' || e.target.tagName === 'OPTION' || e.target.tagName === 'BUTTON') return;
      document.getElementById(fileInputId).click();
    });
    slot.addEventListener('dragover', e => { e.preventDefault(); slot.style.borderColor = 'var(--rasta-green)'; });
    slot.addEventListener('dragleave', () => { slot.style.borderColor = ''; });
    slot.addEventListener('drop', e => {
      e.preventDefault(); slot.style.borderColor = '';
      if (e.dataTransfer.files.length) this.handleSlotFile(slotId, e.dataTransfer.files[0]);
    });
    document.getElementById(fileInputId).addEventListener('change', e => {
      if (e.target.files.length) this.handleSlotFile(slotId, e.target.files[0]);
    });
    document.getElementById('remove-' + slotId).addEventListener('click', (e) => {
      e.stopPropagation();
      this.removeSlotImage(slotId);
    });

    this.slots[slotId] = { file: null, role: defaultRole || 'subject' };
  }

  addPlusButton() {
    const grid = document.getElementById('image-slots-grid');
    const btn = document.createElement('button');
    btn.className = 'add-slot-btn';
    btn.id = 'add-slot-btn';
    btn.innerHTML = '<div class="add-slot-icon">+</div><div>Add Another Image</div><div style="font-size:0.65rem;">Character, style ref, scene...</div>';
    btn.addEventListener('click', () => this.addExtraSlot());
    grid.appendChild(btn);
  }

  addExtraSlot() {
    slotCounter++;
    const slotId = 'extra_' + slotCounter;
    this.createSlotElement(
      slotId, '👤', 'Image #' + (Object.keys(this.slots).length + 1),
      'Additional character, reference, or input image.',
      'optional', false, EXTRA_SLOT_ROLES, 'character'
    );
  }

  handleSlotFile(slotId, file) {
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) { alert('Only JPEG, PNG, WebP allowed!'); return; }
    if (file.size > 10 * 1024 * 1024) { alert('Max 10MB!'); return; }

    this.slots[slotId].file = file;
    const preview = document.getElementById('preview-' + slotId);
    const icon = document.getElementById('icon-' + slotId);
    const slot = document.getElementById('slot-' + slotId);

    const reader = new FileReader();
    reader.onload = e => {
      preview.src = e.target.result;
      preview.classList.remove('hidden');
      if (icon) icon.style.display = 'none';
      slot.classList.add('has-image');
    };
    reader.readAsDataURL(file);
    this.updateTransformButton();
  }

  removeSlotImage(slotId) {
    // If it's an extra slot and has no image, remove the whole slot
    if (slotId.startsWith('extra_')) {
      const slotEl = document.getElementById('slot-' + slotId);
      if (slotEl) slotEl.remove();
      delete this.slots[slotId];
      this.updateTransformButton();
      return;
    }
    // Default slots: just clear the image
    if (this.slots[slotId]) this.slots[slotId].file = null;
    const preview = document.getElementById('preview-' + slotId);
    const icon = document.getElementById('icon-' + slotId);
    const slot = document.getElementById('slot-' + slotId);
    const fileInput = document.getElementById('file-' + slotId);
    if (preview) { preview.src = ''; preview.classList.add('hidden'); }
    if (icon) icon.style.display = '';
    if (slot) slot.classList.remove('has-image');
    if (fileInput) fileInput.value = '';
    this.updateTransformButton();
  }

  updateTransformButton() {
    const r = RECIPE_DATA[this.selectedRecipe];
    const hasAnySubject = Object.values(this.slots).some(s => s.file && (s.role === 'subject' || s.role === 'character'));
    const hasPrimary = this.slots.primary?.file;
    const canTransform = !r.needs_image || hasPrimary || hasAnySubject;

    if (canTransform) {
      document.getElementById('transform-btn').classList.remove('hidden');
      document.getElementById('model-selector').style.display = 'flex';
    } else {
      document.getElementById('transform-btn').classList.add('hidden');
      document.getElementById('model-selector').style.display = 'none';
    }
  }

  // ═══ V2: Recipe Grid ═══
  buildRecipeGrid() {
    const grid = document.getElementById('recipe-grid');
    grid.innerHTML = '';
    Object.values(RECIPE_DATA).forEach(r => {
      const card = document.createElement('div');
      card.className = 'recipe-card' + (r.id === this.selectedRecipe ? ' active' : '');
      card.dataset.recipe = r.id;
      card.innerHTML = '<div class="recipe-icon">' + r.icon + '</div><div class="recipe-name">' + r.name + '</div><div class="recipe-desc">' + r.desc + '</div>';
      card.addEventListener('click', () => this.selectRecipe(r.id));
      grid.appendChild(card);
    });
  }

  selectRecipe(id) {
    this.selectedRecipe = id;
    document.querySelectorAll('.recipe-card').forEach(c => c.classList.toggle('active', c.dataset.recipe === id));
    const r = RECIPE_DATA[id];
    const imageSlots = document.getElementById('image-slots');
    const noImageNote = document.getElementById('no-image-note');
    if (!r.needs_image) {
      imageSlots.classList.add('hidden');
      noImageNote.classList.remove('hidden');
      document.getElementById('transform-btn').classList.remove('hidden');
      document.getElementById('model-selector').style.display = 'flex';
    } else {
      imageSlots.classList.remove('hidden');
      noImageNote.classList.add('hidden');
      this.updateTransformButton();
    }
    document.getElementById('loading-recipe-text').textContent = 'Brewing ' + r.name + ' recipe...';
  }

  // ═══ V2: Alchemy Controls ═══
  setupAlchemyControls() {
    document.querySelectorAll('#intensity-bar .intensity-dot').forEach(dot => {
      dot.addEventListener('click', () => {
        const val = parseInt(dot.dataset.val);
        this.intensity = val;
        document.querySelectorAll('#intensity-bar .intensity-dot').forEach(d => {
          d.classList.toggle('active', parseInt(d.dataset.val) <= val);
        });
        document.getElementById('intensity-label').textContent = INTENSITY_NAMES[val] || '';
      });
    });
    document.querySelectorAll('#intensity-bar .intensity-dot').forEach(d => {
      d.classList.toggle('active', parseInt(d.dataset.val) <= this.intensity);
    });
    this.setupChipGroup('era-chips', val => { this.selectedEra = val; });
    this.setupChipGroup('mood-chips', val => { this.selectedMood = val; });
    this.setupChipGroup('figure-chips', val => { this.selectedFigure = val; });
  }

  setupChipGroup(containerId, onSelect) {
    document.querySelectorAll('#' + containerId + ' .chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const isActive = chip.classList.contains('active');
        document.querySelectorAll('#' + containerId + ' .chip').forEach(c => c.classList.remove('active'));
        if (!isActive) { chip.classList.add('active'); onSelect(chip.dataset.val); }
        else { onSelect(null); }
      });
    });
  }

  getAlchemyOptions() {
    return {
      recipe: this.selectedRecipe,
      intensity: this.intensity,
      era: this.selectedEra,
      mood: this.selectedMood,
      figure: this.selectedFigure,
      strain: document.getElementById('strain-select')?.value || null,
      custom: document.getElementById('custom-prompt')?.value || null
    };
  }

  // ═══ V1 Methods (preserved) ═══
  loadSavedApiKey() {
    const savedKey = localStorage.getItem('ganjafyApiKey');
    const savedProvider = localStorage.getItem('ganjafyApiProvider') || 'gemini';
    if (savedKey) {
      document.getElementById('user-api-key').value = savedKey;
      document.getElementById('api-provider').value = savedProvider;
      document.getElementById('save-key-checkbox').checked = true;
      document.getElementById('key-status').textContent = '✅ Saved key loaded';
      document.getElementById('key-status').style.color = '#00FF7F';
    }
  }

  onApiKeyChange() {
    const key = document.getElementById('user-api-key').value.trim();
    const saveCheckbox = document.getElementById('save-key-checkbox');
    const provider = document.getElementById('api-provider').value;
    if (saveCheckbox.checked && key) {
      localStorage.setItem('ganjafyApiKey', key);
      localStorage.setItem('ganjafyApiProvider', provider);
      document.getElementById('key-status').textContent = '💾 Key saved locally';
      document.getElementById('key-status').style.color = '#00FF7F';
    }
  }

  onSaveKeyToggle() {
    const saveCheckbox = document.getElementById('save-key-checkbox');
    const key = document.getElementById('user-api-key').value.trim();
    const provider = document.getElementById('api-provider').value;
    if (saveCheckbox.checked && key) {
      localStorage.setItem('ganjafyApiKey', key);
      localStorage.setItem('ganjafyApiProvider', provider);
      document.getElementById('key-status').textContent = '💾 Key saved locally';
      document.getElementById('key-status').style.color = '#00FF7F';
    } else {
      localStorage.removeItem('ganjafyApiKey');
      localStorage.removeItem('ganjafyApiProvider');
      document.getElementById('key-status').textContent = 'Key cleared from storage';
      document.getElementById('key-status').style.color = 'var(--text-muted)';
    }
  }

  enterByokMode() {
    this.isByokMode = true;
    localStorage.setItem('ganjafyByok', 'true');
    this.sessionId = 'byok_' + Date.now();
    localStorage.setItem('ganjafySession', this.sessionId);
    this.showDashboard();
  }

  checkSession() { if (this.sessionId) { this.showDashboard(); } else { this.showLogin(); } }

  showLogin() {
    document.getElementById('login-screen').classList.add('active');
    document.getElementById('dashboard-screen').classList.remove('active');
  }

  showDashboard() {
    document.getElementById('login-screen').classList.remove('active');
    document.getElementById('dashboard-screen').classList.add('active');
    if (this.isByokMode) { document.getElementById('api-key-config').classList.remove('hidden'); }
    else { document.getElementById('api-key-config').classList.add('hidden'); }
    this.showCreate();
  }

  showCreate() {
    document.getElementById('create-view').classList.remove('hidden');
    document.getElementById('gallery-view').classList.add('hidden');
    document.getElementById('gallery-btn').classList.remove('hidden');
    document.getElementById('create-btn').classList.add('hidden');
  }

  async showGallery(reset = true) {
    document.getElementById('create-view').classList.add('hidden');
    document.getElementById('gallery-view').classList.remove('hidden');
    document.getElementById('gallery-btn').classList.add('hidden');
    document.getElementById('create-btn').classList.remove('hidden');
    const grid = document.getElementById('gallery-grid');
    const loading = document.getElementById('gallery-loading');
    const loadMoreBtn = document.getElementById('load-more-btn');
    const galleryCount = document.getElementById('gallery-count');
    if (reset) { grid.innerHTML = ''; this.galleryCursor = null; this.galleryTotal = 0; }
    loading.classList.remove('hidden');
    loadMoreBtn.classList.add('hidden');
    try {
      let url = '/ganjafy/api/gallery';
      if (this.galleryCursor) url += '?cursor=' + encodeURIComponent(this.galleryCursor);
      const res = await fetch(url, { headers: { 'X-Session-Id': this.sessionId } });
      const data = await res.json();
      loading.classList.add('hidden');
      if (data.images && data.images.length > 0) {
        this.galleryTotal += data.images.length;
        data.images.forEach(img => {
          const item = document.createElement('div');
          item.className = 'gallery-item';
          const timestamp = img.metadata?.timestamp || img.name.split('_')[1];
          item.innerHTML = '<div class="gallery-img-container"><img src="/ganjafy/api/image/' + img.name + '" loading="lazy" alt="Rasta Image"></div><div class="gallery-info"><div class="gallery-date">' + new Date(parseInt(timestamp)).toLocaleDateString() + '</div></div>';
          item.onclick = () => this.openModal('/ganjafy/api/image/' + img.name);
          grid.appendChild(item);
        });
        galleryCount.textContent = 'Showing ' + this.galleryTotal + ' blessed images';
        if (data.nextCursor) {
          this.galleryCursor = data.nextCursor;
          loadMoreBtn.classList.remove('hidden');
          loadMoreBtn.onclick = () => this.showGallery(false);
        } else { this.galleryCursor = null; }
      } else if (reset) {
        grid.innerHTML = '<p style="text-align:center; width:100%; color: var(--text-muted);">No images blessed yet. Be di first!</p>';
        galleryCount.textContent = '';
      }
    } catch (e) {
      loading.classList.add('hidden');
      grid.innerHTML = '<p style="text-align:center; color: var(--rasta-red);">Failed to load gallery: ' + e.message + '</p>';
    }
  }

  openModal(src) {
    document.getElementById('modal-img').src = src;
    document.getElementById('modal-download').href = src;
    document.getElementById('image-modal').classList.add('active');
  }

  async login(e) {
    e.preventDefault();
    const password = document.getElementById('password-input').value;
    try {
      const res = await fetch('/ganjafy/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password }) });
      const data = await res.json();
      if (res.ok && data.sessionId) {
        this.sessionId = data.sessionId; this.isByokMode = false;
        localStorage.setItem('ganjafySession', this.sessionId);
        localStorage.setItem('ganjafyByok', 'false');
        document.getElementById('password-input').value = '';
        document.getElementById('login-error').textContent = '';
        this.showDashboard();
      } else { document.getElementById('login-error').textContent = data.error || 'Wrong password!'; }
    } catch (err) { document.getElementById('login-error').textContent = 'Connection error'; }
  }

  logout() {
    localStorage.removeItem('ganjafySession'); localStorage.removeItem('ganjafyByok');
    this.sessionId = null; this.isByokMode = false; this.resetUI(); this.showLogin();
  }

  // ═══ V2: Enhanced Transform (dynamic multi-image) ═══
  async transform() {
    const r = RECIPE_DATA[this.selectedRecipe];
    const filledSlots = Object.entries(this.slots).filter(([k, v]) => v.file);
    const hasAnySubject = filledSlots.some(([k, v]) => v.role === 'subject' || v.role === 'character');

    if (r.needs_image && !hasAnySubject && !this.slots.primary?.file) return;

    document.getElementById('loading-indicator').classList.remove('hidden');
    document.getElementById('result-preview').classList.add('hidden');
    document.getElementById('transform-btn').disabled = true;
    document.getElementById('download-btn').classList.add('hidden');
    document.getElementById('save-status').innerHTML = '';
    document.getElementById('transmission-card').classList.add('hidden');

    // Show preview for first subject image
    const firstSubject = filledSlots.find(([k, v]) => v.role === 'subject' || v.role === 'character');
    if (firstSubject) {
      document.getElementById('preview-container').classList.remove('hidden');
      const reader = new FileReader();
      reader.onload = ev => { document.getElementById('original-preview').src = ev.target.result; };
      reader.readAsDataURL(firstSubject[1].file);
    } else if (!r.needs_image) {
      document.getElementById('preview-container').classList.remove('hidden');
    }

    try {
      const formData = new FormData();

      // Dynamic multi-image: send all slots that have files
      let imageIndex = 0;
      filledSlots.forEach(([slotId, slotData]) => {
        // Get the current role from the dropdown if it exists
        const roleSelect = document.getElementById('role-' + slotId);
        const role = roleSelect ? roleSelect.value : slotData.role;
        formData.append('image_' + imageIndex, slotData.file);
        formData.append('role_' + imageIndex, role);
        imageIndex++;
      });
      formData.append('image_count', imageIndex.toString());

      // Also send primary as 'image' for backward compat
      if (this.slots.primary?.file) formData.append('image', this.slots.primary.file);

      const selectedModel = document.getElementById('model-select').value;
      formData.append('model', selectedModel);

      // V2: Append alchemy options
      const opts = this.getAlchemyOptions();
      formData.append('recipe', opts.recipe);
      formData.append('intensity', opts.intensity);
      if (opts.era) formData.append('era', opts.era);
      if (opts.mood) formData.append('mood', opts.mood);
      if (opts.figure) formData.append('figure', opts.figure);
      if (opts.strain) formData.append('strain', opts.strain);
      if (opts.custom) formData.append('custom', opts.custom);

      if (this.isByokMode) {
        const userApiKey = document.getElementById('user-api-key').value.trim();
        const apiProvider = document.getElementById('api-provider').value;
        if (!userApiKey) { alert('Please enter your API key first!'); document.getElementById('loading-indicator').classList.add('hidden'); document.getElementById('transform-btn').disabled = false; return; }
        formData.append('userApiKey', userApiKey);
        formData.append('apiProvider', apiProvider);
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 90000);
      const res = await fetch('/ganjafy/api/transform', {
        method: 'POST', headers: { 'X-Session-Id': this.sessionId },
        body: formData, signal: controller.signal
      });
      clearTimeout(timeoutId);
      const data = await res.json();

      if (res.ok && data.imageData) {
        document.getElementById('result-preview').src = 'data:image/png;base64,' + data.imageData;
        document.getElementById('result-preview').classList.remove('hidden');
        document.getElementById('loading-indicator').classList.add('hidden');
        const downloadBtn = document.getElementById('download-btn');
        downloadBtn.href = 'data:image/png;base64,' + data.imageData;
        downloadBtn.download = 'ganjafy_' + Date.now() + '.png';
        downloadBtn.classList.remove('hidden');
        const saveStatusEl = document.getElementById('save-status');
        if (data.saveStatus === 'saved') { saveStatusEl.innerHTML = '<span style="color: #00FF7F;">✅ Saved to gallery!</span>'; }
        else if (data.saveStatus) { saveStatusEl.innerHTML = '<span style="color: #FF6B6B;">⚠️ Gallery: ' + data.saveStatus + '</span>'; }
        else { saveStatusEl.innerHTML = '<span style="color: #FFB81C;">⚠️ Gallery save status unknown</span>'; }

        // V2: Show transmission metadata
        if (data.metadata) {
          const tc = document.getElementById('transmission-card');
          document.getElementById('transmission-text').textContent = data.metadata.transmission || '';
          const chips = document.getElementById('meta-chips');
          chips.innerHTML = '';
          if (data.metadata.recipeName) chips.innerHTML += '<span class="meta-chip">' + data.metadata.recipeName + '</span>';
          if (data.metadata.manifestation) chips.innerHTML += '<span class="meta-chip">' + data.metadata.manifestation + '</span>';
          if (data.metadata.era && data.metadata.era !== 'timeless') chips.innerHTML += '<span class="meta-chip">' + data.metadata.era + '</span>';
          if (data.metadata.mood && data.metadata.mood !== 'auto') chips.innerHTML += '<span class="meta-chip">' + data.metadata.mood + '</span>';
          if (data.metadata.imageCount) chips.innerHTML += '<span class="meta-chip">' + data.metadata.imageCount + ' images</span>';
          chips.innerHTML += '<span class="meta-chip">v' + (data.metadata.version || '2.0') + '</span>';
          tc.classList.remove('hidden');
        }
      } else { throw new Error(data.error || 'Transform failed'); }
    } catch (err) {
      document.getElementById('loading-indicator').classList.add('hidden');
      const msg = err.name === 'AbortError' ? 'Request timed out (90s). Jah servers busy, try again!' : err.message;
      alert("Jah didn't bless us: " + msg);
    } finally { document.getElementById('transform-btn').disabled = false; }
  }

  resetUI() {
    this.buildImageSlots(); // Rebuild from scratch
    document.getElementById('preview-container').classList.add('hidden');
    document.getElementById('transform-btn').classList.add('hidden');
    document.getElementById('model-selector').style.display = 'none';
    document.getElementById('download-btn').classList.add('hidden');
    document.getElementById('original-preview').src = '';
    document.getElementById('result-preview').src = '';
    document.getElementById('transmission-card').classList.add('hidden');
  }
}

document.addEventListener('DOMContentLoaded', () => { app = new Ganjafy(); });
<\/script>
</body>
</html>`;

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
