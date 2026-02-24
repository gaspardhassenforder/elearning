#!/usr/bin/env bash
# Bootstrap script for a fresh Ubuntu 22.04 LTS e2-micro VM on GCP.
# Run as root (or with sudo) after the VM is created and the persistent
# disk has been formatted and mounted at /mydata.
#
# Usage:
#   sudo bash gcp-vm-setup.sh
set -euo pipefail

WORKDIR=/opt/open-notebook
IMAGE=ghcr.io/lfnovo/open-notebook:api-v1-latest

echo "=== 1. Add swap (1 GB) ==="
if ! swapon --show | grep -q '/swapfile'; then
  fallocate -l 1G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo "Swap created"
else
  echo "Swap already present — skipping"
fi

echo "=== 2. Install Docker Engine (official apt repo) ==="
if ! command -v docker &>/dev/null; then
  apt-get update -qq
  apt-get install -y --no-install-recommends ca-certificates curl gnupg lsb-release
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable docker
  systemctl start docker
  echo "Docker installed"
else
  echo "Docker already installed — skipping"
fi

echo "=== 3. Verify persistent disk ==="
if [ ! -d /mydata ]; then
  echo "ERROR: /mydata does not exist."
  echo "Please format and mount the persistent disk at /mydata before running this script."
  echo "Example:"
  echo "  mkfs.ext4 /dev/sdb"
  echo "  mkdir /mydata"
  echo "  mount /dev/sdb /mydata"
  echo "  echo '/dev/sdb /mydata ext4 defaults 0 2' >> /etc/fstab"
  exit 1
fi
echo "/mydata exists — OK"

echo "=== 4. Create working directory ==="
mkdir -p "$WORKDIR"

echo "=== 5. Pull GHCR image ==="
docker pull "$IMAGE"

echo "=== 6. Write docker-compose.gcp.yml ==="
cat > "$WORKDIR/docker-compose.gcp.yml" << 'COMPOSE_EOF'
services:
  surrealdb:
    image: surrealdb/surrealdb:v2
    volumes:
      - /mydata:/mydata
    ports:
      - "8000:8000"
    command: start --log info --user root --pass root rocksdb:/mydata/mydatabase.db
    pull_policy: always
    user: root
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s

  worker:
    image: ghcr.io/lfnovo/open-notebook:api-v1-latest
    command: ["uv", "run", "--no-sync", "surreal-commands-worker",
              "--import-modules", "commands"]
    env_file:
      - ./worker.env
    depends_on:
      surrealdb:
        condition: service_healthy
    volumes:
      - /app/data:/app/data
    restart: always
COMPOSE_EOF

echo "=== 7. Write worker.env template (if not present) ==="
if [ ! -f "$WORKDIR/worker.env" ]; then
  cat > "$WORKDIR/worker.env" << 'ENV_EOF'
# SurrealDB connection — internal Docker network
SURREAL_URL=ws://surrealdb:8000/rpc
SURREAL_USER=root
SURREAL_PASSWORD=CHANGE_ME
SURREAL_NAMESPACE=open_notebook
SURREAL_DATABASE=open_notebook

# AI provider keys (worker executes LLM/TTS calls for podcasts and quizzes)
GOOGLE_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GROQ_API_KEY=
MISTRAL_API_KEY=
DEEPSEEK_API_KEY=
XAI_API_KEY=

# Optional: TTS for podcasts
ELEVENLABS_API_KEY=

# Optional: web scraping
FIRECRAWL_API_KEY=
JINA_API_KEY=

# Worker tuning
SURREAL_COMMANDS_RETRY_ENABLED=true
SURREAL_COMMANDS_RETRY_MAX_ATTEMPTS=3
SURREAL_COMMANDS_MAX_TASKS=5
ENV_EOF
  echo "worker.env template written — edit before starting the service"
else
  echo "worker.env already exists — not overwriting"
fi

echo "=== 8. Install systemd unit ==="
cat > /etc/systemd/system/open-notebook-worker.service << 'UNIT_EOF'
[Unit]
Description=Open Notebook Worker
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/open-notebook
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=120

[Install]
WantedBy=multi-user.target
UNIT_EOF

systemctl daemon-reload
systemctl enable open-notebook-worker.service

echo ""
echo "==================================================================="
echo "Setup complete!"
echo ""
echo "NEXT STEPS:"
echo "  1. Edit $WORKDIR/worker.env — fill in passwords and API keys"
echo "  2. Start services: systemctl start open-notebook-worker"
echo "  3. Check status:   docker compose -f $WORKDIR/docker-compose.gcp.yml ps"
echo "  4. View logs:      docker compose -f $WORKDIR/docker-compose.gcp.yml logs -f"
echo ""
echo "Cloud Run env vars to set:"
echo "  SURREAL_URL=ws://<this-vm-external-ip>:8000/rpc"
echo "  SURREAL_USER=root"
echo "  SURREAL_PASSWORD=<same password as in worker.env>"
echo "==================================================================="
