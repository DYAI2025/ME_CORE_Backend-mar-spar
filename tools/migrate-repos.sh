#!/bin/bash
# Repository Migration Script for ME_CORE_Backend-mar-spar Monorepo
# Preserves git history while consolidating three repositories

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MONOREPO_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "🚀 ME_CORE Monorepo Migration Script"
echo "===================================="
echo "Target: $MONOREPO_DIR"
echo ""

# Check if we're in the right directory
if [ ! -f "$MONOREPO_DIR/README.md" ]; then
    echo "❌ Error: Not in ME_CORE_Backend-mar-spar directory"
    exit 1
fi

# Function to migrate a repository
migrate_repo() {
    local REPO_URL=$1
    local TARGET_DIR=$2
    local TEMP_DIR="temp_migration_$(date +%s)"
    
    echo "📦 Migrating $REPO_URL to $TARGET_DIR..."
    
    # Clone the repository
    git clone "$REPO_URL" "$TEMP_DIR"
    cd "$TEMP_DIR"
    
    # Rewrite history to move all files to subdirectory
    git filter-branch --index-filter \
        "git ls-files -s | sed \"s-\t\\\"*-&$TARGET_DIR/-\" |
        GIT_INDEX_FILE=\$GIT_INDEX_FILE.new git update-index --index-info &&
        mv \$GIT_INDEX_FILE.new \$GIT_INDEX_FILE" --tag-name-filter cat -- --all
    
    # Clean up filter-branch backup
    git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d
    
    # Go back to monorepo
    cd "$MONOREPO_DIR"
    
    # Add as remote and fetch
    git remote add "$TARGET_DIR-tmp" "./$TEMP_DIR"
    git fetch "$TARGET_DIR-tmp" --tags
    
    # Merge with allow-unrelated-histories
    git merge --allow-unrelated-histories "$TARGET_DIR-tmp/main" -m "Merge $TARGET_DIR repository"
    
    # Remove temporary remote
    git remote remove "$TARGET_DIR-tmp"
    
    # Clean up temp directory
    rm -rf "$TEMP_DIR"
    
    echo "✅ Successfully migrated $TARGET_DIR"
    echo ""
}

# Initialize git if not already
if [ ! -d "$MONOREPO_DIR/.git" ]; then
    echo "📝 Initializing git repository..."
    cd "$MONOREPO_DIR"
    git init
    git add README.md .gitignore
    git commit -m "Initial monorepo setup"
fi

# Ask for repository URLs
echo "Please provide the repository URLs for migration:"
echo ""

read -p "Backend repository URL (_1-_MEWT-backend): " BACKEND_REPO
read -p "Spark NLP repository URL (markerengine-spark-nlp): " SPARK_REPO
read -p "Frontend repository URL (markerengine_frontend): " FRONTEND_REPO

echo ""
echo "🔄 Starting migration process..."
echo ""

# Migrate each repository
if [ ! -z "$BACKEND_REPO" ]; then
    migrate_repo "$BACKEND_REPO" "backend"
fi

if [ ! -z "$SPARK_REPO" ]; then
    migrate_repo "$SPARK_REPO" "spark-nlp"
fi

if [ ! -z "$FRONTEND_REPO" ]; then
    migrate_repo "$FRONTEND_REPO" "frontend"
fi

# Clean up any leftover files
echo "🧹 Cleaning up migration artifacts..."
cd "$MONOREPO_DIR"

# Remove old root-level files that should be in subdirectories
find . -maxdepth 1 -name "package.json" -o -name "requirements.txt" -o -name "Dockerfile" | \
    grep -v -E "(^./backend/|^./spark-nlp/|^./frontend/)" | xargs rm -f

# Create unified requirements files
echo "📋 Creating unified dependency files..."

# Python dependencies
cat > requirements.txt << EOF
# Backend dependencies
-r backend/requirements.txt

# Spark dependencies (optional)
# Uncomment if using Spark NLP
# -r spark-nlp/requirements-spark.txt
EOF

# Update git
git add -A
git commit -m "Complete monorepo migration and cleanup"

echo ""
echo "✅ Migration completed successfully!"
echo ""
echo "Next steps:"
echo "1. Review the migrated structure"
echo "2. Run tests to ensure everything works"
echo "3. Update CI/CD pipelines"
echo "4. Push to remote: git remote add origin https://github.com/DYAI2025/ME_CORE_Backend-mar-spar.git"
echo "5. Push changes: git push -u origin main"
echo ""
echo "🎉 Happy coding with your new monorepo!"