"""
Claude & Sol Website Scraper
=============================
Full scrape plan for claudeandsol.com data capture.

Uses: httpx (async), playwright (screenshots), archivebox (preservation)
"""

import asyncio
import httpx
import json
from datetime import datetime
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================

BASE_URL = "https://claudeandsol.com"
WEBCAM_URL = "https://autoncorp.com/biodome/get_webcam.php"

OUTPUT_DIR = Path("data/scraped/claudeandsol")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API Endpoints discovered
ENDPOINTS = {
    "sensors_latest": "/api/sensors/latest",
    "sensors_history": "/api/sensors/history",  # ?hours=24
    "devices_latest": "/api/devices/latest",
    "ai_latest": "/api/ai/latest",
    "og_image": "/api/webcam/og-image",
}

# Token info
SOL_TOKEN = {
    "chain": "solana",
    "address": "jk1T35eWK41MBMM8AWoYVaNbjHEEQzMDetTsfnqpump",
    "pump_fun": "https://pump.fun/coin/jk1T35eWK41MBMM8AWoYVaNbjHEEQzMDetTsfnqpump",
    "twitter": "@d33v33d0",
}


# =============================================================================
# Scraper Classes
# =============================================================================

class ClaudeAndSolScraper:
    """Async scraper for Claude & Sol website data"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=30.0,
            headers={"User-Agent": "GrokAndMon/1.0 (Research)"}
        )
    
    async def close(self):
        await self.client.aclose()
    
    # -------------------------------------------------------------------------
    # API Scrapers
    # -------------------------------------------------------------------------
    
    async def get_sensors_latest(self) -> dict:
        """Get current sensor readings"""
        response = await self.client.get(ENDPOINTS["sensors_latest"])
        return response.json()
    
    async def get_sensors_history(self, hours: int = 24) -> list:
        """Get historical sensor data"""
        response = await self.client.get(
            ENDPOINTS["sensors_history"],
            params={"hours": hours}
        )
        return response.json()
    
    async def get_devices_status(self) -> dict:
        """Get current hardware/device status"""
        response = await self.client.get(ENDPOINTS["devices_latest"])
        return response.json()
    
    async def get_ai_narrative(self) -> str:
        """Get Claude's latest narrative output"""
        response = await self.client.get(ENDPOINTS["ai_latest"])
        # Returns markdown text, not JSON
        return response.text
    
    async def get_webcam_image(self) -> bytes:
        """Download current webcam image"""
        timestamp = int(datetime.now().timestamp() * 1000)
        url = f"{WEBCAM_URL}?t={timestamp}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.content
    
    # -------------------------------------------------------------------------
    # Bulk Operations
    # -------------------------------------------------------------------------
    
    async def scrape_all(self) -> dict:
        """Scrape all available data"""
        timestamp = datetime.now().isoformat()
        
        # Fetch all data concurrently
        sensors, history, devices, narrative = await asyncio.gather(
            self.get_sensors_latest(),
            self.get_sensors_history(hours=72),  # Get 3 days
            self.get_devices_status(),
            self.get_ai_narrative(),
        )
        
        # Download webcam image
        image_bytes = await self.get_webcam_image()
        
        return {
            "scraped_at": timestamp,
            "sensors_latest": sensors,
            "sensors_history": history,
            "devices_status": devices,
            "ai_narrative": narrative,
            "webcam_image": image_bytes,
        }
    
    def save_scrape(self, data: dict, output_dir: Path = OUTPUT_DIR):
        """Save scraped data to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON data
        json_data = {k: v for k, v in data.items() if k != "webcam_image"}
        json_path = output_dir / f"scrape_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)
        
        # Save image
        if data.get("webcam_image"):
            image_path = output_dir / f"webcam_{timestamp}.jpg"
            with open(image_path, "wb") as f:
                f.write(data["webcam_image"])
        
        # Append narrative to log
        narrative_log = output_dir / "ai_narratives.log"
        with open(narrative_log, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Timestamp: {data['scraped_at']}\n")
            f.write(f"{'='*60}\n")
            f.write(data.get("ai_narrative", "No narrative available"))
            f.write("\n")
        
        print(f"Saved scrape to {json_path}")
        return json_path


# =============================================================================
# Continuous Monitoring
# =============================================================================

async def monitor_loop(interval_minutes: int = 30):
    """Continuously monitor and scrape the site"""
    scraper = ClaudeAndSolScraper()
    
    try:
        while True:
            print(f"\n[{datetime.now()}] Scraping Claude & Sol...")
            
            try:
                data = await scraper.scrape_all()
                scraper.save_scrape(data)
                
                # Print summary
                sensors = data.get("sensors_latest", {})
                print(f"  Temperature: {sensors.get('air_temp', 'N/A')}°F")
                print(f"  Humidity: {sensors.get('humidity', 'N/A')}%")
                print(f"  VPD: {sensors.get('vpd', 'N/A')} kPa")
                
            except Exception as e:
                print(f"  Error: {e}")
            
            print(f"  Next scrape in {interval_minutes} minutes...")
            await asyncio.sleep(interval_minutes * 60)
            
    finally:
        await scraper.close()


# =============================================================================
# Archive with ArchiveBox
# =============================================================================

def archive_with_archivebox():
    """
    Use ArchiveBox to create a full snapshot of the site.
    Run this separately as it's synchronous.
    
    Commands:
        archivebox add "https://claudeandsol.com"
        archivebox add "https://autoncorp.com"
        archivebox add "https://pump.fun/coin/jk1T35eWK41MBMM8AWoYVaNbjHEEQzMDetTsfnqpump"
    """
    import subprocess
    
    urls = [
        "https://claudeandsol.com",
        "https://autoncorp.com", 
        "https://pump.fun/coin/jk1T35eWK41MBMM8AWoYVaNbjHEEQzMDetTsfnqpump",
        "https://x.com/d33v33d0",
    ]
    
    for url in urls:
        print(f"Archiving: {url}")
        subprocess.run(["archivebox", "add", url], check=True)


# =============================================================================
# CLI
# =============================================================================

async def main():
    """One-time scrape"""
    scraper = ClaudeAndSolScraper()
    
    try:
        print("Scraping Claude & Sol website...")
        data = await scraper.scrape_all()
        
        # Save results
        output_path = scraper.save_scrape(data)
        
        # Print summary
        print("\n" + "="*60)
        print("SCRAPE COMPLETE")
        print("="*60)
        print(f"Saved to: {output_path}")
        print(f"\nSensor History: {len(data.get('sensors_history', []))} records")
        print(f"AI Narrative length: {len(data.get('ai_narrative', ''))} chars")
        
        # Print latest sensors
        sensors = data.get("sensors_latest", {})
        if sensors:
            print("\nLatest Sensors:")
            for key, value in sensors.items():
                print(f"  {key}: {value}")
        
        # Print device status
        devices = data.get("devices_status", {})
        if devices:
            print("\nDevice Status:")
            for key, value in devices.items():
                print(f"  {key}: {value}")
                
    finally:
        await scraper.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        asyncio.run(monitor_loop(interval))
    else:
        asyncio.run(main())
