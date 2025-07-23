FROM dev-tools:latest

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install global packages
RUN npm install -g \
    typescript \
    @vue/cli \
    @nuxt/cli \
    create-react-app \
    vite \
    nodemon \
    pm2 \
    eslint \
    prettier

# Install Node.js VS Code extensions
RUN code-server --install-extension bradlc.vscode-tailwindcss \
    --install-extension esbenp.prettier-vscode \
    --install-extension ms-vscode.vscode-typescript-next

COPY node-startup.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/node-startup.sh

CMD ["/usr/local/bin/node-startup.sh"]
