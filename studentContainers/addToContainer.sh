#!/bin/bash

# Source directory containing .ipynb files on the host
SRC_DIR="$ABSOLUTE_PATH_TO_COURSE_DIRECTORY"

# Destination directory inside the container (adjust based on your setup)
DEST_DIR="/home/jovyan/work"

# Get all container IDs running the jupyterlab-courseone image
CONTAINERS=$(docker ps --filter "ancestor=jupyterlab-student" --format "{{.ID}}")

# Check if any containers are running
if [ -z "$CONTAINERS" ]; then
  echo "No containers running with image jupyterlab-student"
  exit 1
fi

# Loop through each container
for CONTAINER_ID in $CONTAINERS; do
  echo "Processing container: $CONTAINER_ID"
  
  # Create destination directory if it doesn't exist
  docker exec "$CONTAINER_ID" mkdir -p "$DEST_DIR"
  
  # Copy all .ipynb files
  for NOTEBOOK_FILE in "$SRC_DIR"/*.ipynb; do
    if [ -f "$NOTEBOOK_FILE" ]; then
      FILENAME=$(basename "$NOTEBOOK_FILE")
      
      # Check if the file already exists in the container
      FILE_EXISTS=$(docker exec "$CONTAINER_ID" test -f "$DEST_DIR/$FILENAME" && echo "yes" || echo "no")
      
      if [ "$FILE_EXISTS" == "no" ]; then
        echo "Copying $NOTEBOOK_FILE to container $CONTAINER_ID"
        docker cp -a "$NOTEBOOK_FILE" "$CONTAINER_ID:$DEST_DIR/"
      else
        echo "Skipping $NOTEBOOK_FILE: File already exists in container $CONTAINER_ID"
      fi
    fi
  done
done

echo "All files copied successfully to containers"