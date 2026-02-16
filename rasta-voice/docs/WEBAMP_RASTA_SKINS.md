# Webamp - Rasta Skins for Web Music Player

A guide to embedding the classic Winamp 2.9 media player in web projects using open-source Webamp, with Rasta/Jamaica themed skins.

## Overview

**Webamp** is an open-source (MIT license) HTML5/JavaScript reimplementation of Winamp 2.9 that runs in any modern browser.

| Resource | URL |
|----------|-----|
| Live Demo | https://webamp.org/ |
| GitHub | https://github.com/captbaritone/webamp |
| NPM | https://www.npmjs.com/package/webamp |
| Documentation | https://docs.webamp.org/ |
| Skin Museum | https://skins.webamp.org/ |

## Features

- **Pixel-perfect skin support** - loads classic `.wsz` Winamp skins
- **MilkDrop visualizer** - via Butterchurn WebGL implementation
- **Full equalizer** and playlist management
- **Drag-and-drop** local audio files and skins
- **Shade mode** and doubled size mode
- Works in Chrome, Firefox, Safari, Edge

## Finding Rasta/Jamaica Skins

The **Winamp Skin Museum** contains 98,000+ skins with search:

| Theme | Search URL |
|-------|------------|
| Rasta | https://skins.webamp.org/?query=rasta |
| Reggae | https://skins.webamp.org/?query=reggae |
| Jamaica | https://skins.webamp.org/?query=jamaica |
| Bob Marley | https://skins.webamp.org/?query=marley |

### Known Rasta-Themed Skins

| Skin Name | Description |
|-----------|-------------|
| **ZDL ANALOG STUDIO-5** | Analog reel-to-reel look with selectable "rasta colors" theme |
| **BLAKK** | 165 color themes - customizable to red/gold/green |
| **Rastamp** | Classic rasta-themed skin |
| **KalaK Amp** | Gold color variation for reggae setups |

### Alternative Skin Sources

- **Winamp Heritage:** https://winampheritage.com/skins
- **1001 Winamp Skins:** http://1001winampskins.com/

## Installation

### NPM Install

```bash
npm install webamp
```

### CDN (No Build Required)

```html
<script src="https://unpkg.com/webamp@1.5.0/built/webamp.bundle.min.js"></script>
```

## Basic Usage

### Minimal Setup

```html
<!DOCTYPE html>
<html>
<head>
  <title>Rasta Player</title>
</head>
<body>
  <div id="app"></div>
  <script src="https://unpkg.com/webamp@1.5.0/built/webamp.bundle.min.js"></script>
  <script>
    const webamp = new Webamp({
      initialTracks: [
        {
          url: "./music/one-love.mp3",
          metaData: { artist: "Bob Marley", title: "One Love" }
        }
      ]
    });
    webamp.renderWhenReady(document.getElementById("app"));
  </script>
</body>
</html>
```

### With Rasta Skin

```javascript
const webamp = new Webamp({
  initialSkin: {
    url: "./skins/rasta-skin.wsz"
  },
  initialTracks: [
    { url: "./music/track1.mp3", metaData: { artist: "Artist", title: "Track 1" } }
  ]
});

webamp.renderWhenReady(document.getElementById("app"));
```

### Multiple Skin Options

Let users choose from available skins:

```javascript
const webamp = new Webamp({
  availableSkins: [
    { url: "./skins/rasta-vibes.wsz", name: "Rasta Vibes" },
    { url: "./skins/jamaica-gold.wsz", name: "Jamaica Gold" },
    { url: "./skins/reggae-roots.wsz", name: "Reggae Roots" },
    { url: "./skins/one-love.wsz", name: "One Love" }
  ],
  initialSkin: {
    url: "./skins/rasta-vibes.wsz"
  }
});
```

### With MilkDrop Visualizer (Butterchurn)

```javascript
import Webamp from "webamp";
import butterchurnPresets from "butterchurn-presets";

const webamp = new Webamp({
  initialSkin: { url: "./skins/rasta.wsz" },
  butterchurnOpen: true,
  butterchurnPresets: butterchurnPresets.getPresets()
});
```

## API Methods

```javascript
// Play/Pause
webamp.play();
webamp.pause();

// Volume (0-100)
webamp.setVolume(80);

// Load new tracks
webamp.appendTracks([
  { url: "./new-track.mp3", metaData: { artist: "Artist", title: "New Track" } }
]);

// Change skin at runtime
webamp.setSkinFromUrl("./skins/new-rasta-skin.wsz");

// Get current state
const state = webamp.getMediaStatus(); // "PLAYING", "PAUSED", "STOPPED"

// Events
webamp.onTrackDidChange((track) => {
  console.log("Now playing:", track);
});

webamp.onClose(() => {
  console.log("Player closed");
});
```

## Downloading Skins

### From Skin Museum

1. Go to https://skins.webamp.org/?query=rasta
2. Click on a skin to preview
3. Right-click → "Download skin"
4. Save the `.wsz` file to your project

### Programmatic Download

```bash
# Example: Download a skin directly
curl -o rasta-skin.wsz "https://skins.webamp.org/skin/xxxxx/download"
```

## Hosting Considerations

### CORS for Remote Skins

If loading skins from external URLs, ensure CORS headers are set:

```
Access-Control-Allow-Origin: *
```

### Skin File Hosting

For production, host `.wsz` files on your own server or CDN to avoid CORS issues.

## Integration Ideas for Grok & Mon

### Livestream Player

Embed Webamp on grokandmon.com with Rasta skin for ambient music during grow streams:

```javascript
const webamp = new Webamp({
  initialSkin: { url: "/skins/rasta-grokmon.wsz" },
  initialTracks: [
    { url: "/music/ambient-reggae-1.mp3", metaData: { artist: "Grok & Mon", title: "Grow Vibes Vol. 1" } },
    { url: "/music/ambient-reggae-2.mp3", metaData: { artist: "Grok & Mon", title: "Grow Vibes Vol. 2" } }
  ],
  availableSkins: [
    { url: "/skins/rasta-grokmon.wsz", name: "Rasta Grok" },
    { url: "/skins/cannabis-green.wsz", name: "Cannabis Green" }
  ]
});
```

### Voice Pipeline Integration

Use with the Rasta voice pipeline output for demo playback:

```javascript
// Play generated voice clips
webamp.setTracksToPlay([
  { url: "/output/rasta-clip-001.wav", metaData: { artist: "Rasta Ralph", title: "Greeting" } }
]);
```

## Resources

- **Webamp Docs:** https://docs.webamp.org/
- **Skin Format Spec:** https://github.com/captbaritone/webamp/blob/master/packages/webamp/docs/skin-format.md
- **Butterchurn (MilkDrop):** https://github.com/jberg/butterchurn
- **Winamp Skin Museum API:** https://api.webamp.org/

## License

Webamp is MIT licensed. Skins may have individual licenses - check before commercial use.
