# Web Component Testing Policy

**CRITICAL**: NEVER ask the user to check dashboards, web interfaces, or any web components without testing them yourself first using browser automation (Playwright tools).

## Required Workflow

1. Create/update web interface
2. Start the server
3. Use Playwright to navigate to the URL
4. Take screenshots and verify it renders correctly
5. Test interactive elements (buttons, forms, etc.)
6. Fix any errors or issues found
7. ONLY THEN show the user and provide the URL

## Why

This prevents wasting user time on broken interfaces and ensures quality before delivery.

## Verification Mantra

> IT'S NEVER CONFIRMED WORKING UNTIL YOU'VE CHECKED IT WITH A BROWSER AND SCREENSHOT AND INTERACTED WITH IT AND REALLY MADE SURE IT WORKS
