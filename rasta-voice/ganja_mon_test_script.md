# Ganja Mon Test Script

Test various speech lengths to identify issues with transcription, Patois transformation, and TTS.

## Short Phrases (1-3 seconds)

### Test 1A
**Read:** "Hello, I'm Ganja Mon."

### Test 1B
**Read:** "Welcome to the grow."

### Test 1C
**Read:** "Let's check the plants."

---

## Medium Phrases (4-7 seconds)

### Test 2A
**Read:** "Ganja Mon is an AI-powered cannabis cultivation system that uses Grok AI to make autonomous growing decisions."

### Test 2B
**Read:** "We monitor temperature, humidity, and VPD to keep the plants healthy and thriving throughout their growth cycle."

### Test 2C
**Read:** "The Purple Milk strain is a sativa-dominant hybrid with amazing trichome production and purple coloration."

---

## Long Passages (8-15 seconds)

### Test 3A
**Read:** "Ganja Mon combines cutting-edge artificial intelligence with traditional cannabis cultivation knowledge. We use sensors to monitor the environment, and Grok AI analyzes the data to make real-time decisions about lighting, watering, and climate control."

### Test 3B
**Read:** "Our current grow is Purple Milk by Compound Genetics. It's a cross between Horchata and Grape Gasoline, creating a sixty-forty sativa-dominant hybrid with incredible bag appeal. We're targeting a late April harvest with optimal trichome development."

### Test 3C
**Read:** "The MON token will launch on the Monad blockchain, which is an EVM-compatible layer one with high throughput and low latency. This allows us to record grow data on-chain and create a transparent, decentralized cultivation system that the community can verify."

---

## Very Long (15+ seconds) - Tests speech loss

### Test 4A
**Read:** "Welcome to Ganja Mon, where artificial intelligence meets cannabis cultivation. I'm your host, and today we're going to talk about how we use cutting-edge technology to grow the highest quality cannabis possible. Our system monitors every aspect of the environment twenty-four seven, from temperature and humidity to carbon dioxide levels and soil moisture. The AI makes intelligent decisions based on this data, adjusting lights, fans, and irrigation to keep the plants in their optimal growth zone."

### Test 4B
**Read:** "Let me tell you about the science behind VPD, which stands for vapor pressure deficit. VPD is the difference between the amount of moisture in the air and how much moisture the air can hold when saturated. This measurement is crucial because it drives transpiration, which is how plants breathe and take up nutrients. During the vegetative stage, we target a VPD between point eight and one point two kilopascals. In flowering, we increase it to between one and one point five kilopascals to strengthen the plant and prevent mold."

---

## Instructions for Testing

1. **Read each test phrase naturally** (don't rush, speak conversationally)
2. **Note the test number** so we can track which ones have issues
3. **Record observations:**
   - Was transcription accurate?
   - Did Patois transformation make sense?
   - Was TTS clear or choppy?
   - Did long speech get cut off?
4. **After each test**, we'll analyze and tune parameters

## Expected Issues to Watch For

- **Choppy TTS:** Audio breaks, stutters, or has gaps
- **Speech loss:** Long passages don't fully process
- **Transcription errors:** Deepgram mishears technical terms
- **Patois issues:** Transformation loses meaning or sounds unnatural
- **Latency:** Delay longer than 4-5 seconds
