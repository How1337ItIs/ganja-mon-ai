"""
Full commerce loop demo showcasing all 5 x402 hackathon features.

This script demonstrates:
1. Oracle pricing discovery
2. Alpha seeker purchases
3. AP2 mandate chain execution
4. Profit allocation
5. Reputation farming

Usage:
    python -m src.x402_hackathon.seeker.demo [--local]
"""

import asyncio
import argparse
import json
from pathlib import Path

import httpx

from src.x402_hackathon.seeker.alpha_seeker import AlphaSeeker
from src.payments.splitter import get_profit_splitter
from src.x402_hackathon.reputation.farming import get_oracle_stats, get_reputation_signals


BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║    🌿 GanjaMon x402 Hackathon: Full Commerce Loop Demo 🌿       ║
║                                                                  ║
║    Autonomous Intelligence Trading via Micropayments            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

SEPARATOR = "─" * 68


async def demo_oracle_pricing_discovery(base_url: str):
    """Feature 1: Oracle Pricing Discovery"""
    print(f"\n{SEPARATOR}")
    print("📊 FEATURE 1: Oracle Pricing Discovery")
    print(SEPARATOR)

    pricing_url = f"{base_url}/api/x402/pricing"
    print(f"🔗 URL: {pricing_url}\n")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(pricing_url)

            if resp.status_code == 200:
                data = resp.json()
                tiers = data.get("tiers", {})

                print(f"✅ Found {len(tiers)} pricing tiers:\n")

                for tier_name, tier_info in tiers.items():
                    price = tier_info.get("price_usd", 0)
                    desc = tier_info.get("description", "No description")
                    signal_type = tier_info.get("signal_type", "N/A")

                    print(f"   • {tier_name}")
                    print(f"     💵 Price: ${price:.4f}")
                    print(f"     📝 {desc}")
                    print(f"     🎯 Signal: {signal_type}\n")
            else:
                print(f"❌ Failed to fetch pricing: {resp.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def demo_alpha_seeker_purchase(base_url: str):
    """Feature 2: Alpha Seeker Purchase"""
    print(f"\n{SEPARATOR}")
    print("🔍 FEATURE 2: Alpha Seeker Purchase")
    print(SEPARATOR)

    x402_base = f"{base_url}/api/x402"
    print(f"🔗 Oracle: {x402_base}\n")

    # Initialize seeker
    seeker = AlphaSeeker(
        oracle_url=x402_base,
        budget_usd=0.50,  # Just buy first two tiers for demo
        use_ap2=False  # Direct x402 for dev mode testing
    )

    print(f"💰 Budget: ${seeker.budget_usd:.2f}\n")

    # Buy sensor-snapshot and daily-vibes
    tiers = ["sensor-snapshot", "daily-vibes"]

    for tier in tiers:
        tier_url = f"{x402_base}/{tier}"
        print(f"   📦 Purchasing: {tier}")

        data = await seeker.buy_consultation(tier_url)

        if "error" in data:
            print(f"      ❌ Error: {data['error']}\n")
            continue

        # Show results
        signal = data.get("signal", "N/A")
        narrative_score = data.get("narrative_score", 0)
        decision = seeker.decide_trade(data)

        print(f"      ✅ Signal: {signal}")
        print(f"      📈 Narrative: {narrative_score:.2f}")
        print(f"      🎯 Decision: {decision}\n")

    # Show stats
    stats = seeker.get_stats()
    print(f"💸 Spent: ${stats['total_spent']:.4f} | Remaining: ${stats['budget_remaining']:.4f}")


async def demo_ap2_mandate_chain():
    """Feature 3: AP2 Mandate Chain"""
    print(f"\n{SEPARATOR}")
    print("⛓️  FEATURE 3: AP2 Mandate Chain Status")
    print(SEPARATOR)

    mandate_log = Path("data/ap2_mandates.json")

    if not mandate_log.exists():
        print("⚠️  No mandate chain data found yet (will be created on first AP2 purchase)\n")
        return

    try:
        with open(mandate_log, "r") as f:
            mandates = json.load(f)

        if not mandates:
            print("📭 No mandate chains recorded yet\n")
            return

        # Show latest mandate chain
        latest = mandates[-1]
        print(f"📋 Latest Mandate Chain:\n")
        print(f"   🆔 Session: {latest.get('ap2_session_id', 'N/A')}")
        print(f"   🕐 Timestamp: {latest.get('timestamp', 'N/A')}")
        print(f"   💵 Total Cost: ${latest.get('total_cost_usd', 0):.4f}")
        print(f"   🔗 Oracle: {latest.get('oracle_url', 'N/A')}")

        steps = latest.get("steps", [])
        print(f"\n   📊 {len(steps)} Steps in Chain:")

        for i, step in enumerate(steps, 1):
            print(f"      {i}. {step.get('step', 'Unknown')}")
            print(f"         Status: {step.get('status', 'N/A')}")
            if step.get('cost_usd'):
                print(f"         Cost: ${step['cost_usd']:.4f}")

        print()

    except Exception as e:
        print(f"❌ Error reading mandate log: {e}\n")


async def demo_profit_allocation():
    """Feature 4: Profit Allocation"""
    print(f"\n{SEPARATOR}")
    print("💰 FEATURE 4: Profit Allocation")
    print(SEPARATOR)

    try:
        splitter = get_profit_splitter()
        status = splitter.get_status()

        print(f"📊 Profit Splitter Status:\n")
        print(f"   💵 Total Profits: ${status.get('total_profit_usd', 0):.2f}")
        print(f"   🔄 Total Splits: {status.get('total_splits', 0)}")

        splits = status.get("splits", {})
        print(f"\n   📈 Allocation Breakdown:")
        print(f"      • Compound (60%): ${splits.get('compound', 0):.2f}")
        print(f"      • Buy $MON (25%): ${splits.get('buy_mon', 0):.2f}")
        print(f"      • Buy $GANJA (10%): ${splits.get('buy_ganja', 0):.2f}")
        print(f"      • Burn (5%): ${splits.get('burn', 0):.2f}")

        print()

    except Exception as e:
        print(f"❌ Error getting profit status: {e}\n")


async def demo_reputation_farming():
    """Feature 5: Reputation Farming"""
    print(f"\n{SEPARATOR}")
    print("🏆 FEATURE 5: Reputation Farming (ERC-8004)")
    print(SEPARATOR)

    try:
        # Get oracle stats
        stats = get_oracle_stats()
        print(f"📊 Oracle Performance:\n")
        print(f"   🔢 Total Calls: {stats.get('oracle_consultations', 0)}")
        print(f"   💵 Revenue: ${stats.get('total_received_usd', 0):.4f}")

        # Get reputation signals (returns a dict)
        signals = get_reputation_signals()
        if signals:
            print(f"\n   📡 ERC-8004 Reputation Signals:")
            for key, value in signals.items():
                print(f"      • {key}: {value}")
        else:
            print(f"\n   📭 No reputation signals published yet")

        print()

    except Exception as e:
        print(f"❌ Error getting reputation data: {e}\n")


async def main():
    """Run full commerce loop demo."""
    parser = argparse.ArgumentParser(description="x402 Hackathon Commerce Loop Demo")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local server (http://localhost:8000)"
    )
    args = parser.parse_args()

    # Determine base URL
    base_url = "http://localhost:8000" if args.local else "https://grokandmon.com"

    # Print banner
    print(BANNER)
    print(f"🌐 Base URL: {base_url}\n")

    # Run all demos
    await demo_oracle_pricing_discovery(base_url)
    await demo_alpha_seeker_purchase(base_url)
    await demo_ap2_mandate_chain()
    await demo_profit_allocation()
    await demo_reputation_farming()

    # Final message
    print(f"\n{SEPARATOR}")
    print("✅ Demo Complete!")
    print(SEPARATOR)
    print("\n🎯 All 5 Features Demonstrated:")
    print("   1. ✅ Oracle Pricing Discovery")
    print("   2. ✅ Alpha Seeker Purchase")
    print("   3. ✅ AP2 Mandate Chain")
    print("   4. ✅ Profit Allocation")
    print("   5. ✅ Reputation Farming")
    print(f"\n{SEPARATOR}\n")


if __name__ == "__main__":
    asyncio.run(main())
