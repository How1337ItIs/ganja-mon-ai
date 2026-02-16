"""
OBS Overlay Endpoints
=====================

Transparent HTML overlays for OBS streaming.
These render with transparent backgrounds for compositing.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from datetime import datetime

router = APIRouter(prefix="/overlay", tags=["Overlays"])


# =============================================================================
# Sensor Overlay
# =============================================================================

@router.get("/sensors", response_class=HTMLResponse)
async def sensor_overlay(request: Request):
    """
    Transparent sensor overlay for OBS.

    Shows: Temperature, Humidity, VPD, Grow Day
    Auto-refreshes every 30 seconds.
    """
    # Get sensor data from app state (no fake fallbacks)
    temp = None
    humidity = None
    vpd = None
    sensor_connected = False

    try:
        sensors = request.app.state.sensors
        reading = await sensors.read_all()
        temp = reading.get("temperature")
        humidity = reading.get("humidity")
        vpd = reading.get("vpd")
        sensor_connected = temp is not None
    except Exception:
        pass  # Leave as None, no fake data

    # Get grow day from database
    grow_day = None
    stage = None
    try:
        from db.connection import get_db_session
        from db.models import GrowSession
        from sqlalchemy import select
        async with get_db_session() as session:
            result = await session.execute(
                select(GrowSession).where(GrowSession.is_active == True)
            )
            grow_session = result.scalar_one_or_none()
            if grow_session:
                grow_day = grow_session.current_day
                stage = grow_session.current_stage.value.lower() if grow_session.current_stage else None
    except Exception:
        pass  # Leave as None

    return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="30">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: transparent;
            font-family: 'JetBrains Mono', monospace;
            color: #4ade80;
            padding: 20px;
        }}
        .container {{
            background: rgba(0, 0, 0, 0.7);
            border: 2px solid #4ade80;
            border-radius: 12px;
            padding: 20px;
            display: inline-block;
        }}
        .title {{
            font-size: 14px;
            color: #888;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        .sensor {{
            font-size: 28px;
            margin: 8px 0;
            display: flex;
            justify-content: space-between;
            gap: 20px;
        }}
        .label {{
            color: #6E54FF;
            font-weight: 500;
        }}
        .value {{
            color: #4ade80;
            font-weight: 700;
            text-shadow: 0 0 10px rgba(74, 222, 128, 0.5);
        }}
        .day {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #333;
            font-size: 20px;
            color: #FFD700;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="title">Mon Environment</div>
        <div class="sensor">
            <span class="label">TEMP</span>
            <span class="value">{f"{temp:.1f}F" if temp is not None else "--"}</span>
        </div>
        <div class="sensor">
            <span class="label">RH</span>
            <span class="value">{f"{humidity:.0f}%" if humidity is not None else "--"}</span>
        </div>
        <div class="sensor">
            <span class="label">VPD</span>
            <span class="value">{f"{vpd:.2f}" if vpd is not None else "--"}</span>
        </div>
        <div class="day">
            DAY {grow_day or "--"} - {stage.upper() if stage else "SETUP"}
        </div>
    </div>
</body>
</html>
'''


# =============================================================================
# AI Commentary Overlay
# =============================================================================

@router.get("/commentary", response_class=HTMLResponse)
async def commentary_overlay(request: Request):
    """
    Transparent AI commentary overlay for OBS.

    Shows the latest Grok AI commentary with typewriter effect.
    """
    # Get latest AI output
    try:
        db = request.app.state.db
        async with db() as session:
            repo = request.app.state.repo_class(session)
            latest = await repo.get_latest_ai_output()
            commentary = latest.summary if latest else "Awaiting Grok's wisdom..."
    except Exception:
        commentary = "Mon vibin' in da garden, seen? Environment lookin' irie!"

    # Truncate if too long
    if len(commentary) > 200:
        commentary = commentary[:197] + "..."

    return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="60">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: transparent;
            font-family: 'JetBrains Mono', monospace;
            padding: 20px;
        }}
        .container {{
            background: rgba(0, 0, 0, 0.8);
            border-left: 4px solid #6E54FF;
            padding: 20px;
            max-width: 500px;
        }}
        .header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }}
        .avatar {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #4ade80, #6E54FF);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }}
        .name {{
            color: #4ade80;
            font-weight: bold;
            font-size: 16px;
        }}
        .role {{
            color: #888;
            font-size: 12px;
        }}
        .text {{
            color: #fff;
            font-size: 18px;
            line-height: 1.5;
        }}
        .timestamp {{
            color: #666;
            font-size: 12px;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="avatar">G</div>
            <div>
                <div class="name">Grok</div>
                <div class="role">Mon's AI Caretaker</div>
            </div>
        </div>
        <div class="text">"{commentary}"</div>
        <div class="timestamp">{datetime.now().strftime("%I:%M %p")}</div>
    </div>
</body>
</html>
'''


# =============================================================================
# Token Price Overlay
# =============================================================================

@router.get("/token", response_class=HTMLResponse)
async def token_overlay(request: Request):
    """
    Transparent token price overlay for OBS.

    Shows $MON price and market cap.
    """
    # Get token data (no fake fallbacks)
    price = None
    mcap = None
    change = None

    try:
        from ..blockchain import NadFunClient
        client = NadFunClient()
        metrics = await client.get_token_metrics()
        price = metrics.price_usd
        mcap = metrics.market_cap
        change = metrics.price_change_24h
    except Exception:
        pass  # Leave as None, no fake data

    # Format with None handling
    if price is not None:
        price_str = f"${price:.6f}" if price < 0.01 else f"${price:.4f}"
    else:
        price_str = "--"

    if mcap is not None:
        mcap_str = f"${mcap/1000:.1f}K" if mcap < 1_000_000 else f"${mcap/1_000_000:.2f}M"
    else:
        mcap_str = "--"

    change_color = "#4ade80" if change and change >= 0 else "#ef4444" if change else "#888"
    change_str = f"+{change:.1f}%" if change and change >= 0 else f"{change:.1f}%" if change else "--"

    return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="30">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: transparent;
            font-family: 'JetBrains Mono', monospace;
            padding: 15px;
        }}
        .container {{
            background: rgba(0, 0, 0, 0.8);
            border: 2px solid #FFD700;
            border-radius: 10px;
            padding: 15px 25px;
            display: inline-block;
        }}
        .symbol {{
            color: #FFD700;
            font-size: 24px;
            font-weight: 700;
        }}
        .price {{
            color: #fff;
            font-size: 32px;
            font-weight: 700;
            margin: 5px 0;
        }}
        .change {{
            color: {change_color};
            font-size: 18px;
        }}
        .mcap {{
            color: #888;
            font-size: 14px;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="symbol">$MON</div>
        <div class="price">{price_str}</div>
        <div class="change">{change_str}</div>
        <div class="mcap">MCap: {mcap_str}</div>
    </div>
</body>
</html>
'''


# =============================================================================
# Minimal Sensor Bar
# =============================================================================

@router.get("/bar", response_class=HTMLResponse)
async def sensor_bar_overlay(request: Request):
    """
    Minimal horizontal sensor bar for bottom of stream.
    """
    temp = None
    humidity = None
    vpd = None

    try:
        sensors = request.app.state.sensors
        reading = await sensors.read_all()
        temp = reading.get("temperature")
        humidity = reading.get("humidity")
        vpd = reading.get("vpd")
    except Exception:
        pass  # Leave as None, no fake data

    # Get grow day from database
    grow_day = None
    try:
        from db.connection import get_db_session
        from db.models import GrowSession
        from sqlalchemy import select
        async with get_db_session() as session:
            result = await session.execute(
                select(GrowSession).where(GrowSession.is_active == True)
            )
            grow_session = result.scalar_one_or_none()
            if grow_session:
                grow_day = grow_session.current_day
    except Exception:
        pass

    return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="30">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: transparent;
            font-family: 'JetBrains Mono', monospace;
        }}
        .bar {{
            background: rgba(0, 0, 0, 0.8);
            padding: 10px 20px;
            display: flex;
            gap: 30px;
            align-items: center;
        }}
        .item {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        .label {{
            color: #888;
            font-size: 12px;
        }}
        .value {{
            color: #4ade80;
            font-size: 16px;
            font-weight: 500;
        }}
        .day {{
            color: #FFD700;
        }}
        .logo {{
            color: #6E54FF;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="bar">
        <span class="logo">GROK & MON</span>
        <div class="item">
            <span class="label">DAY</span>
            <span class="value day">{grow_day or "--"}</span>
        </div>
        <div class="item">
            <span class="label">TEMP</span>
            <span class="value">{f"{temp:.0f}F" if temp is not None else "--"}</span>
        </div>
        <div class="item">
            <span class="label">RH</span>
            <span class="value">{f"{humidity:.0f}%" if humidity is not None else "--"}</span>
        </div>
        <div class="item">
            <span class="label">VPD</span>
            <span class="value">{f"{vpd:.2f}" if vpd is not None else "--"}</span>
        </div>
    </div>
</body>
</html>
'''
