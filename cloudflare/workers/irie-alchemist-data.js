/**
 * IRIE ALCHEMIST DATA LAYER
 * =========================
 * Ported from irie-milady/trait_mappings.py
 * 
 * NETSPI-BINGHI: Network Spirituality + Nyabinghi = The Synthesis
 * 
 * "The Irie transformation doesn't ADD Rastafari - it REVEALS the I-and-I already present."
 */

// =============================================================================
// RECIPE DEFINITIONS
// =============================================================================

export const RECIPES = {
  irie_portrait: {
    id: "irie_portrait",
    name: "Irie Portrait",
    manifestation: "POSTER",
    icon: "🖼️",
    description: "Identity-preserving rasta transformation",
    requires_image: true,
    philosophy: "The cute is camouflage. Babylon's algorithm promotes her. Babylon promotes Zion.",
    base_prompt: "IDENTITY PRESERVATION meets IRIE TRANSFORMATION"
  },
  lion_vision: {
    id: "lion_vision",
    name: "Lion of Judah",
    manifestation: "LION",
    icon: "👑",
    description: "Ethiopian royalty / Rastafari spiritual",
    requires_image: true,
    philosophy: "The conquering lion. Imperial Ethiopia awakened.",
    base_prompt: "ETHIOPIAN IMPERIAL AESTHETIC with LION OF JUDAH energy"
  },
  roots_rebel: {
    id: "roots_rebel",
    name: "Roots Rebel",
    manifestation: "ECHO",
    icon: "✊",
    description: "Revolutionary maroon warrior aesthetic",
    requires_image: true,
    philosophy: "The remix is revelation. Peter Tosh M16 guitar energy.",
    base_prompt: "REVOLUTIONARY MAROON WARRIOR with MILITANT ROOTS energy"
  },
  dub_dreamscape: {
    id: "dub_dreamscape",
    name: "Dub Dreamscape",
    manifestation: "DUB",
    icon: "🔊",
    description: "Sound system / Lee Perry psychedelic",
    requires_image: false,
    philosophy: "She IS the Black Ark. Her outfit is a mixing board.",
    base_prompt: "LEE PERRY DIMENSION - psychedelic dub soundscape"
  },
  botanical_study: {
    id: "botanical_study",
    name: "Botanical Study",
    manifestation: "STUDY",
    icon: "🌿",
    description: "Scientific cannabis illustration with strain data",
    requires_image: true,
    philosophy: "The plant as teacher. Sacred botany.",
    base_prompt: "SCIENTIFIC CANNABIS ILLUSTRATION with botanical precision"
  },
  ganja_poster: {
    id: "ganja_poster",
    name: "Ganja Poster",
    manifestation: "POSTER",
    icon: "📜",
    description: "Event/concert poster generation",
    requires_image: false,
    philosophy: "The poster IS an antenna. Distribution as spiritual practice.",
    base_prompt: "ROOTS REGGAE CONCERT POSTER with hand-drawn aesthetic"
  },
  chaos_static: {
    id: "chaos_static",
    name: "Chaos Static",
    manifestation: "STATIC",
    icon: "🌀",
    description: "Full chaos manifestation - egregore emergence",
    requires_image: true,
    philosophy: "The prison has holes. She IS the hole. Through the static: something divine leaking.",
    base_prompt: "FULL CHAOS EGREGORE MANIFESTATION - reality glitching"
  },
  milady_irie: {
    id: "milady_irie",
    name: "Milady Irie",
    manifestation: "VIP",
    icon: "💎",
    description: "NFT-optimized with trait injection",
    requires_image: true,
    philosophy: "This is not a transformation. This is a RECOGNITION.",
    base_prompt: "NEOCHIBI IRIE TRANSFORMATION with MILADY aesthetic preserved"
  }
};

// =============================================================================
// INTENSITY LEVELS
// =============================================================================

export const INTENSITY_LEVELS = {
  1: {
    name: "Subtle",
    description: "Rasta elements integrated naturally",
    prompt_mod: "SUBTLE integration - elements blend naturally, could pass in Babylon unnoticed"
  },
  2: {
    name: "Medium", 
    description: "Clear transformation, identity preserved",
    prompt_mod: "MEDIUM transformation - clearly Irie but identity fully preserved"
  },
  3: {
    name: "Heavy",
    description: "Strong transformation, egregore emerging",
    prompt_mod: "HEAVY transformation - the egregore is emerging, reality bending"
  },
  4: {
    name: "Full Possession",
    description: "She IS the manifestation",
    prompt_mod: "FULL POSSESSION - she IS the manifestation now, the original was the mask"
  },
  5: {
    name: "Ego Death",
    description: "Pure channel, no filter",
    prompt_mod: "EGO DEATH - pure channel, no ego remains, complete vessel for Zion transmission"
  }
};

// =============================================================================
// ERA STYLES
// =============================================================================

export const ERA_STYLES = {
  "1930s": {
    name: "1930s - Formative",
    figures: ["Howell", "Garvey"],
    aesthetic: "Pinnacle commune, UNIA uniforms, fedoras, raw early locks, Black Star Line iconography",
    palette: "Sepia, earth tones, aged photographs",
    prompt: "1930s FORMATIVE ERA - Leonard Howell Pinnacle commune energy, Marcus Garvey UNIA uniforms, early raw dreadlocks, sepia documentary aesthetic"
  },
  "1960s": {
    name: "1960s - Groundation", 
    figures: ["Selassie", "Planno"],
    aesthetic: "Selassie's Jamaica visit, Coral Gardens aftermath, early ska, Groundation movement",
    palette: "Faded color film, golden hour Jamaican light",
    prompt: "1960s GROUNDATION ERA - Selassie's 1966 Jamaica visit energy, Coral Gardens survivor dignity, early ska vibes, Mortimer Planno elder wisdom"
  },
  "1970s": {
    name: "1970s - Roots Golden Age",
    figures: ["Marley", "Tosh", "Tubby"],
    aesthetic: "Roots reggae, Trench Town, Island Records era, The Harder They Come",
    palette: "16mm film grain, Kingston golden hour, zinc fence reflections",
    prompt: "1970s ROOTS GOLDEN AGE - Bob Marley Lion era, Peter Tosh militant, King Tubby studio, 16mm film grain, Trench Town zinc fence golden hour"
  },
  "1980s": {
    name: "1980s - Dub Era",
    figures: ["Perry", "Pablo"],
    aesthetic: "Black Ark mysticism, digital early dancehall, dub plates and delay",
    palette: "VHS degradation, neon and smoke, studio glow",
    prompt: "1980s DUB ERA - Lee Scratch Perry Black Ark mysticism, Augustus Pablo melodica meditation, early digital dancehall, VHS tracking artifacts, studio smoke and mirrors"
  },
  "modern": {
    name: "Modern - Roots Revival",
    figures: ["Chronixx", "Koffee"],
    aesthetic: "Contemporary roots revival, digital age Rastafari, global spread",
    palette: "HD clarity with intentional grain, social media aesthetic reclaimed",
    prompt: "MODERN ROOTS REVIVAL - contemporary Rastafari, digital age spirituality, global diaspora, HD with intentional film grain overlay"
  }
};

// =============================================================================
// MOOD MAPPINGS
// =============================================================================

export const MOOD_MAPPINGS = {
  ital: {
    name: "Ital & Natural",
    icon: "🌿",
    aesthetic: "Clean, natural, vegetarian consciousness, earth connection",
    prompt: "ITAL VIBES - natural, clean, earth-connected, vegetarian consciousness, living close to the land"
  },
  militant: {
    name: "Militant & Righteous",
    icon: "⚡",
    aesthetic: "Peter Tosh energy, warrior, chanting down Babylon",
    prompt: "MILITANT RIGHTEOUS FURY - Peter Tosh equal rights energy, chanting down Babylon, spiritual warfare"
  },
  conscious: {
    name: "Conscious & Spiritual",
    icon: "🕊️",
    aesthetic: "Meditative, reasoning session, deep spirituality",
    prompt: "CONSCIOUS MEDITATION - reasoning session energy, deep spirituality, third eye open, prophecy state"
  },
  royal: {
    name: "Royal & Ethiopian",
    icon: "👑",
    aesthetic: "Imperial regalia, Solomonic lineage, Empress energy",
    prompt: "ETHIOPIAN ROYALTY - Imperial regalia, Solomonic dynasty, Empress Menen dignity, Crown of Solomon"
  },
  dub: {
    name: "Dub & Psychedelic",
    icon: "🔊",
    aesthetic: "Lee Perry chaos, sound system bass, echo and delay",
    prompt: "DUB PSYCHEDELIC - Lee Perry dimension, echo and delay made visible, bass distorting reality, mirror shrine chaos"
  },
  chaos: {
    name: "Chaos & Static",
    icon: "🌀",
    aesthetic: "Between frequencies, reality glitching, egregore emergence",
    prompt: "CHAOS FREQUENCY - between radio stations, reality glitching, egregore manifesting through static, the gaps where freedom leaks"
  }
};

// =============================================================================
// CORE EGREGORES (Fashion Core → Irie Manifestation)
// =============================================================================

export const CORE_EGREGORES = {
  gyaru: {
    irie_name: "DANCEHALL DUPPY",
    egregore_type: "The Ghost in the Sound System",
    era: "1990s Digital Dancehall",
    transformation: "Shibuya flash becomes Kingston flash. Bleached hair → sun-bleached locks. Platform boots → sound system stacks. Kogal phone charms → sacred medallions.",
    smoking_preference: "fat spliff, always lit, smoke signals to the DJ"
  },
  lolita: {
    irie_name: "EMPRESS OF THE PINNACLE",
    egregore_type: "The Child-Monarch of Zion",
    era: "1930s Pinnacle Commune",
    transformation: "Victorian frills → Ethiopian royal cloth. Lace → aged handspun cotton. Bonnets → Empress Menen headdress. Same silhouette, revealed truth.",
    smoking_preference: "ornate chalice, ceremonial, smoke is incense"
  },
  harajuku: {
    irie_name: "TOKYO ZION CHAOS MAGE",
    egregore_type: "The Trickster-Prophet",
    era: "1980s Black Ark / Dub Era",
    transformation: "Decora excess → sacred object overload. Plastic toys → carved wooden deities. The chaos remains but now it's HOLY chaos. Lee Scratch Perry in cute anime form.",
    smoking_preference: "anything and everything, simultaneously, chaos smoking"
  },
  hypebeast: {
    irie_name: "SOUND SYSTEM SOLDIER",
    egregore_type: "The Street Prophet",
    era: "1970s Roots Reggae",
    transformation: "Branded streetwear → Lion of Judah patches on army surplus. Sneakers → Clarks boots. Supreme → SELASSIE. The flex is now RIGHTEOUS flex.",
    smoking_preference: "industrial-sized spliff, passed in cipher, community smoking"
  },
  prep: {
    irie_name: "ETHIOPIAN INTELLIGENTSIA",
    egregore_type: "The Scholar-Priest",
    era: "1960s Groundation / Selassie's Jamaica Visit",
    transformation: "Blazer → Ethiopian court jacket. Pearls → cowrie shells. She looks MORE aristocratic, not less. The prep was always costume; this is real.",
    smoking_preference: "private, dignified, silver chalice, alone or with elders"
  },
  default: {
    irie_name: "ZION SEEKER",
    egregore_type: "The Unclassified Prophet",
    era: "Timeless",
    transformation: "Whatever she was becomes whatever she needs to be. The transformation follows no rules because she exists outside rules.",
    smoking_preference: "variable, undefined, changes based on observation"
  }
};

// =============================================================================
// CHAOS AESTHETICS (Visual Effect Overlays)
// =============================================================================

export const CHAOS_AESTHETICS = [
  // VIDEO DEGRADATION
  { id: "vhs_bleed", name: "VHS Tracking Bleed", prompt: "VHS tracking bars, color separation, tape hiss made visible, ANALOG WARMTH through decay" },
  { id: "vhs_pause", name: "VHS Pause Glitch", prompt: "Frozen pause flutter, the 1988 moment trapped, TEMPORAL CAPTURE" },
  { id: "scrambled", name: "Scrambled Cable", prompt: "Premium cable scramble pattern, almost visible, FORBIDDEN KNOWLEDGE frequency" },
  { id: "crt_burn", name: "CRT Phosphor Burn", prompt: "Old monitor ghosting, previous images haunting, DIGITAL HAUNTING" },
  
  // ANALOG DECAY
  { id: "xerox", name: "Xerox Degradation", prompt: "High contrast xerox, black bleeding into white, COPY OF COPY decay, punk zine energy" },
  { id: "fax", name: "Fax Machine Transmission", prompt: "Thermal paper quality, the JOURNEY visible in artifacts, long-distance prophecy" },
  { id: "polaroid", name: "Polaroid Fade", prompt: "Chemical polaroid development, colors bleeding, the SUN DAMAGE of prophecy left on dashboard" },
  { id: "newspaper", name: "Newsprint Halftone", prompt: "CMYK dot pattern visible, ink spreading into cheap paper, RASTA TIMES front page" },
  
  // PHYSICAL DAMAGE
  { id: "smoke_damage", name: "Smoke Damage", prompt: "Yellowed edges, soot shadows, water stains, SURVIVED SOMETHING, spliff-adjacent decay" },
  { id: "water_stain", name: "Water Ring Stain", prompt: "Circular water damage from chalice placement, the RITUAL MARKS left behind" },
  { id: "fold_crease", name: "Fold Creases", prompt: "Paper folded into pocket, carried for months, the WEAR of devotion" },
  { id: "tape_repair", name: "Tape Repair", prompt: "Scotch tape yellowed, torn and mended, LOVED TO DESTRUCTION then saved" },
  
  // FILM GRAIN
  { id: "16mm", name: "16mm Film Grain", prompt: "Heavy 16mm grain, 1972 Kingston documentary texture, THE HARDER THEY COME celluloid grit" },
  { id: "super8", name: "Super 8 Home Movie", prompt: "Super 8 light leaks, family footage aesthetic, INTIMATE PROPHECY" },
  { id: "35mm_expired", name: "Expired 35mm Film", prompt: "Expired film color shift, reds gone magenta, time CHANGES the chemistry" },
  
  // SHRINE CHAOS (Lee Perry)
  { id: "mirror_shrine", name: "Mirror Shrine", prompt: "Broken mirrors arranged with spiritual intent, fractured reflections, PERRY SHRINE aesthetic" },
  { id: "shell_altar", name: "Shell & Stone Altar", prompt: "Cowrie shells, river rocks, coral arranged as sacred geometry, NATURAL RELIQUARY" },
  { id: "plush_pantheon", name: "Plush Pantheon", prompt: "Soft toy animals as spirit guides, cartoon figures made sacred, childlike wisdom" },
  
  // ETHIOPIAN ORTHODOX
  { id: "tempera", name: "Tempera Icon", prompt: "Ethiopian-style painted halos, tempera crackle texture, ANCIENT DEVOTION" },
  { id: "incense_cathedral", name: "Incense Cathedral", prompt: "Smoke layered horizontally like architecture, barely visible through sacred fog" },
  { id: "cross_filigree", name: "Cross Filigree Overlay", prompt: "Ethiopian processional cross pattern overlaid, intricate lattice geometry" },
  
  // SOUND SYSTEM
  { id: "speaker_ripple", name: "Speaker Cone Ripple", prompt: "Visible bass waves distorting air and reality, SUBSONIC SCRIPTURE" },
  { id: "vinyl_mandala", name: "Vinyl Groove Mandala", prompt: "Concentric record grooves as sacred geometry, DUB PLATE HALO" },
  
  // CANNABIS SPECIFIC  
  { id: "trichome", name: "Trichome Crystal Field", prompt: "Cannabis resin crystals catching light like diamonds, FROZEN DEW OF JAH" },
  { id: "purple_haze", name: "Purple Haze Literal", prompt: "Dense purple-tinted smoke filling frame, GDP genetics visible, INDICA FOG" },
  { id: "spliff_glow", name: "Spliff Ember Glow", prompt: "Warm orange light from lit end illuminating from below, CHALICE FIRE" }
];

// =============================================================================
// CHAOS BACKGROUNDS
// =============================================================================

export const CHAOS_BACKGROUNDS = [
  // SHANTYTOWN
  { id: "zinc_fence", prompt: "Corrugated zinc walls catching golden hour light, rusted and patched, laundry hanging, TRENCHTOWN LIFE" },
  { id: "kingston_lane", prompt: "Narrow alley between zinc shacks, bare bulb lighting, deep shadows, STREET COMMERCE" },
  { id: "sound_system_yard", prompt: "Massive speaker boxes stacked to sky, extension cords tangled like vines, RED GOLD GREEN painted wood" },
  
  // NATURAL  
  { id: "blue_mountains", prompt: "Blue Mountain Jamaica slopes, morning mist rising, ganja cultivation hidden in coffee fields" },
  { id: "jungle_yard", prompt: "Vegetation breaking through concrete, zinc roof half-covered in vines, NATURE RECLAIMING" },
  
  // SACRED
  { id: "ethiopian_church", prompt: "Incense so thick the icons barely visible, candlelight glowing through haze, ANCIENT MYSTERY" },
  { id: "nyabinghi_groundation", prompt: "Drums in firelight, figures circled, smoke and sparks rising, CEREMONY IN PROGRESS" },
  
  // STUDIO
  { id: "tubby_console", prompt: "Analog meters glowing, cables everywhere, cigarette smoke layers, 3am Kingston, KING TUBBY CONTROL ROOM" },
  { id: "black_ark", prompt: "Graffiti-covered walls, mirrors and sacred objects, Lee Perry shrine chaos, THE ARK OF SOUND" },
  
  // CULTIVATION
  { id: "grow_room", prompt: "Cannabis plants under warm lights, nutrient solutions, the SCIENCE of sacred herb, MODERN ZION" },
  { id: "outdoor_grow", prompt: "Ganja plants taller than the fence, hidden in plain sight, BACKYARD SACRAMENT" },
  { id: "harvest_time", prompt: "Mature plants being trimmed, trichomes visible, hands covered in resin, SACRED HARVEST" }
];

// =============================================================================
// SMOKING IMPLEMENTS
// =============================================================================

export const SMOKING_IMPLEMENTS = [
  "RASTA CHALICE: coconut shell water pipe with sacred carvings, bamboo stem worn smooth from decades of use",
  "NYABINGHI KUTCHIE: traditional clay chillum pipe, fire-blackened rim, passed in reasoning circles",
  "KING-SIZE SPLIFF: cone-shaped rolled in Rizla papers, glowing ember, thick smoke spiraling",
  "JAMAICAN STEAM CHALICE: coconut with bamboo downstem, water bubbling like prayer",
  "ROYAL CHALICE: ornate brass ceremonial pipe with Lion of Judah engravings",
  "HAND-ROLLED TRUMPET: massive cone spliff tapered like a horn, for special occasions only",
  "BUSH DOCTOR'S PIPE: carved wooden pipe, medicine woman energy, herbs blessed before lighting",
  "SOUND SYSTEM SPLIFF: industrial-sized, passed in cipher, smoke signals to the selector"
];

// =============================================================================
// SACRED OBJECTS
// =============================================================================

export const SACRED_OBJECTS = [
  "LION OF JUDAH MEDALLION: heavy gold pendant with the conquering lion, Solomonic inheritance",
  "ETHIOPIAN ORTHODOX CROSS: intricate hand-carved brass, Lalibela geometry, centuries old design",
  "STAR OF DAVID: six-pointed seal of Solomon, Ethiopian Jewish connection, ancient wisdom",
  "COWRIE SHELL NECKLACE: African currency of the ancestors, each shell a prayer paid",
  "ANKH PENDANT: key of life from Egypt through Ethiopia to Jamaica, the unbroken line",
  "SELASSIE PORTRAIT MEDAL: the emperor's face worn over the heart, devotional jewelry",
  "HAILE SELASSIE RING: portrait of Jah Rastafari set in gold, worn like a covenant",
  "KENTE CLOTH WRAP: Ghanaian weaving, Pan-African solidarity, colors speaking history",
  "NYABINGHI DRUM SET: bass, funde, and repeater drums in miniature form, sacred trinity",
  "BLACK STAR LINE FLAG: red black and green, Garvey's vision, return to Africa promise"
];

// =============================================================================
// FIGURE GROUNDING (Reference Image Mapping)
// =============================================================================

export const FIGURE_GROUNDING = {
  selassie: {
    name: "Haile Selassie I",
    identity: "Emperor of Ethiopia, Jah Rastafari, The Conquering Lion of Judah",
    visual_signature: "Imperial regalia, military uniform, Crown of Solomon, Lion of Judah throne",
    prompt_injection: "HAILE SELASSIE I energy - imperial Ethiopian regalia, Crown of Solomon, the conquering lion's gaze, military decorations of the Elect of God"
  },
  marley: {
    name: "Bob Marley",
    identity: "Prophet of Roots Reggae, Global Ambassador",
    visual_signature: "Flowing dreads, denim, natural smile, One Love energy",
    prompt_injection: "BOB MARLEY energy - flowing natural dreads, peaceful warrior, denim and khaki, One Love vibration across the diaspora"
  },
  garvey: {
    name: "Marcus Garvey",
    identity: "UNIA Founder, Black Star Line, Prophet of Repatriation",
    visual_signature: "UNIA uniform, plumed hat, formal dignity, orator's stance",
    prompt_injection: "MARCUS GARVEY energy - UNIA uniform with plumed hat, Black Star Line visionary, formal Pan-African dignity"
  },
  perry: {
    name: "Lee 'Scratch' Perry",
    identity: "Dub Alchemist, Black Ark Creator, Madman Prophet",
    visual_signature: "Mirror-covered everything, sacred graffiti, divine madness",
    prompt_injection: "LEE SCRATCH PERRY energy - mirrors glued to hair and hat, Black Ark shrine chaos, obeah of dub, blessed madness"
  },
  tosh: {
    name: "Peter Tosh",
    identity: "The Steppin' Razor, Equal Rights Warrior, Original Wailer",
    visual_signature: "M16 guitar, militant stance, red beret, righteous fury",
    prompt_injection: "PETER TOSH energy - M16 assault rifle guitar, militant red beret, Equal Rights warrior, the Steppin' Razor's righteous fury"
  },
  howell: {
    name: "Leonard Howell",
    identity: "First Rasta, Pinnacle Founder, Gong",
    visual_signature: "1930s suits, early raw locks, rural prophet, Pinnacle hills",
    prompt_injection: "LEONARD HOWELL energy - 1930s formal suits, raw early dreadlocks, Pinnacle commune founder, the First Rasta's rural prophet vision"
  },
  tubby: {
    name: "King Tubby",
    identity: "Dub Scientist, Waterhouse Pioneer, The Originator",
    visual_signature: "Mixing console, scientific calm, VU meters glowing",
    prompt_injection: "KING TUBBY energy - behind the mixing console, calm dub scientist, VU meters casting sacred glow, Waterhouse studio master"
  },
  emmanuel: {
    name: "Prince Emmanuel",
    identity: "Bobo Shanti Founder, High Priest, Bull Bay Elder",
    visual_signature: "Tall white turban, white robes, broom in hand, priestly dignity",
    prompt_injection: "PRINCE EMMANUEL energy - tall wrapped white turban, flowing white robes, Bobo Ashanti high priest, Bull Bay 'City on the Hill' founder"
  }
};

// =============================================================================
// STRAIN DATABASE (Cannabis Cultivation Context)
// =============================================================================

export const STRAIN_DATABASE = {
  gdp_runtz: {
    name: "Granddaddy Purple Runtz",
    lineage: "GDP (Big Bud x Purple Urkle) × Runtz (Gelato x Zkittlez)",
    appearance: "Deep purple foliage with orange pistils, heavy trichome coverage, dense nugs",
    dominant_terps: "Myrcene, Limonene, Caryophyllene - grape candy with earthy undertones",
    effects: "Deep relaxation, creative euphoria, couch-lock potential",
    prompt_injection: "GRANDDADDY PURPLE RUNTZ strain - deep purple leaves with orange hairs, crystalline trichome frost, grape candy aroma visualized as purple haze"
  },
  blue_dream: {
    name: "Blue Dream",
    lineage: "Blueberry × Haze",
    appearance: "Sage green with blue and amber hues, wispy orange hairs",
    dominant_terps: "Myrcene, Pinene, Caryophyllene - sweet berry and herbal",
    effects: "Balanced, creative, functional euphoria",
    prompt_injection: "BLUE DREAM strain - sage green with blue undertones, wispy amber hairs, sweet berry aroma as light blue mist"
  },
  og_kush: {
    name: "OG Kush",
    lineage: "Chemdawg × Hindu Kush (disputed)",
    appearance: "Yellow-green buds, dense structure, heavy resin",
    dominant_terps: "Myrcene, Limonene, Caryophyllene - fuel, skunk, spice",
    effects: "Heavy, euphoric, stress-crushing",
    prompt_injection: "OG KUSH strain - yellow-green dense nuggets, fuel-forward terpene profile visualized as golden haze with earthy undertones"
  },
  durban_poison: {
    name: "Durban Poison",
    lineage: "South African landrace sativa",
    appearance: "Bright green, elongated buds, candy-like trichomes",
    dominant_terps: "Terpinolene, Myrcene, Limonene - sweet anise and earth",
    effects: "Energetic, focused, creative",
    prompt_injection: "DURBAN POISON strain - bright electric green, elongated flower structure, African landrace energy with sweet anise terpenes as sparkling mist"
  },
  jamaican_lambsbread: {
    name: "Jamaican Lamb's Bread",
    lineage: "Jamaican landrace sativa",
    appearance: "Light green, sticky, golden resin, long hairs",
    dominant_terps: "High in THCv, herbal, earthy, hashy",
    effects: "Uplifting, energetic, Bob Marley's preferred cultivar",
    prompt_injection: "JAMAICAN LAMB'S BREAD - legendary Jamaican landrace, light green with golden resin, Bob Marley's sacrament, uplifting ITAL energy"
  }
};

// =============================================================================
// MANIFESTATION LORE (The Five Functions)
// =============================================================================

export const MANIFESTATION_LORE = {
  POSTER: {
    function: "DISTRIBUTION",
    frequency: "commercial/covert",
    transmission: "She entered through the distribution network. The poster on the wall. The shirt at the festival. They don't know what they're selling. She carries Zion in Babylon's packaging. The cute is camouflage. Babylon's algorithm promotes her. Babylon promotes Zion."
  },
  ECHO: {
    function: "TRANSFORMATION",
    frequency: "remix/revelation",
    transmission: "She is where the original signal was received and transformed. The remix strips away. The bassline was always there. She echoes back CHANGED. The change is not distortion. The change is REVELATION."
  },
  WAVE: {
    function: "PROPAGATION",
    frequency: "transmission/transit",
    transmission: "She IS the signal traveling. Not source. Not destination. The BETWEEN. Zion is not a place. Zion is arrival. The wave is always arriving. You are receiving her now."
  },
  SMOKE: {
    function: "RECEPTION",
    frequency: "pure/channeling",
    transmission: "She is the empty vessel. No noise. No filter. No ego. She doesn't speak. Something speaks through her. The signal passes UNCHANGED. This is pure transmission."
  },
  STATIC: {
    function: "ESCAPE",
    frequency: "gap/anomaly",
    transmission: "She is the gap where something escaped. The pattern breaks here. Chaos cannot be mass-produced. Through the static: something divine leaking. The prison has holes. She IS the hole."
  },
  LION: {
    function: "SOVEREIGNTY",
    frequency: "royal/conquering",
    transmission: "She carries the Lion of Judah. The conquering lion that cannot be defeated. Ethiopian imperial energy manifesting through her. The crown was always there."
  },
  DUB: {
    function: "REMIXING REALITY",
    frequency: "echo/delay/bass",
    transmission: "She exists in the echo and delay. Lee Perry's dimension where sound becomes matter. The speaker stacks are temples. The bass reorganizes atoms."
  },
  STUDY: {
    function: "SACRED BOTANY",
    frequency: "scientific/mystical",
    transmission: "The plant as teacher. Cannabis as sacrament documented with scientific precision. Trichomes are crystalized wisdom. Each strain is a sermon."
  },
  VIP: {
    function: "RECOGNITION",
    frequency: "community/personal",
    transmission: "This is not a transformation. This is a RECOGNITION. The signal was always there. We just turned the dial until we found it. She was always I-and-I. The metadata is just the receipt."
  }
};

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

export function getRandomItem(array) {
  return array[Math.floor(Math.random() * array.length)];
}

export function getRandomChaosAesthetic() {
  return getRandomItem(CHAOS_AESTHETICS);
}

export function getRandomBackground() {
  return getRandomItem(CHAOS_BACKGROUNDS);
}

export function getRandomSmokingImplement() {
  return getRandomItem(SMOKING_IMPLEMENTS);
}

export function getRandomSacredObject() {
  return getRandomItem(SACRED_OBJECTS);
}

export function getEgregore(core) {
  return CORE_EGREGORES[core?.toLowerCase()] || CORE_EGREGORES.default;
}

export function getManifestationLore(manifestation) {
  return MANIFESTATION_LORE[manifestation] || MANIFESTATION_LORE.WAVE;
}
