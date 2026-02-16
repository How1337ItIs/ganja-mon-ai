# Dead simple: Cursor IDE + OpenCode (for a friend)

Your friend does two things: install Cursor, then open the code. **Cursor does the rest.**

---

## What your friend does

### 1. Install Cursor

1. Go to **https://cursor.com**
2. Click **Download** (pick Windows / Mac / Linux if asked).
3. Run the installer. Click through until it finishes.
4. Open **Cursor** from the Start menu (or Applications on Mac).

### 2. Open the code

- In Cursor: **File → Open Folder**
- Go to the folder with the project (e.g. the repo you sent them, or `Documents\my-project`).
- Click **Select Folder** (or **Open** on Mac).

That's it for your friend. The project is open in Cursor.

---

## Cursor does the rest (with specific context + prompt)

Your friend (or you) opens Cursor's **AI chat** (Ctrl+L or Cmd+L, or the chat icon), then pastes **context** first, then the **prompt**. Cursor uses that to run the right commands in the integrated terminal.

### Step 1: Paste this context first

Copy the whole block below and paste it into Cursor chat so the AI has the facts it needs:

```
Context for this task:
- OpenCode is a terminal-based AI coding assistant (opencode.ai). It has a CLI and a Cursor/VS Code extension.
- Goal: get OpenCode working inside this Cursor workspace so the user can run `opencode` in the terminal and use the OpenCode extension (shortcuts Ctrl+Esc / Cmd+Esc).
- Install the OpenCode CLI globally: `npm i -g opencode-ai`. If Node.js isn't installed, install it first (nodejs.org LTS or e.g. winget install OpenJS.NodeJS.LTS on Windows, brew on Mac).
- After installing the CLI, run `opencode` once in Cursor's integrated terminal so Cursor can install the OpenCode extension when it prompts. The user should accept the extension install.
- Use only the integrated terminal in Cursor. Do the steps yourself; don't ask the user to run commands in an external terminal.
- User's OS: [FRIEND FILLS IN: Windows / macOS / Linux]
```

**Your friend should replace the last line** with their OS (e.g. `User's OS: Windows` or `User's OS: macOS`).

### Step 2: Paste this prompt

Then send this in the same chat:

```
Do the setup described in the context above: ensure Node.js is available, install the OpenCode CLI globally, then run `opencode` in the integrated terminal so the OpenCode extension can install. Tell me when it's done and what the user should do next (e.g. accept the extension, use Ctrl+Esc to open OpenCode).
```

Cursor will run the commands, handle Node if needed, and tell your friend when to accept the extension and how to use OpenCode.

---

## TL;DR

1. **Friend:** Install Cursor from cursor.com → **File → Open Folder** → choose the project.
2. **Friend:** Open Cursor chat (Ctrl+L / Cmd+L) → paste the **context** block (and fill in OS) → paste the **prompt** → send. Cursor does the rest and says what to do next.
