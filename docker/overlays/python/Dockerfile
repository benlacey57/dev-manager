FROM dev-tools:latest

# Install Python and related tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install common Python packages
RUN pip3 install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    django \
    flask \
    requests \
    pandas \
    numpy \
    pytest \
    black \
    flake8 \
    mypy \
    poetry \
    pipenv

# Install Python-specific VS Code extensions
RUN code-server --install-extension ms-python.python \
    --install-extension ms-python.pylint \
    --install-extension ms-python.black-formatter \
    --install-extension ms-toolsai.jupyter

COPY python-startup.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/python-startup.sh

CMD ["/usr/local/bin/python-startup.sh"]
