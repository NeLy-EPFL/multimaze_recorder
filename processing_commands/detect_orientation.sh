#!/bin/bash

# Input directory (pass as first argument)
input_dir="$1"

if [[ -z "$input_dir" ]]; then
    echo "Usage: $0 <input_folder>"
    exit 1
fi

# Check if input directory exists
if [[ ! -d "$input_dir" ]]; then
    echo "Input directory does not exist: $input_dir"
    exit 1
fi

# Path to metadata.json
metadata_file="$input_dir/metadata.json"

# Check if metadata.json exists
if [[ ! -f "$metadata_file" ]]; then
    echo "Metadata file not found in $input_dir"
    exit 1
fi

# Extract and print the orientation for each arena
arenas=$(jq -r 'keys[] | select(startswith("Arena"))' "$metadata_file")
for arena in $arenas; do
    orientation=$(jq -r --arg arena "$arena" '.[$arena][4]' "$metadata_file")
    if [[ "$orientation" == "hz" || "$orientation" == "std" ]]; then
        echo "Orientation for $arena: $orientation"
    else
        echo "Unknown orientation for $arena: $orientation"
    fi
done
