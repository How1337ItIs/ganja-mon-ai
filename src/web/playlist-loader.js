/**
 * Playlist Loader for Grok & Mon Website
 * =======================================
 * 
 * Dynamically loads playlists from API and populates Webamp player.
 * Supports both Trenchtown and Ultimate Dub playlists.
 */

class PlaylistLoader {
    constructor() {
        this.currentPlaylist = null;
        this.playlists = [];
    }

    async loadPlaylists() {
        try {
            const response = await fetch('/api/playlist/list');
            const data = await response.json();
            this.playlists = data.playlists;
            console.log('Loaded playlists:', this.playlists);
            return this.playlists;
        } catch (error) {
            console.error('Error loading playlists:', error);
            return [];
        }
    }

    async loadPlaylist(playlistId = 'trenchtown') {
        try {
            const response = await fetch(`/api/playlist/${playlistId}`);
            const playlist = await response.json();
            this.currentPlaylist = playlist;
            console.log(`Loaded playlist: ${playlist.name} (${playlist.total_tracks} tracks)`);
            return playlist;
        } catch (error) {
            console.error(`Error loading playlist ${playlistId}:`, error);
            return null;
        }
    }

    convertToWebampTracks(playlist) {
        if (!playlist || !playlist.tracks) {
            return [];
        }

        return playlist.tracks.map(track => {
            // Handle different playlist formats
            let url, artist, title;

            if (track.url) {
                // Ultimate dub format (has API URL)
                url = track.url;
                artist = track.artist || 'Various Artists';
                title = track.title || track.file;
            } else if (track.file) {
                // Trenchtown format (relative path)
                url = `/music/${track.file}`;
                artist = track.artist || 'Various Artists';
                title = track.title || track.file;
            } else {
                return null;
            }

            return {
                url: url,
                metaData: {
                    artist: artist,
                    title: title,
                    album: track.album || playlist.name,
                    genre: track.genre || 'Dub Reggae'
                }
            };
        }).filter(track => track !== null);
    }

    async initializeWebamp(playlistId = 'trenchtown') {
        if (typeof Webamp === 'undefined') {
            console.error('Webamp not loaded');
            return null;
        }

        // Load the playlist
        const playlist = await this.loadPlaylist(playlistId);
        if (!playlist) {
            console.error('Failed to load playlist');
            return null;
        }

        // Convert to Webamp format
        const tracks = this.convertToWebampTracks(playlist);

        if (tracks.length === 0) {
            console.warn('No tracks found in playlist');
            return null;
        }

        // Create Webamp instance
        const webamp = new Webamp({
            __butterchurnOptions: {
                importButterchurn: () => {
                    return new Promise((resolve, reject) => {
                        if (window.butterchurn) {
                            resolve(window.butterchurn);
                            return;
                        }
                        const script = document.createElement('script');
                        script.src = 'https://cdn.jsdelivr.net/npm/butterchurn@2.6.7/lib/butterchurn.min.js';
                        script.onload = () => resolve(window.butterchurn);
                        script.onerror = reject;
                        document.head.appendChild(script);
                    });
                },
                getPresets: async () => {
                    if (!window.butterchurnPresets) {
                        await new Promise((resolve, reject) => {
                            const script = document.createElement('script');
                            script.src = 'https://cdn.jsdelivr.net/npm/butterchurn-presets@2.4.7/lib/butterchurnPresets.min.js';
                            script.onload = resolve;
                            script.onerror = reject;
                            document.head.appendChild(script);
                        });
                    }
                    const presets = window.butterchurnPresets.getPresets();
                    return Object.entries(presets).map(([name, preset]) => ({
                        name,
                        butterchurnPresetObject: preset
                    }));
                },
                butterchurnOpen: true
            },
            initialSkin: {
                url: "https://r2.webampskins.org/skins/dc5ac7d407df9d529814abb2bee0da6b.wsz"
            },
            availableSkins: [
                { url: "https://r2.webampskins.org/skins/dc5ac7d407df9d529814abb2bee0da6b.wsz", name: "Rasta Amp" },
                { url: "https://r2.webampskins.org/skins/30cb7598df33f02bf0fc6091ad85cc6d.wsz", name: "Rasta Classic" },
                { url: "https://r2.webampskins.org/skins/cefb1d2d703b0c4a617b9abbba46ce74.wsz", name: "Rasta Knast" },
                { url: "https://r2.webampskins.org/skins/0c872a56c46d67316a3032c675c95f86.wsz", name: "Rastamp" },
                { url: "https://r2.webampskins.org/skins/7bc4a37de3805127fc6c23481d6011b6.wsz", name: "Jamaica Amp" },
                { url: "https://r2.webampskins.org/skins/26ddb0d349448db6ff5f48fdf5239453.wsz", name: "Jamaica" }
            ],
            initialTracks: tracks
        });

        return webamp;
    }

    async switchPlaylist(playlistId) {
        if (!window.webamp) {
            console.error('Webamp not initialized');
            return;
        }

        const playlist = await this.loadPlaylist(playlistId);
        if (!playlist) {
            console.error('Failed to load playlist');
            return;
        }

        const tracks = this.convertToWebampTracks(playlist);
        
        // Clear current playlist and add new tracks
        window.webamp.store.dispatch({
            type: "CLEAR_TRACKS"
        });

        // Add new tracks
        for (const track of tracks) {
            window.webamp.store.dispatch({
                type: "ADD_TRACKS",
                tracks: [track]
            });
        }

        console.log(`Switched to playlist: ${playlist.name}`);
    }
}

// Export for use in index.html
window.PlaylistLoader = PlaylistLoader;
