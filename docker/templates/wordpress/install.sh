#!/bin/bash
# WordPress plugin installation script

set -euo pipefail

WP_CLI_URL="https://raw.githubusercontent.com/wp-cli/wp-cli/master/utils/wp-completion.bash"
CONTAINER_NAME="{{PROJECT_NAME}}-wordpress"

# Essential plugins
PLUGINS=(
    "redis-cache"
    "wordfence"
    "updraftplus"
    "wp-super-cache"
    "yoast-seo"
    "elementor"
    "contact-form-7"
    "akismet"
)

echo "🔧 Installing WordPress plugins..."

for plugin in "${PLUGINS[@]}"; do
    echo "Installing: $plugin"
    docker exec $CONTAINER_NAME wp plugin install $plugin --activate --allow-root
done

# Configure Redis
echo "🔧 Configuring Redis cache..."
docker exec $CONTAINER_NAME wp config set WP_REDIS_HOST "redis" --allow-root
docker exec $CONTAINER_NAME wp config set WP_REDIS_PORT 6379 --allow-root
docker exec $CONTAINER_NAME wp config set WP_REDIS_PASSWORD "{{REDIS_PASSWORD}}" --allow-root
docker exec $CONTAINER_NAME wp redis enable --allow-root

# Set basic WordPress settings
echo "🔧 Configuring WordPress settings..."
docker exec $CONTAINER_NAME wp option update blogname "{{PROJECT_NAME}}" --allow-root
docker exec $CONTAINER_NAME wp option update blogdescription "Powered by automated setup" --allow-root
docker exec $CONTAINER_NAME wp option update siteurl "https://{{DOMAIN}}" --allow-root
docker exec $CONTAINER_NAME wp option update home "https://{{DOMAIN}}" --allow-root

echo "✅ WordPress setup complete!"
echo "🌐 Site: https://{{DOMAIN}}"
echo "🗄️  Database: https://pma.{{DOMAIN}}"
