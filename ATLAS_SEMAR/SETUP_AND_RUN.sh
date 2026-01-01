#!/bin/bash
###############################################################################
# JARVIS Voice Assistant - Complete Setup & Run Script
# This script will install dependencies and run JARVIS
###############################################################################

set -e  # Exit on error

clear
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║           🎙️  JARVIS VOICE ASSISTANT - SETUP & RUN                    ║"
echo "║                      WEEKS 1-5 COMPLETE & LOCKED                      ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check Python version
echo "📋 Step 1: Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "   ✅ Python $PYTHON_VERSION detected"
echo ""

# Step 2: Navigate to project directory
echo "📋 Step 2: Navigating to project directory..."
cd /mnt/f/WINDSURF/neliti_code/signate/SEMAR
echo "   ✅ Current directory: $(pwd)"
echo ""

# Step 3: Display requirements
echo "📋 Step 3: Checking requirements..."
echo "   Requirements to install:"
cat requirements.txt | grep -v "^$" | sed 's/^/      /'
echo ""

# Step 4: Install dependencies
echo "📋 Step 4: Installing dependencies..."
echo "   This may take 2-5 minutes..."
echo ""

if command -v pip3 &> /dev/null; then
    echo "   Using pip3..."
    pip3 install -r requirements.txt
    echo "   ✅ Dependencies installed"
elif command -v pip &> /dev/null; then
    echo "   Using pip..."
    pip install -r requirements.txt
    echo "   ✅ Dependencies installed"
else
    echo "   ⚠️  pip/pip3 not found in PATH"
    echo "   Please install manually:"
    echo "      pip3 install -r requirements.txt"
    echo "   Then run:"
    echo "      python3 -m jarvis.main"
    exit 1
fi
echo ""

# Step 5: Verify syntax
echo "📋 Step 5: Verifying syntax..."
python3 -m py_compile jarvis/components/*.py jarvis/models/*.py tests/*.py 2>&1 | grep -i error || echo "   ✅ All files have valid syntax"
echo ""

# Step 6: Run tests (optional)
echo "📋 Step 6: Running tests (optional)..."
echo "   This verifies all components work correctly"
echo ""
read -p "   Run tests? (y/n) [y]: " -r run_tests
run_tests=${run_tests:-y}

if [[ $run_tests =~ ^[Yy]$ ]]; then
    echo "   Running 104+ architectural tests..."
    python3 -m pytest tests/ -v --tb=short 2>&1 | tail -30 || echo "   ⚠️  Tests need pytest - skipping"
else
    echo "   ⏭️  Skipping tests"
fi
echo ""

# Step 7: Ready to run
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "✅ SETUP COMPLETE!"
echo ""
echo "🚀 To run JARVIS, execute:"
echo ""
echo "   python3 -m jarvis.main"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "📖 USAGE:"
echo "   1. Press F12 and hold"
echo "   2. Speak your command or question"
echo "   3. Release F12"
echo "   4. JARVIS will process and respond"
echo ""
echo "💬 AVAILABLE COMMANDS:"
echo "   • \"help\"            - Show available commands"
echo "   • \"mode coding\"     - Switch to coding mode"
echo "   • \"what is X?\"      - Ask Claude a question"
echo "   • \"delete all\"      - Will block dangerous patterns"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Step 8: Offer to run now
read -p "Run JARVIS now? (y/n) [n]: " -r run_now
run_now=${run_now:-n}

if [[ $run_now =~ ^[Yy]$ ]]; then
    echo ""
    echo "🎙️  Starting JARVIS..."
    echo "   Press F12 to start recording"
    echo "   Release F12 when done"
    echo "   Press Ctrl+C to stop"
    echo ""
    python3 -m jarvis.main
else
    echo ""
    echo "✨ Setup complete! Run JARVIS with:"
    echo "   python3 -m jarvis.main"
    echo ""
fi
