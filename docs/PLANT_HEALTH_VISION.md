# Plant Health Detection via Computer Vision

Comprehensive guide for detecting cannabis plant health issues using computer vision and image analysis techniques.

## Overview

Computer vision can identify plant health issues before they become critical, enabling proactive intervention. This document outlines visual symptoms, detection techniques, and implementation approaches for an AI-autonomous cultivation system.

---

## Detection Categories

1. **Nutrient Deficiencies**
2. **Pest Infestations**
3. **Diseases**
4. **Environmental Stress**
5. **Watering Issues**
6. **Harvest Timing (Trichome Analysis)**

---

## 1. Nutrient Deficiency Detection

### Nitrogen (N) Deficiency

**Visual Symptoms:**
- **Early Stage:** Lower leaves turn light green, then yellow
- **Progression:** Yellowing spreads upward, leaves become pale green/yellow
- **Advanced:** Leaves become completely yellow, dry out, and fall off
- **Pattern:** Starts from bottom of plant, moves upward
- **Leaf Shape:** Leaves may curl downward slightly

**Color Analysis:**
- **Healthy:** RGB values show green dominance (G > R, G > B)
- **Deficient:** Yellowing shows increased R and B relative to G
- **Threshold:** G/(R+B) ratio drops below 1.2 (normal ~1.5-2.0)

**Detection Algorithm:**
```python
def detect_nitrogen_deficiency(image):
    # Convert to HSV for better color analysis
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    
    # Extract green channel dominance
    green_ratio = calculate_green_dominance(image)
    
    # Check lower leaves first (bottom 1/3 of plant)
    lower_region = image[image.shape[0]*2//3:, :]
    lower_yellowing = detect_yellowing(lower_region)
    
    # Nitrogen deficiency if:
    # - Green ratio < 1.2 in lower leaves
    # - Yellowing pattern starts from bottom
    if green_ratio < 1.2 and lower_yellowing > 0.3:
        return "NITROGEN_DEFICIENCY", confidence=0.8
```

**Severity Levels:**
- **Mild:** 20-30% of lower leaves yellowing
- **Moderate:** 30-50% yellowing, spreading upward
- **Severe:** >50% yellowing, leaves dropping

---

### Phosphorus (P) Deficiency

**Visual Symptoms:**
- **Early Stage:** Dark green leaves with purple/reddish stems
- **Progression:** Leaves develop dark purple/reddish-brown patches
- **Advanced:** Leaves become dark purple/black, curl downward
- **Pattern:** Affects older leaves first, but can appear throughout
- **Leaf Shape:** Leaves curl and may become brittle

**Color Analysis:**
- **Healthy:** Green with minimal purple/red
- **Deficient:** Increased purple/red channels in leaf tissue
- **Threshold:** Purple/red intensity > 0.3 in leaf areas

**Detection Algorithm:**
```python
def detect_phosphorus_deficiency(image):
    # Detect purple/reddish coloration in leaves
    purple_mask = detect_purple_coloration(image)
    
    # Check for darkening (reduced brightness)
    brightness = calculate_brightness(image)
    
    # Phosphorus deficiency if:
    # - Purple/red patches in leaves
    # - Overall darkening
    # - Downward leaf curl
    if purple_mask > 0.25 and brightness < 0.4:
        return "PHOSPHORUS_DEFICIENCY", confidence=0.75
```

---

### Potassium (K) Deficiency

**Visual Symptoms:**
- **Early Stage:** Leaf edges turn yellow/brown (marginal chlorosis)
- **Progression:** Yellow/brown edges spread inward, leaf tips curl
- **Advanced:** Leaf edges become necrotic (brown/dead), leaves curl upward
- **Pattern:** Affects older leaves first, edges and tips
- **Leaf Shape:** Upward curling, "burnt" edges

**Color Analysis:**
- **Healthy:** Uniform green throughout leaf
- **Deficient:** Yellow/brown edges with green center
- **Edge Detection:** High contrast at leaf margins

**Detection Algorithm:**
```python
def detect_potassium_deficiency(image):
    # Detect leaf edges
    edges = cv2.Canny(image, 50, 150)
    
    # Analyze color at leaf margins
    margin_colors = extract_margin_colors(image, edges)
    
    # Check for yellow/brown at edges
    yellow_brown_ratio = detect_yellow_brown(margin_colors)
    
    # Potassium deficiency if:
    # - Yellow/brown edges > 30% of leaf perimeter
    # - Upward leaf curl
    if yellow_brown_ratio > 0.3:
        return "POTASSIUM_DEFICIENCY", confidence=0.7
```

---

### Calcium (Ca) Deficiency

**Visual Symptoms:**
- **Early Stage:** New growth shows distorted, twisted leaves
- **Progression:** Brown spots/patches on leaves, especially new growth
- **Advanced:** New leaves become necrotic, growth stunted
- **Pattern:** Affects new growth first (top of plant)
- **Leaf Shape:** Distorted, twisted, "hooked" new leaves

**Color Analysis:**
- **Healthy:** Uniform green new growth
- **Deficient:** Brown spots/patches in new leaves
- **Pattern:** Concentrated in new growth areas

**Detection Algorithm:**
```python
def detect_calcium_deficiency(image):
    # Focus on new growth (top 1/3 of plant)
    new_growth = image[:image.shape[0]//3, :]
    
    # Detect brown necrotic spots
    brown_spots = detect_brown_necrosis(new_growth)
    
    # Check for leaf distortion
    distortion = measure_leaf_distortion(new_growth)
    
    # Calcium deficiency if:
    # - Brown spots in new growth
    # - Distorted leaf shape
    if brown_spots > 0.15 and distortion > 0.2:
        return "CALCIUM_DEFICIENCY", confidence=0.8
```

---

### Magnesium (Mg) Deficiency

**Visual Symptoms:**
- **Early Stage:** Interveinal chlorosis (yellowing between veins)
- **Progression:** Yellow patches between green veins, "marbled" appearance
- **Advanced:** Entire leaf yellow except veins, leaves may curl
- **Pattern:** Affects older leaves first
- **Leaf Shape:** May curl upward or downward

**Color Analysis:**
- **Healthy:** Uniform green
- **Deficient:** Yellow between green veins
- **Pattern:** Interveinal chlorosis is distinctive

**Detection Algorithm:**
```python
def detect_magnesium_deficiency(image):
    # Detect leaf veins (darker green lines)
    veins = detect_veins(image)
    
    # Analyze color between veins
    interveinal_regions = extract_interveinal_regions(image, veins)
    
    # Check for yellowing between veins
    yellowing_ratio = detect_yellowing(interveinal_regions)
    
    # Magnesium deficiency if:
    # - Yellowing between veins > 40%
    # - Veins remain green
    if yellowing_ratio > 0.4:
        return "MAGNESIUM_DEFICIENCY", confidence=0.85
```

---

### Iron (Fe) Deficiency

**Visual Symptoms:**
- **Early Stage:** New growth shows interveinal chlorosis
- **Progression:** Yellowing between veins in new leaves
- **Advanced:** New leaves become almost white, veins remain green
- **Pattern:** Affects new growth first (opposite of Mg)
- **Leaf Shape:** New leaves may be smaller

**Color Analysis:**
- **Healthy:** Green new growth
- **Deficient:** Yellow/white new growth with green veins
- **Pattern:** New growth affected, old growth normal

**Detection Algorithm:**
```python
def detect_iron_deficiency(image):
    # Focus on new growth
    new_growth = image[:image.shape[0]//3, :]
    
    # Detect interveinal chlorosis in new leaves
    interveinal_yellowing = detect_interveinal_chlorosis(new_growth)
    
    # Iron deficiency if:
    # - New growth shows interveinal chlorosis
    # - Old growth appears normal
    if interveinal_yellowing > 0.5:
        return "IRON_DEFICIENCY", confidence=0.75
```

---

## 2. Pest Identification

### Spider Mites

**Visual Symptoms:**
- **Webbing:** Fine silk webbing on leaves and stems
- **Stippling:** Tiny white/yellow dots on leaves (feeding damage)
- **Pattern:** Damage appears as speckled/mottled leaves
- **Location:** Underside of leaves, webbing visible

**Detection Algorithm:**
```python
def detect_spider_mites(image):
    # Detect fine webbing (thin white lines)
    webbing = detect_webbing(image, min_length=10, max_width=2)
    
    # Detect stippling (tiny white/yellow dots)
    stippling = detect_stippling(image, dot_size=1-3)
    
    # Check underside of leaves (if available)
    # Spider mites if:
    # - Webbing detected
    # - Stippling pattern present
    if webbing > 0.1 or stippling > 0.2:
        return "SPIDER_MITES", confidence=0.9
```

**Image Processing:**
- Use edge detection for webbing
- Blob detection for mite bodies (if visible)
- Pattern recognition for stippling damage

---

### Thrips

**Visual Symptoms:**
- **Damage:** Silvery streaks/scratches on leaves
- **Feces:** Black dots (thrip feces) on leaves
- **Pattern:** Linear damage marks
- **Location:** Upper surface of leaves

**Detection Algorithm:**
```python
def detect_thrips(image):
    # Detect silvery streaks (linear damage)
    streaks = detect_linear_damage(image, orientation='any')
    
    # Detect black fecal spots
    black_spots = detect_black_spots(image, size=1-2)
    
    # Thrips if:
    # - Silvery streaks present
    # - Black fecal spots detected
    if streaks > 0.15 or black_spots > 0.1:
        return "THRIPS", confidence=0.8
```

---

### Aphids

**Visual Symptoms:**
- **Bodies:** Small green/black/yellow insects on leaves/stems
- **Honeydew:** Sticky substance on leaves (shiny appearance)
- **Sooty Mold:** Black mold growing on honeydew
- **Location:** Underside of leaves, new growth

**Detection Algorithm:**
```python
def detect_aphids(image):
    # Detect insect bodies (small oval shapes)
    insects = detect_insect_bodies(image, size_range=(2, 5))
    
    # Detect honeydew (shiny/reflective areas)
    honeydew = detect_reflective_surfaces(image)
    
    # Detect sooty mold (black patches)
    sooty_mold = detect_black_patches(image)
    
    # Aphids if:
    # - Small insects detected
    # - Honeydew present
    # - Sooty mold may be present
    if insects > 0.05 or (honeydew > 0.1 and sooty_mold > 0.05):
        return "APHIDS", confidence=0.85
```

---

### Fungus Gnats

**Visual Symptoms:**
- **Adults:** Small black flies around soil/plant base
- **Larvae:** White/transparent worms in soil (not visible in leaf images)
- **Damage:** Usually minimal on leaves, but can indicate overwatering

**Detection Algorithm:**
```python
def detect_fungus_gnats(image):
    # Detect small black flies (if in frame)
    flies = detect_small_insects(image, color='black', size=2-4)
    
    # Usually detected via soil monitoring, not leaf images
    # But can indicate overwatering if present
    if flies > 0.02:
        return "FUNGUS_GNATS", confidence=0.6
```

---

## 3. Disease Identification

### Powdery Mildew

**Visual Symptoms:**
- **Appearance:** White powdery coating on leaves
- **Pattern:** Starts as small white spots, spreads to cover leaves
- **Texture:** Powdery, flour-like appearance
- **Location:** Upper surface of leaves, can spread to stems

**Detection Algorithm:**
```python
def detect_powdery_mildew(image):
    # Convert to grayscale for texture analysis
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Detect white powdery patches
    white_patches = detect_white_patches(image, min_size=5)
    
    # Texture analysis (powdery texture)
    texture = analyze_texture(gray, method='LBP')
    powdery_texture = detect_powdery_texture(texture)
    
    # Powdery mildew if:
    # - White patches present
    # - Powdery texture detected
    if white_patches > 0.1 or powdery_texture > 0.3:
        return "POWDERY_MILDEW", confidence=0.9
```

**Color Analysis:**
- White patches: RGB values close to (255, 255, 255)
- Distinct from healthy green leaves

---

### Bud Rot (Botrytis)

**Visual Symptoms:**
- **Early Stage:** Gray/brown patches on buds
- **Progression:** Buds become mushy, gray mold visible
- **Advanced:** Entire bud rots, white/gray mycelium visible
- **Location:** Inside dense buds, hard to detect early

**Detection Algorithm:**
```python
def detect_bud_rot(image):
    # Focus on bud areas
    buds = detect_bud_regions(image)
    
    # Detect gray/brown discoloration in buds
    discoloration = detect_gray_brown_patches(buds)
    
    # Texture analysis (mushy/rotten texture)
    texture = analyze_texture(buds)
    mushy_texture = detect_mushy_texture(texture)
    
    # Bud rot if:
    # - Gray/brown patches in buds
    # - Mushy texture
    if discoloration > 0.15 or mushy_texture > 0.2:
        return "BUD_ROT", confidence=0.85
```

**Challenges:**
- Hard to detect early (inside dense buds)
- May require thermal imaging or close-up inspection
- High humidity indicator

---

### Root Rot

**Visual Symptoms:**
- **Above Ground:** Wilting, yellowing leaves, stunted growth
- **Below Ground:** Brown/black mushy roots (not visible in leaf images)
- **Pattern:** Affects entire plant, not localized

**Detection Algorithm:**
```python
def detect_root_rot_symptoms(image):
    # Root rot shows as general plant decline
    # Wilting detection
    wilting = detect_wilting(image)
    
    # Overall yellowing
    yellowing = detect_overall_yellowing(image)
    
    # Stunted growth (compare to expected size)
    growth_stunting = detect_stunted_growth(image)
    
    # Root rot symptoms if:
    # - Multiple symptoms present
    # - Affects entire plant
    if (wilting > 0.3 and yellowing > 0.4) or growth_stunting:
        return "POSSIBLE_ROOT_ROT", confidence=0.7
```

**Note:** Root rot requires root inspection, but above-ground symptoms can indicate it.

---

## 4. Environmental Stress Detection

### Light Stress (Light Burn/Bleaching)

**Visual Symptoms:**
- **Bleaching:** White/yellow patches on upper leaves
- **Pattern:** Affects leaves closest to light
- **Progression:** Starts as yellowing, becomes white/bleached
- **Location:** Top of plant, upper leaves

**Detection Algorithm:**
```python
def detect_light_stress(image):
    # Focus on upper leaves
    upper_leaves = image[:image.shape[0]//3, :]
    
    # Detect bleaching (white/yellow patches)
    bleaching = detect_bleaching(upper_leaves)
    
    # Check proximity to light (if light position known)
    # Light stress if:
    # - Bleaching in upper leaves
    # - Pattern matches light exposure
    if bleaching > 0.2:
        return "LIGHT_STRESS", confidence=0.8
```

---

### Heat Stress

**Visual Symptoms:**
- **Leaf Curl:** Leaves curl upward (taco shape)
- **Color:** Leaves may appear darker green or develop brown edges
- **Pattern:** Affects upper/new growth first
- **Texture:** Leaves may feel dry/crispy

**Detection Algorithm:**
```python
def detect_heat_stress(image):
    # Detect upward leaf curl
    upward_curl = detect_upward_curl(image)
    
    # Check for brown edges (heat damage)
    brown_edges = detect_brown_edges(image)
    
    # Heat stress if:
    # - Upward curling > 30%
    # - Brown edges present
    if upward_curl > 0.3 or brown_edges > 0.2:
        return "HEAT_STRESS", confidence=0.75
```

---

### Cold Stress

**Visual Symptoms:**
- **Color:** Purple/reddish coloration (especially stems)
- **Growth:** Stunted, slow growth
- **Leaves:** May droop, dark green color
- **Pattern:** Affects entire plant

**Detection Algorithm:**
```python
def detect_cold_stress(image):
    # Detect purple/reddish coloration
    purple_red = detect_purple_red_coloration(image)
    
    # Check for stunted growth
    growth_stunting = detect_stunted_growth(image)
    
    # Cold stress if:
    # - Purple/red coloration
    # - Stunted growth
    if purple_red > 0.25 or growth_stunting:
        return "COLD_STRESS", confidence=0.7
```

---

## 5. Watering Issues

### Overwatering

**Visual Symptoms:**
- **Drooping:** Leaves droop downward
- **Color:** Dark green, may show signs of nutrient lockout
- **Texture:** Leaves feel soft/mushy
- **Pattern:** Affects entire plant

**Detection Algorithm:**
```python
def detect_overwatering(image):
    # Detect downward drooping
    drooping = detect_drooping(image, direction='down')
    
    # Check for dark green color (nutrient issues)
    dark_green = detect_dark_green_coloration(image)
    
    # Overwatering if:
    # - Significant drooping
    # - Dark green coloration
    if drooping > 0.4 or dark_green > 0.5:
        return "OVERWATERING", confidence=0.7
```

---

### Underwatering

**Visual Symptoms:**
- **Drooping:** Leaves droop downward (similar to overwatering)
- **Color:** Leaves may appear lighter green or yellow
- **Texture:** Leaves feel dry/crispy
- **Pattern:** Affects entire plant

**Detection Algorithm:**
```python
def detect_underwatering(image):
    # Detect drooping
    drooping = detect_drooping(image, direction='down')
    
    # Check for dry/crispy appearance
    dryness = detect_dry_texture(image)
    
    # Check soil moisture (if sensor available)
    # Underwatering if:
    # - Drooping with dry appearance
    # - Low soil moisture
    if drooping > 0.4 and dryness > 0.3:
        return "UNDERWATERING", confidence=0.75
```

**Note:** Combine with soil moisture sensor data for accuracy.

---

### pH Lockout

**Visual Symptoms:**
- **Pattern:** Multiple nutrient deficiency symptoms simultaneously
- **Color:** Various discolorations (yellow, brown, purple)
- **Growth:** Stunted despite feeding
- **Pattern:** Doesn't respond to nutrient adjustments

**Detection Algorithm:**
```python
def detect_ph_lockout(image):
    # Detect multiple deficiency symptoms
    deficiencies = detect_multiple_deficiencies(image)
    
    # pH lockout if:
    # - Multiple deficiencies present
    # - Symptoms don't match single deficiency pattern
    if len(deficiencies) > 2:
        return "PH_LOCKOUT", confidence=0.8
```

**Note:** Requires pH sensor data for confirmation.

---

## 6. Harvest Timing: Trichome Analysis

### Trichome Maturity Stages

**Visual Appearance:**
- **Clear:** Transparent, glass-like (immature)
- **Cloudy/Milky:** White/opaque (peak THC, harvest time)
- **Amber:** Yellow/brown (higher CBN, sedative effects)

**Optimal Harvest:**
- **Energetic High:** 70-80% cloudy, 20-30% clear
- **Balanced:** 70-80% cloudy, 10-20% amber
- **Sedative High:** 50-60% cloudy, 40-50% amber

**Detection Algorithm:**
```python
def analyze_trichomes(image):
    # Requires macro/close-up image of buds
    # Detect trichome heads
    trichomes = detect_trichome_heads(image, size=50-100)
    
    # Classify by color/opacity
    clear = classify_trichomes(trichomes, color='clear')
    cloudy = classify_trichomes(trichomes, color='cloudy')
    amber = classify_trichomes(trichomes, color='amber')
    
    # Calculate percentages
    total = len(trichomes)
    clear_pct = len(clear) / total
    cloudy_pct = len(cloudy) / total
    amber_pct = len(amber) / total
    
    # Determine harvest readiness
    if cloudy_pct >= 0.7 and amber_pct < 0.2:
        return "HARVEST_READY_BALANCED", confidence=0.9
    elif cloudy_pct >= 0.7 and clear_pct <= 0.3:
        return "HARVEST_READY_ENERGETIC", confidence=0.85
    elif amber_pct >= 0.4:
        return "HARVEST_READY_SEDATIVE", confidence=0.9
    else:
        return "NOT_READY", confidence=0.8
```

**Image Requirements:**
- Macro lens or close-up camera
- High resolution (trichomes are ~50-100μm)
- Good lighting (trichomes are reflective)
- Focus on bud surface, not leaves

---

## Implementation Approach

### Image Acquisition

**Camera Setup:**
- **Overview:** Wide-angle for full plant monitoring
- **Close-up:** Macro lens for trichome/leaf detail
- **Positioning:** Multiple angles (top, side, underside)
- **Lighting:** Consistent, full-spectrum LED

**Capture Schedule:**
- **Daily:** Full plant overview
- **Weekly:** Close-up leaf inspection
- **Pre-Harvest:** Daily trichome analysis

### Image Processing Pipeline

```python
class PlantHealthAnalyzer:
    def __init__(self):
        self.nutrient_detector = NutrientDeficiencyDetector()
        self.pest_detector = PestDetector()
        self.disease_detector = DiseaseDetector()
        self.stress_detector = StressDetector()
        self.trichome_analyzer = TrichomeAnalyzer()
    
    def analyze_plant_health(self, image):
        results = {
            'nutrient_deficiencies': [],
            'pests': [],
            'diseases': [],
            'stress_factors': [],
            'harvest_readiness': None
        }
        
        # Nutrient analysis
        results['nutrient_deficiencies'] = self.nutrient_detector.detect_all(image)
        
        # Pest detection
        results['pests'] = self.pest_detector.detect_all(image)
        
        # Disease detection
        results['diseases'] = self.disease_detector.detect_all(image)
        
        # Stress detection
        results['stress_factors'] = self.stress_detector.detect_all(image)
        
        # Trichome analysis (if close-up image)
        if self.is_closeup_image(image):
            results['harvest_readiness'] = self.trichome_analyzer.analyze(image)
        
        return results
```

### Machine Learning Models

**Training Data:**
- Collect labeled images of healthy vs. unhealthy plants
- Use data augmentation (rotation, brightness, contrast)
- Balance dataset across all conditions

**Model Options:**
1. **Custom CNN:** Train from scratch on cannabis-specific data
2. **Transfer Learning:** Fine-tune ResNet, EfficientNet, or Vision Transformer
3. **Object Detection:** YOLO or Faster R-CNN for pest/disease detection
4. **Segmentation:** U-Net for precise leaf/bud region detection

**Recommended Approach:**
- Start with transfer learning (EfficientNet-B3)
- Fine-tune on cannabis-specific dataset
- Use ensemble of models for different conditions

### Integration with Grok AI

**Workflow:**
1. Capture images daily/weekly
2. Run computer vision analysis
3. Send results + images to Grok API
4. Grok interprets results and recommends actions
5. Execute actions via MCP tools

**Prompt for Grok:**
```
Analyze this plant health report from computer vision:
- Nutrient deficiencies detected: [list]
- Pests detected: [list]
- Diseases detected: [list]
- Stress factors: [list]

Provide specific recommendations for:
1. Nutrient adjustments
2. Pest treatment
3. Disease management
4. Environmental corrections
```

---

## Existing APIs and Models

### PlantNet API
- **Purpose:** Plant species identification
- **URL:** https://plantnet.org/
- **Use Case:** Verify plant species, not health issues

### Plant.id API
- **Purpose:** Plant disease identification
- **URL:** https://plant.id/
- **Use Case:** Disease detection (general plants, may need cannabis-specific training)

### Custom Training
- **Recommended:** Train custom models on cannabis-specific data
- **Dataset Sources:**
  - r/microgrowery image submissions
  - Grow journals with labeled issues
  - Academic research datasets (if available)

---

## Color Analysis Techniques

### HSV Color Space
- Better for plant color analysis than RGB
- H (Hue): Dominant color
- S (Saturation): Color intensity
- V (Value): Brightness

### Color Thresholding
```python
def detect_yellowing(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    
    # Yellow range in HSV
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([30, 255, 255])
    
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    yellow_ratio = np.sum(mask > 0) / mask.size
    
    return yellow_ratio
```

### Green Dominance Ratio
```python
def calculate_green_dominance(image):
    r, g, b = cv2.split(image)
    
    # Green dominance = G / (R + B)
    green_dominance = np.mean(g) / (np.mean(r) + np.mean(b) + 1e-6)
    
    return green_dominance
```

---

## Implementation Priority

### Phase 1: Basic Detection
1. Nutrient deficiencies (N, P, K, Mg)
2. Overwatering/underwatering
3. Light stress

### Phase 2: Advanced Detection
1. All nutrient deficiencies
2. Pest detection (spider mites, thrips)
3. Disease detection (powdery mildew)

### Phase 3: Advanced Features
1. Trichome analysis
2. All pests and diseases
3. Machine learning model integration

---

## Sources & References

1. **Grow Weed Easy** - Visual guides for nutrient deficiencies and pests
2. **Royal Queen Seeds** - Disease and pest identification guides
3. **r/microgrowery** - Community image database of plant issues
4. **Academic Papers** - Computer vision for plant health monitoring
5. **Plant Pathology Resources** - Disease symptom databases

---

*Last Updated: 2025-01-12*
*For use with Grok & Mon AI-autonomous cannabis cultivation system*
