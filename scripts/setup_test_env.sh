#!/bin/bash

# Script to set up test environment for backend tests
# This configures PostgreSQL and pgvector for testing.postgresql

set -e

echo "🔧 Setting up test environment..."

# Check if PostgreSQL 16 is installed
if [ ! -d "/usr/local/opt/postgresql@16" ]; then
    echo "❌ PostgreSQL 16 not found. Installing..."
    brew install postgresql@16
else
    echo "✅ PostgreSQL 16 found"
fi

# Check if pgvector is installed for postgresql@16
if [ ! -f "/usr/local/opt/postgresql@16/share/postgresql@16/extension/vector.control" ]; then
    echo "📦 Building pgvector for PostgreSQL 16..."

    # Create temp directory
    TMPDIR=$(mktemp -d)
    cd "$TMPDIR"

    # Clone and build pgvector
    git clone --branch v0.8.1 --depth 1 https://github.com/pgvector/pgvector.git
    cd pgvector

    export PG_CONFIG=/usr/local/opt/postgresql@16/bin/pg_config
    make clean
    make
    make install

    cd ~
    rm -rf "$TMPDIR"

    echo "✅ pgvector installed"
else
    echo "✅ pgvector already installed"
fi

# Check if PATH is configured
SHELL_RC=""
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ] && [ -f "$SHELL_RC" ]; then
    if grep -q "postgresql@16/bin" "$SHELL_RC"; then
        echo "✅ PATH already configured in $SHELL_RC"
    else
        echo "⚠️  Adding PostgreSQL 16 to PATH in $SHELL_RC"
        echo "" >> "$SHELL_RC"
        echo "# PostgreSQL 16 for testing.postgresql" >> "$SHELL_RC"
        echo 'export PATH="/usr/local/opt/postgresql@16/bin:$PATH"' >> "$SHELL_RC"
        echo "✅ PATH configured - restart your shell or run: source $SHELL_RC"
    fi
fi

# Verify installation
echo ""
echo "🔍 Verifying installation..."

if /usr/local/opt/postgresql@16/bin/postgres --version > /dev/null 2>&1; then
    echo "✅ postgres: $(/usr/local/opt/postgresql@16/bin/postgres --version)"
else
    echo "❌ postgres not found"
    exit 1
fi

if /usr/local/opt/postgresql@16/bin/initdb --version > /dev/null 2>&1; then
    echo "✅ initdb: $(/usr/local/opt/postgresql@16/bin/initdb --version)"
else
    echo "❌ initdb not found"
    exit 1
fi

if [ -f "/usr/local/opt/postgresql@16/share/postgresql@16/extension/vector.control" ]; then
    echo "✅ pgvector extension installed"
else
    echo "❌ pgvector extension not found"
    exit 1
fi

echo ""
echo "✨ Test environment setup complete!"
echo ""
echo "⚠️  IMPORTANT: PostgreSQL binaries are now configured in $SHELL_RC"
echo "   but your CURRENT shell session doesn't have them yet."
echo ""
echo "To use this environment, choose ONE option:"
echo ""
echo "Option 1 (Recommended): Reload your current shell"
echo "  source $SHELL_RC"
echo ""
echo "Option 2: Start a new terminal window/tab"
echo ""
echo "Then verify with:"
echo "  which postgres"
echo "  # Should show: /usr/local/opt/postgresql@16/bin/postgres"
echo ""
echo "Finally, run tests:"
echo "  pytest backend/tests/ -v"
