#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^\s*$' | xargs)
fi

# Run the fix script with auto-confirmation
python3 fix_doubled_history.py --yes
