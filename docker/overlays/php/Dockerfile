FROM dev-tools:latest

# Install PHP and extensions
RUN apt-get update && apt-get install -y \
    php8.1 \
    php8.1-cli \
    php8.1-fpm \
    php8.1-mysql \
    php8.1-zip \
    php8.1-gd \
    php8.1-mbstring \
    php8.1-curl \
    php8.1-xml \
    php8.1-bcmath \
    composer \
    && rm -rf /var/lib/apt/lists/*

# Install PHP VS Code extensions
RUN code-server --install-extension bmewburn.vscode-intelephense-client \
    --install-extension xdebug.php-debug

COPY php-startup.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/php-startup.sh

CMD ["/usr/local/bin/php-startup.sh"]
