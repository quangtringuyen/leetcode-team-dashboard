#!/bin/bash
# Cleanup unused files and commit changes

echo "🧹 Cleaning up unused files..."
echo ""

# Remove old backup files (keep only the most recent)
echo "📦 Cleaning old backup files..."
cd data
rm -f history.backup_20251201_203057.json
rm -f history.backup_20251202_202355.json
rm -f history.backup_before_restore_20251202_203110.json
rm -f history.backup_final_fix_20251202_203205.json
# Keep history.backup_normalize_20251202_205206.json as the latest backup

# Remove old backup directories
rm -rf backup_20251121_091039
rm -rf backup_20251124_220043
rm -rf backup_20251124_220109

cd ..

echo "✅ Cleanup complete!"
echo ""
echo "📋 Files to commit:"
git status --short

echo ""
echo "🎯 Ready to commit changes"
