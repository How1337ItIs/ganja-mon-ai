import asyncio, os, sys
sys.path.insert(0, ".")
from src.hardware.govee import GoveeCloudAPI

async def check():
    api = GoveeCloudAPI(os.environ["GOVEE_API_KEY"])
    co2 = await api.find_co2_sensor()
    if co2:
        state = await api.get_device_state(co2.get("device"), co2.get("sku"))
        if state:
            for p in state.get("properties", []):
                if isinstance(p, dict):
                    for k, v in p.items():
                        print(f"  {k}: {v}")
        else:
            print("NO STATE RETURNED")
    else:
        print("NO CO2 SENSOR FOUND")
    await api.close()

asyncio.run(check())
