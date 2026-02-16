#!/bin/bash
# Install Foundry and compile contracts on Chromebook
export PATH="/home/natha/.foundry/bin:$PATH"

echo "=== Installing Foundry ==="
foundryup 2>&1 | tail -10

echo "=== Checking Forge ==="
forge --version

echo "=== Compiling Contracts ==="
cd /home/natha/projects/sol-cannabis/contracts/grow

# Install OpenZeppelin deps
forge install OpenZeppelin/openzeppelin-contracts --no-commit 2>&1 | tail -5

# Compile
forge build 2>&1

echo "=== Done ==="
