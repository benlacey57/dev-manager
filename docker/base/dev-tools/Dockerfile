FROM ubuntu:22.04

# Install common development tools
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    tree \
    unzip \
    zip \
    jq \
    build-essential \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install code-server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt update && apt install gh -y

# Configure code-server
RUN mkdir -p /workspace && \
    mkdir -p /home/coder/.config/code-server

COPY config.yaml /home/coder/.config/code-server/
COPY startup.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/startup.sh

WORKDIR /workspace
EXPOSE 8080

CMD ["/usr/local/bin/startup.sh"]
