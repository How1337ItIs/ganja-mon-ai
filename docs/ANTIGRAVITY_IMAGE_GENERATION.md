# Antigravity Native Image Generation Tools Guide

## Overview

This document focuses on **native Antigravity image generation tools** that work with your Google AI subscription - **no API keys required**. These tools are built into Antigravity and automatically use your Google account authentication.

**Critical Understanding**: Antigravity's agents **automatically decide** which image generation tool to use based on task analysis. By default, **Imagen 3** is used for general-purpose tasks, while **Nano Banana Pro** is selected for high-fidelity requirements. This document explains how to ensure **Nano Banana Pro is always preferred**.

## Available Native Image Generation Tools

### 1. Nano Banana Pro (Gemini 3 Pro Image)

**Status**: ✅ Native, built-in, no setup required  
**Model**: Google Gemini 3 Pro Image  
**Subscription**: Covered by Google AI subscription  
**Best For**: Professional-quality images, UI mockups, system diagrams, high-resolution images

**Key Features**:
- **4K resolution** image generation
- Enhanced text rendering capabilities
- Real-world grounding using Google Search
- "Thinking" process that refines composition before generation
- Consistency across edits
- High-fidelity image generation
- Automatically available to Antigravity agents

**How Agents Access It**:
- **No explicit tool call needed** - agents invoke it automatically when appropriate
- Agents can autonomously decide to use Nano Banana Pro
- Simply describe what image you need in natural language
- Works seamlessly with your Google AI subscription (no API keys)

**Example Usage**:
```
"Generate a UI mockup for a cannabis grow monitoring dashboard"
"Create a system architecture diagram showing the data flow"
"Create a professional product image of a cannabis plant in a grow tent"
```

**Technical Details**:
- Built on Gemini 3 Pro Image model
- Up to 4K resolution output
- Professional asset production capabilities
- Complex instruction handling

---

## Nano Banana Pro: Complete Control Guide

### Aspect Ratio Control

Nano Banana Pro supports various aspect ratios. **Specify the aspect ratio in your prompt** to control the image dimensions:

**Supported Aspect Ratios**:
- **1:1 (Square)** - Social media posts, profile pictures, Instagram posts
- **4:3 (Standard)** - Traditional photography, prints, classic format
- **3:2 (Classic)** - Professional photography, prints
- **4:5 (Portrait)** - Instagram feeds, Facebook images, greeting cards
- **2:3 (Portrait)** - Standard portrait orientation, vertical prints
- **3:4 (Portrait)** - Magazine layouts, portrait prints
- **16:9 (Landscape)** - Videos, presentations, YouTube thumbnails, website headers, widescreen displays
- **9:16 (Vertical)** - Mobile content, Instagram Stories, TikTok, vertical videos
- **9:21 (Tall)** - Ultra-tall format, mobile-first content, special vertical displays
- **21:9 (Ultrawide)** - Cinematic shots, wide displays, dramatic landscapes, panoramic images

**How to Specify Aspect Ratio**:
Include the aspect ratio in your prompt. Examples:
```
"Generate a 4K professional UI mockup for a cannabis grow monitoring dashboard, 16:9 aspect ratio"
"Create a high-resolution system architecture diagram, 21:9 ultrawide format"
"Generate a professional product image, 1:1 square format for social media"
"A cinematic 21:9 wide shot of a futuristic city skyline at blue hour"
```

**Note**: You can also mention the aspect ratio naturally in the description:
- "wide landscape format"
- "vertical portrait orientation"
- "square format"
- "cinematic ultrawide"

---

### Size and Resolution Control

Nano Banana Pro offers three resolution levels. **Always specify resolution in uppercase (e.g., "4K")**:

**Resolution Options**:
- **1K** - ~1024px on the short side (fast, standard quality)
- **2K** - ~2048px on the short side (high quality, balanced)
- **4K** - ~4096px on the short side (maximum quality, professional)

**How to Specify Resolution**:
Always include the resolution in your prompt:
```
"Generate a 4K professional UI mockup..."
"Create a 2K high-resolution system diagram..."
"Generate a 1K quick thumbnail image..."
```

**Important**: 
- Higher resolutions provide better quality but may require more processing time
- Always use uppercase: "4K" not "4k" or "4k resolution"
- Combine with aspect ratio for precise control: "4K, 16:9 aspect ratio"

---

### Detailed Prompt Controls: Professional Features

Nano Banana Pro supports **studio-quality controls** through detailed prompts. Include these elements for precise control:

#### 1. Camera Angles and Composition

**Camera Angles**:
- "low-angle shot" - Dramatic, looking up
- "high-angle shot" - Looking down, overview perspective
- "eye-level shot" - Natural, straight-on view
- "bird's eye view" - Overhead, top-down
- "dutch angle" - Tilted, dynamic
- "close-up" - Tight framing, detail focus
- "wide-angle shot" - Broad view, expansive
- "medium shot" - Balanced framing
- "overhead view" - Directly above
- "side view" - Profile perspective

**Composition Techniques**:
- "rule of thirds composition"
- "centered composition"
- "symmetrical composition"
- "leading lines"
- "framing with foreground elements"

**Example**:
```
"Generate a 4K professional product image, low-angle shot with rule of thirds composition, 16:9 aspect ratio"
```

#### 2. Depth of Field and Focus

**Depth of Field Control**:
- "shallow depth of field (f/1.8)" - Blurred background, sharp subject
- "deep depth of field (f/16)" - Everything in focus
- "bokeh background" - Artistic blur
- "selective focus" - Focus on specific element
- "rack focus" - Focus shift effect

**Focus Points**:
- "focus on [subject]"
- "foreground in focus, background blurred"
- "everything in sharp focus"

**Example**:
```
"Create a 4K professional product image with shallow depth of field (f/1.8), focus on the product, bokeh background"
```

#### 3. Lighting Control

**Lighting Types**:
- "golden hour lighting" - Warm, sunset/sunrise
- "blue hour lighting" - Cool, twilight
- "studio softbox lighting" - Professional, even
- "natural daylight" - Bright, natural
- "dramatic side lighting" - Strong shadows, contrast
- "rim lighting" - Edge lighting, separation
- "backlighting" - Light from behind
- "front lighting" - Light from front
- "top lighting" - Light from above
- "ambient lighting" - General, soft
- "neon lighting" - Vibrant, colorful
- "warm lighting" - Orange/yellow tones
- "cool lighting" - Blue/white tones
- "high-key lighting" - Bright, minimal shadows
- "low-key lighting" - Dark, dramatic shadows

**Lighting Quality**:
- "soft diffused lighting"
- "harsh directional lighting"
- "even lighting"
- "dramatic lighting"
- "moody lighting"

**Example**:
```
"Generate a 4K professional image with golden hour backlighting, soft diffused shadows, warm color temperature"
```

#### 4. Color Grading and Color Control

**Color Grading Styles**:
- "warm color grading" - Orange/yellow tones
- "cool color grading" - Blue/cyan tones
- "desaturated" - Muted colors
- "vibrant colors" - Saturated, vivid
- "monochrome" - Single color
- "high contrast" - Strong color differences
- "low contrast" - Subtle color differences
- "color grading: teal and orange" - Cinematic look
- "muted color palette" - Soft, pastel
- "bold color palette" - Strong, vibrant

**Color Schemes**:
- "complementary colors"
- "analogous colors"
- "monochromatic"
- "triadic color scheme"

**Example**:
```
"Create a 4K professional image with warm color grading, teal and orange cinematic look, high contrast"
```

#### 5. Style and Medium

**Artistic Styles**:
- "photorealistic" - Realistic photography
- "cinematic" - Movie-like quality
- "minimalist" - Simple, clean
- "modern" - Contemporary design
- "vintage" - Retro, classic
- "futuristic" - Sci-fi, advanced
- "abstract" - Non-representational
- "illustration style" - Drawn appearance
- "3D render" - Computer-generated
- "oil painting style" - Traditional painting
- "watercolor" - Soft, flowing
- "sketch" - Line drawing
- "vector art" - Clean, geometric

**Example**:
```
"Generate a 4K photorealistic professional product image with cinematic color grading"
```

#### 6. Mood and Atmosphere

**Mood Descriptors**:
- "dramatic"
- "peaceful"
- "energetic"
- "mysterious"
- "professional"
- "playful"
- "serious"
- "elegant"
- "raw"
- "polished"

**Atmosphere**:
- "foggy atmosphere"
- "misty morning"
- "crisp clear day"
- "moody atmosphere"
- "bright and airy"
- "dark and dramatic"

**Example**:
```
"Create a 4K professional image with dramatic mood, mysterious atmosphere, low-key lighting"
```

#### 7. Text Rendering (Nano Banana Pro Specialty)

**Text Control**:
- "precise text rendering"
- "accurate typography"
- "legible text"
- "stylized text"
- "clear text overlay"
- "professional typography"

**Text Styles**:
- "bold sans-serif text"
- "elegant serif typography"
- "modern geometric fonts"
- "hand-lettered style"

**Example**:
```
"Generate a 4K UI mockup with precise text rendering, clear typography, professional font choices"
```

---

### Complete Prompt Template

**Full Control Template**:
```
"Generate a [4K/2K/1K] [professional/high-resolution/detailed] [image type] of [subject], 
[aspect ratio] aspect ratio, 
[camera angle] with [depth of field], 
[lighting type] with [lighting quality], 
[color grading/style], 
[artistic style], 
[mood/atmosphere], 
[text rendering if needed]"
```

**Real-World Example**:
```
"Generate a 4K professional UI mockup for a cannabis grow monitoring dashboard, 
16:9 aspect ratio, 
eye-level shot with deep depth of field (f/16), 
studio softbox lighting with even illumination, 
modern minimalist style with cool color grading, 
photorealistic rendering, 
professional clean atmosphere, 
precise text rendering with clear typography"
```

**Simplified Example** (Still Effective):
```
"Generate a 4K professional product image of a cannabis plant in a grow tent, 
16:9 aspect ratio, 
low-angle shot with shallow depth of field, 
golden hour backlighting, 
warm color grading, 
photorealistic style"
```

---

### Advanced Features

#### Outpainting (Image Expansion)
Extend images beyond original borders:
```
"Expand the image to 21:9 aspect ratio, adding more background scenery to the sides, maintaining current style"
```

#### Inpainting (Local Editing)
Modify specific areas:
```
"Replace the background with a sunset sky, maintaining the subject's appearance"
```

#### Batch Generation
Create variations:
```
"Generate 3 variations of this image with different lighting: golden hour, blue hour, and studio lighting"
```

---

### Quick Reference: Control Keywords

**Aspect Ratios**: 1:1, 4:3, 3:2, 4:5, 2:3, 3:4, 16:9, 9:16, 9:21, 21:9

**Resolutions**: 1K, 2K, 4K (always uppercase)

**Camera Angles**: low-angle, high-angle, eye-level, bird's eye, overhead, close-up, wide-angle

**Depth of Field**: shallow (f/1.8), deep (f/16), bokeh, selective focus

**Lighting**: golden hour, blue hour, studio softbox, natural daylight, dramatic side, rim, backlighting, neon

**Color**: warm, cool, desaturated, vibrant, high contrast, muted, bold

**Style**: photorealistic, cinematic, minimalist, modern, vintage, futuristic, 3D render

**Mood**: dramatic, peaceful, professional, mysterious, elegant

---

### 2. Nano Banana (Gemini 2.5 Flash Image)

**Status**: ✅ Native, built-in, no setup required  
**Model**: Google Gemini 2.5 Flash Image  
**Subscription**: Covered by Google AI subscription  
**Best For**: Quick image generation, high-volume tasks, standard resolution images

**Key Features**:
- **1024px resolution** image generation
- Optimized for speed and efficiency
- Low-latency generation
- High-volume task support
- Automatically available to Antigravity agents

**How Agents Access It**:
- **No explicit tool call needed** - agents use it automatically for faster tasks
- Agents may choose this for quick iterations
- Works seamlessly with your Google AI subscription (no API keys)

**Example Usage**:
```
"Quickly generate a thumbnail image for the dashboard"
"Create a simple icon for the grow monitoring system"
```

**Technical Details**:
- Built on Gemini 2.5 Flash Image model
- 1024px resolution output
- Optimized for speed and efficiency

---

### 3. Imagen 3 (Default - NOT Preferred)

**Status**: ⚠️ Default model for general-purpose tasks  
**Model**: Google Imagen 3  
**Subscription**: Covered by Google AI subscription  
**Best For**: General-purpose image generation (but you want to avoid this)

**Key Features**:
- General-purpose image creation
- Efficient and versatile
- **This is the default** - agents use this unless task requires higher fidelity

**Why This is a Problem**:
- **Imagen 3 is the default** for general tasks
- Agents may choose Imagen 3 when you want Nano Banana Pro
- You need to guide agents to prefer Nano Banana Pro instead

**How Agents Access It**:
- Agents automatically select Imagen 3 for general-purpose tasks
- This happens when task requirements don't explicitly trigger Nano Banana Pro selection criteria

**⚠️ IMPORTANT**: You want to **avoid Imagen 3** and always use **Nano Banana Pro** instead. See the "Ensuring Nano Banana Pro Preference" section below.

---

## Tools NOT Covered (Require External Setup/API Keys)

The following tools are **NOT native** and require external setup or API keys:

- ❌ **Intelligent Image Generator MCP** - Requires MCP server installation and may need external API keys
- ❌ **Animo** - Requires separate installation and subscription
- ❌ **External MCP servers** - Require configuration and may need API keys

**Focus on the native tools above** - they work with your Google AI subscription automatically.

---

## Internal Mechanism: How Antigravity Chooses Image Generation Tools

### Agent Decision-Making Process

Antigravity's agents use an **automatic decision-making process** to select image generation tools:

1. **Task Analysis**: When you request an image, the agent analyzes:
   - Prompt complexity
   - Required resolution/fidelity
   - Specific features needed (text rendering, professional quality, etc.)
   - Task type (UI mockup, diagram, general image, etc.)

2. **Tool Selection Logic**:
   - **Imagen 3** (Default): Selected for general-purpose image generation tasks
   - **Nano Banana Pro**: Selected when task requires:
     - High-resolution outputs (1K, 2K, 4K)
     - Advanced text rendering
     - UI mockups or system diagrams
     - Professional asset production
     - Complex instructions
   - **Nano Banana** (Flash): Selected for quick iterations or high-volume tasks

3. **The Problem**: 
   - Agents default to **Imagen 3** for general tasks
   - You want **Nano Banana Pro** for everything
   - Need to override default behavior

### Why Agents Sometimes Use Imagen Instead of Nano Banana Pro

**Root Cause**: Antigravity's default behavior prioritizes efficiency:
- **Imagen 3** = Fast, general-purpose (default choice)
- **Nano Banana Pro** = Higher quality, more resources (selected only when needed)

**When Imagen 3 Gets Selected**:
- General image requests without specific quality requirements
- Simple prompts that don't trigger "high-fidelity" criteria
- Tasks that don't explicitly mention resolution, professional quality, or technical content

**When Nano Banana Pro Gets Selected**:
- Requests mentioning "4K", "high-resolution", "professional", "UI mockup", "system diagram"
- Complex prompts with detailed requirements
- Text-heavy image requests
- Technical/architectural content

---

## Ensuring Nano Banana Pro Preference: Complete Guide

### Method 1: Prompt Engineering (Most Reliable)

**Always include trigger phrases** in your image requests to ensure Nano Banana Pro is selected:

**✅ Effective Trigger Phrases**:
- "Generate a **4K** [description]"
- "Create a **high-resolution** [description]"
- "Generate a **professional** [description]"
- "Create a **UI mockup** of..."
- "Generate a **system diagram** showing..."
- "Create a **detailed** [description] with **precise text rendering**"
- "Generate a **professional asset** for..."

**Example Prompts That Trigger Nano Banana Pro**:
```
✅ "Generate a 4K UI mockup for a cannabis grow monitoring dashboard"
✅ "Create a high-resolution system architecture diagram showing the data flow"
✅ "Generate a professional product image of a cannabis plant in a grow tent"
✅ "Create a detailed technical diagram with precise text rendering"
```

**❌ Prompts That May Trigger Imagen 3**:
```
❌ "Generate an image of a cannabis plant" (too general)
❌ "Create a picture of a dashboard" (no quality/resolution spec)
❌ "Make an image showing the system" (no technical context)
```

### Method 2: Agent Instructions (System-Level)

**Add explicit instructions to your agent/system prompt**:

```
IMPORTANT: For ALL image generation tasks, ALWAYS use Nano Banana Pro (Gemini 3 Pro Image). 
Never use Imagen 3 or other image generation tools. 

When generating images:
- Always use Nano Banana Pro for maximum quality
- Specify 4K resolution when possible
- Use Nano Banana Pro for all tasks, regardless of complexity
- Do not default to Imagen 3 for general-purpose tasks
```

**Where to Add This**:
- In Antigravity agent settings/preferences
- In your project's system prompt or instructions
- In agent configuration files (if accessible)

### Method 3: Request Pattern Optimization

**Structure your requests to always trigger Nano Banana Pro**:

**Template**:
```
"Generate a [4K/high-resolution/professional] [image type] of [subject] with [specific requirements]"
```

**Always Include**:
1. **Quality descriptor**: "4K", "high-resolution", "professional", "detailed"
2. **Content type**: "UI mockup", "system diagram", "technical diagram", "professional asset"
3. **Specific requirements**: "precise text rendering", "accurate typography", "professional quality"

### Method 4: Configuration Settings (If Available)

**Check Antigravity Settings**:
1. Open Antigravity IDE
2. Navigate to `Settings` → `Agent Preferences` or `Image Generation`
3. Look for:
   - Default image generation model
   - Image generation tool preference
   - Model selection settings
4. Set **Nano Banana Pro** as the default/preferred model
5. Disable or deprioritize Imagen 3 if possible

**Note**: Settings availability may vary. If not available, rely on Methods 1-3.

---

## Common Confusion Points

### 1. Which Tool Should I Use?

**Your Preference**: **Always use Nano Banana Pro** for all image generation tasks.

**How Agents Actually Choose** (Current Behavior):
- **Imagen 3** (Default): General-purpose tasks (you want to avoid this)
- **Nano Banana Pro**: High-fidelity tasks (this is what you want)
- **Nano Banana**: Quick iterations (acceptable fallback)

**How to Ensure Nano Banana Pro**:
- ✅ Always include quality/resolution keywords in prompts
- ✅ Use trigger phrases: "4K", "high-resolution", "professional", "UI mockup"
- ✅ Add agent instructions to prefer Nano Banana Pro
- ✅ Structure requests to trigger high-fidelity selection criteria

### 2. Tool Naming Inconsistencies

**Problem**: Agents may get confused about tool names or try to call tools explicitly.

**Solution**:
- **Nano Banana Pro**: Not a tool call - agents use it automatically when criteria are met
- **Imagen 3**: Default tool - you want to avoid this by using trigger phrases
- **No explicit tool calls needed** - but you MUST use trigger phrases to ensure Nano Banana Pro
- Agents handle tool selection automatically, but you guide them with prompt engineering

**Key Insight**: You can't call tools directly, but you CAN influence selection through prompt design.

### 3. Access Method Confusion

**Problem**: Agents may think they need to configure tools or use API keys.

**Clarification**:
- **Native Tools**: Nano Banana Pro and Nano Banana are built-in
- **No Setup Required**: They work automatically with your Google AI subscription
- **No API Keys**: Your Google account authentication handles everything
- **Automatic Selection**: Agents choose the right tool automatically

### 4. "Tool Not Found" Errors

**Problem**: Agents may try to call tools with explicit names that don't exist.

**Solution**:
- **Don't use explicit tool calls** - agents should use natural language with trigger phrases
- Native tools are invoked automatically by Antigravity based on prompt analysis
- If you see tool errors, the agent is trying to use non-native tools
- Remind agents: "Use natural language with quality keywords (4K, professional, high-resolution) to trigger Nano Banana Pro"

### 5. Agents Using Imagen 3 Instead of Nano Banana Pro

**Problem**: Agents default to Imagen 3 for general tasks when you want Nano Banana Pro.

**Solution**:
- **Always include trigger phrases** in image requests (see Method 1 above)
- **Add system instructions** to prefer Nano Banana Pro (see Method 2 above)
- **Structure requests** to trigger high-fidelity criteria (see Method 3 above)
- **Check settings** to configure default model if available (see Method 4 above)

---

## Best Practices

### 1. For Agents Using Native Tools (Ensuring Nano Banana Pro)

**How to Request Images** (Always Trigger Nano Banana Pro):
- ✅ **Use trigger phrases**: "Generate a **4K** UI mockup for..."
- ✅ **Include quality keywords**: "high-resolution", "professional", "detailed"
- ✅ **Specify technical content**: "system diagram", "UI mockup", "technical diagram"
- ✅ **Be descriptive**: Include details about style, content, purpose, AND quality
- ✅ **Guide selection**: Use phrases that trigger high-fidelity tool selection
- ❌ **Don't use generic prompts**: "Generate an image" may trigger Imagen 3
- ❌ **Don't skip quality descriptors**: Always mention resolution or quality level

**Example: Good vs Bad Prompts**:

✅ **Good** (Triggers Nano Banana Pro):
```
"Generate a 4K professional UI mockup for a cannabis grow monitoring dashboard with precise text rendering"
"Create a high-resolution system architecture diagram showing the data flow between components"
"Generate a detailed technical diagram with accurate typography"
```

❌ **Bad** (May Trigger Imagen 3):
```
"Generate an image of a dashboard"
"Create a picture showing the system"
"Make an image of a cannabis plant"
```

**When Nano Banana Pro is Used** (Current Automatic Triggers):
- Prompts mentioning "4K", "high-resolution", "professional"
- UI mockups and system diagrams
- Text-heavy images (better text rendering)
- Complex instructions
- Technical/architectural content

**When Imagen 3 is Used** (What You Want to Avoid):
- Generic image requests without quality specifications
- Simple prompts that don't trigger high-fidelity criteria
- General-purpose image generation tasks

**When Nano Banana is Used** (Acceptable Fallback):
- Quick iterations (if speed is explicitly requested)
- Standard resolution (1024px) when explicitly specified
- High-volume tasks

### 2. Troubleshooting

**Tool Not Found Errors**:
- ✅ **Solution**: Agents should use natural language, not explicit tool calls
- ✅ **Check**: Ensure your Google account is linked in Antigravity
- ✅ **Verify**: Your Google AI subscription includes Gemini API access
- ❌ **Don't**: Try to install MCP servers or external tools

**Poor Image Quality**:
- Provide more detailed and specific prompts
- Include style descriptions (e.g., "photorealistic", "modern UI", "technical diagram")
- Specify desired resolution if needed (though agents choose automatically)
- Request revisions if needed - agents can refine prompts

**Agent Confusion**:
- Remind agents: "Use natural language with quality keywords (4K, professional, high-resolution) to trigger Nano Banana Pro"
- Provide examples: "Generate a 4K professional UI mockup for a cannabis grow monitoring dashboard"
- Clarify: "Always include quality descriptors to ensure Nano Banana Pro is used instead of Imagen 3"
- Add system instructions: "For all image generation, always use Nano Banana Pro. Include quality keywords in prompts."
- Avoid: Generic prompts that may trigger Imagen 3 default behavior

---

## Native Tools Comparison Table

| Tool | Model | Resolution | Speed | Best For | Setup |
|------|-------|------------|-------|----------|-------|
| **Nano Banana Pro** | Gemini 3 Pro Image | Up to 4K | Standard | High-quality, professional images | ✅ None |
| **Nano Banana** | Gemini 2.5 Flash Image | 1024px | Fast | Quick iterations, high-volume | ✅ None |
| **Imagen 4** | Imagen 4 | High | Standard | Text-to-image, improved text rendering | ⚠️ May need config |

**All native tools**: No API keys, work with Google AI subscription, automatic agent access

---

## Quick Reference

### Nano Banana Pro (Recommended)
- ✅ Native, built-in, no setup
- ✅ 4K resolution capability
- ✅ Automatic agent access
- ✅ Best for professional/technical content
- ✅ Enhanced text rendering
- ✅ Works with Google AI subscription

### Nano Banana
- ✅ Native, built-in, no setup
- ✅ Fast generation (1024px)
- ✅ Automatic agent access
- ✅ Best for quick iterations
- ✅ Works with Google AI subscription

### What NOT to Use
- ❌ **MCP servers** - Require external setup and may need API keys
- ❌ **External tools** - Not covered by Google AI subscription
- ❌ **Explicit tool calls** - Native tools work automatically

---

## Additional Resources

- [Nano Banana Pro Announcement](https://antigravityide.org/blog/nano-banana-pro/)
- [Gemini Image Generation API Docs](https://ai.google.dev/gemini-api/docs/image-generation)
- [Google AI Studio](https://aistudio.google.com/)

---

## Summary

**Key Takeaways for Ensuring Nano Banana Pro Preference**:

1. ✅ **Nano Banana Pro** (Gemini 3 Pro) - Your ALWAYS-PREFERRED Tool
   - Native, built-in, no setup
   - 4K resolution, professional quality
   - **Agents use it when you include trigger phrases**
   - Works with Google AI subscription

2. ⚠️ **Imagen 3** - Default (You Want to Avoid This)
   - **This is the default** for general-purpose tasks
   - Agents may choose this for simple prompts
   - **Override by using trigger phrases** in your prompts

3. ✅ **How to Ensure Nano Banana Pro**:
   - **Always include trigger phrases**: "4K", "high-resolution", "professional", "UI mockup"
   - **Add system instructions**: Tell agents to prefer Nano Banana Pro
   - **Structure requests**: Include quality and technical descriptors
   - **Check settings**: Configure default model if available

4. ✅ **No API Keys Needed**
   - All native tools use your Google account authentication
   - Covered by your Google AI subscription
   - Automatic access in Antigravity

5. ✅ **No Explicit Tool Calls, But Use Trigger Phrases**
   - Agents use natural language: "Generate a **4K professional** UI mockup..."
   - Antigravity handles tool selection automatically based on prompt analysis
   - **You guide selection through prompt engineering**
   - Don't try to call tools by name, but DO use quality keywords

6. ❌ **Avoid External Tools**
   - MCP servers require setup and may need API keys
   - External tools aren't covered by Google AI subscription
   - Stick to native Nano Banana tools

**Critical Instructions for Agents**:

```
FOR ALL IMAGE GENERATION TASKS:
1. ALWAYS use Nano Banana Pro (Gemini 3 Pro Image) - never use Imagen 3
2. When requesting images, ALWAYS include quality keywords:
   - "4K" or "high-resolution" or "professional"
   - "UI mockup" or "system diagram" or "technical diagram"
   - "detailed" or "precise text rendering"
3. Never use generic prompts like "generate an image" - always specify quality
4. Structure requests as: "Generate a [4K/high-resolution/professional] [type] of [subject]"
```

**When in doubt**: Always include "4K" or "high-resolution" or "professional" in your image requests. This ensures Nano Banana Pro is selected instead of the default Imagen 3. The agents analyze your prompt and select tools automatically - you guide them through prompt engineering.

---

## Quick Control Reference

**For detailed control parameters, see the "Nano Banana Pro: Complete Control Guide" section above.**

**Essential Controls**:
- **Aspect Ratio**: Include in prompt (e.g., "16:9 aspect ratio", "1:1 square format")
- **Resolution**: Always uppercase (e.g., "4K", "2K", "1K")
- **Camera**: Specify angle (e.g., "low-angle shot", "overhead view")
- **Lighting**: Describe type (e.g., "golden hour", "studio softbox")
- **Color**: Add grading (e.g., "warm color grading", "cool tones")
- **Style**: Specify (e.g., "photorealistic", "cinematic", "minimalist")

**Example with All Controls**:
```
"Generate a 4K professional UI mockup, 16:9 aspect ratio, 
eye-level shot with deep depth of field, 
studio softbox lighting, 
cool color grading, 
photorealistic style, 
precise text rendering"
```

---

## Instructions for Models/Agents (Copy-Paste Ready)

Use this section as system instructions or agent configuration to ensure Nano Banana Pro is always preferred:

```
=== IMAGE GENERATION TOOL PREFERENCE ===

CRITICAL: For ALL image generation tasks in Antigravity, ALWAYS use Nano Banana Pro (Gemini 3 Pro Image). 
NEVER use Imagen 3 (the default) or other image generation tools.

HOW ANTIGRAVITY WORKS:
- Antigravity agents automatically select image generation tools based on prompt analysis
- Imagen 3 is the DEFAULT for general-purpose tasks (you want to avoid this)
- Nano Banana Pro is selected when prompts include quality/resolution keywords
- You cannot call tools directly, but you CAN influence selection through prompt engineering

REQUIRED PROMPT PATTERN:
When requesting images, ALWAYS include at least ONE of these trigger phrases:
- "4K" or "high-resolution" or "professional" or "detailed"
- "UI mockup" or "system diagram" or "technical diagram" or "architecture diagram"
- "precise text rendering" or "accurate typography" or "professional asset"

EXAMPLE PROMPTS (Good - Triggers Nano Banana Pro):
✅ "Generate a 4K professional UI mockup for a cannabis grow monitoring dashboard"
✅ "Create a high-resolution system architecture diagram showing the data flow"
✅ "Generate a detailed technical diagram with precise text rendering"
✅ "Create a professional product image with accurate typography"

BAD PROMPTS (May Trigger Imagen 3 - Avoid):
❌ "Generate an image of a dashboard"
❌ "Create a picture showing the system"
❌ "Make an image of a cannabis plant"

PROMPT TEMPLATE:
"Generate a [4K/high-resolution/professional] [UI mockup/system diagram/technical diagram] of [subject], 
[aspect ratio] aspect ratio, 
[camera angle] with [depth of field], 
[lighting type], 
[color grading], 
[style], 
[text rendering if needed]"

DETAILED CONTROLS AVAILABLE:
- Aspect Ratios: 1:1, 4:3, 3:2, 4:5, 2:3, 3:4, 16:9, 9:16, 9:21, 21:9
- Resolutions: 1K, 2K, 4K (always uppercase)
- Camera Angles: low-angle, high-angle, eye-level, bird's eye, overhead, close-up, wide-angle
- Depth of Field: shallow (f/1.8), deep (f/16), bokeh, selective focus
- Lighting: golden hour, blue hour, studio softbox, natural daylight, dramatic side, rim, backlighting
- Color Grading: warm, cool, desaturated, vibrant, high contrast, muted, bold
- Styles: photorealistic, cinematic, minimalist, modern, vintage, futuristic, 3D render

See "Nano Banana Pro: Complete Control Guide" section for full details.

SYSTEM BEHAVIOR:
- Antigravity analyzes your prompt for quality/resolution keywords
- If keywords are present → Nano Banana Pro is selected
- If keywords are missing → Imagen 3 (default) may be selected
- Always include trigger phrases to ensure Nano Banana Pro selection

REMEMBER:
- No explicit tool calls needed - use natural language with quality keywords
- No API keys needed - works with Google AI subscription automatically
- Always include quality descriptors in image requests
- Structure requests to trigger high-fidelity tool selection criteria
```

**Usage**: Copy the above block and add it to:
- Agent system prompts
- Project instructions
- Antigravity agent configuration
- Any place where you configure agent behavior
