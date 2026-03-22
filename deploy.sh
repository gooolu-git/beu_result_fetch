
if [ ! -f Dockerfile ]; then
    echo "Error: Dockerfile not found! Run this script from your project root."
    exit 1
fi

echo "Starting Build and Push for BEU Result Engine..."

# Build for standard servers (amd64) and push
docker buildx build --platform linux/amd64 -t gooolu/beu-result-engine:latest --push .

echo "Success! Your image is live on Docker Hub."