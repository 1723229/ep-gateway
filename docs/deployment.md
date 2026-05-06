# Deployment

## Docker

> [!TIP]
> The `-v ~/.hiperone:/root/.hiperone` flag mounts your local config directory into the container, so your config and workspace persist across container restarts.
> The container currently runs as root and reads config from `/root/.hiperone`. Always mount your host config directory to `/root/.hiperone`.
> If you get **Permission denied**, fix ownership on the host first: `sudo chown -R root:root ~/.hiperone`, or pass `--user $(id -u):$(id -g)` and mount to that user's home directory consistently.
>
> [!IMPORTANT]
> Official Docker usage currently means building from this repository with the included `Dockerfile`. Docker Hub images under third-party namespaces are not maintained or verified by HKUDS/nanobot; do not mount API keys or bot tokens into them unless you trust the publisher.

### Docker Compose

```bash
docker compose run --rm nanobot-cli onboard   # first-time setup
vim ~/.hiperone/config.json                    # add API keys
docker compose up -d nanobot-gateway           # start gateway
```

```bash
docker compose run --rm nanobot-cli agent -m "Hello!"   # run CLI
docker compose logs -f nanobot-gateway                   # view logs
docker compose down                                      # stop
```

### Docker

```bash
# Build the image
docker build -t nanobot .

# Initialize config (first time only)
docker run -v ~/.hiperone:/root/.hiperone --rm nanobot onboard

# Edit config on host to add API keys
vim ~/.hiperone/config.json

# Run gateway (connects to enabled channels, e.g. Telegram/Discord/Mochat)
docker run -v ~/.hiperone:/root/.hiperone -p 18790:18790 nanobot gateway

# Or run a single command
docker run -v ~/.hiperone:/root/.hiperone --rm nanobot agent -m "Hello!"
docker run -v ~/.hiperone:/root/.hiperone --rm nanobot status
```

## Linux Service

Run the gateway as a systemd user service so it starts automatically and restarts on failure.

**1. Find the nanobot binary path:**

```bash
which nanobot   # e.g. /home/user/.local/bin/nanobot
```

**2. Create the service file** at `~/.config/systemd/user/nanobot-gateway.service` (replace `ExecStart` path if needed):

```ini
[Unit]
Description=Nanobot Gateway
After=network.target

[Service]
Type=simple
ExecStart=%h/.local/bin/nanobot gateway
Restart=always
RestartSec=10
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=%h

[Install]
WantedBy=default.target
```

**3. Enable and start:**

```bash
systemctl --user daemon-reload
systemctl --user enable --now nanobot-gateway
```

**Common operations:**

```bash
systemctl --user status nanobot-gateway        # check status
systemctl --user restart nanobot-gateway       # restart after config changes
journalctl --user -u nanobot-gateway -f        # follow logs
```

If you edit the `.service` file itself, run `systemctl --user daemon-reload` before restarting.

> **Note:** User services only run while you are logged in. To keep the gateway running after logout, enable lingering:
>
> ```bash
> loginctl enable-linger $USER
> ```

## macOS LaunchAgent

Use a LaunchAgent when you want `nanobot gateway` to stay online after you log in, without keeping a terminal open.

**1. Get the absolute `nanobot` path:**

```bash
which nanobot   # e.g. /Users/youruser/.local/bin/nanobot
```

Use that exact path in the plist. It keeps the Python environment from your install method.

**2. Create `~/Library/LaunchAgents/ai.nanobot.gateway.plist`:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>ai.nanobot.gateway</string>

  <key>ProgramArguments</key>
  <array>
    <string>/Users/youruser/.local/bin/nanobot</string>
    <string>gateway</string>
    <string>--workspace</string>
    <string>/Users/youruser/.hiperone/workspace</string>
  </array>

  <key>WorkingDirectory</key>
  <string>/Users/youruser/.hiperone/workspace</string>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <dict>
    <key>SuccessfulExit</key>
    <false/>
  </dict>

  <key>StandardOutPath</key>
  <string>/Users/youruser/.hiperone/logs/gateway.log</string>

  <key>StandardErrorPath</key>
  <string>/Users/youruser/.hiperone/logs/gateway.error.log</string>
</dict>
</plist>
```

**3. Load and start it:**

```bash
mkdir -p ~/Library/LaunchAgents ~/.hiperone/logs
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.nanobot.gateway.plist
launchctl enable gui/$(id -u)/ai.nanobot.gateway
launchctl kickstart -k gui/$(id -u)/ai.nanobot.gateway
```

**Common operations:**

```bash
launchctl list | grep ai.nanobot.gateway
launchctl kickstart -k gui/$(id -u)/ai.nanobot.gateway   # restart
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/ai.nanobot.gateway.plist
```

After editing the plist, run `launchctl bootout ...` and `launchctl bootstrap ...` again.

> **Note:** if startup fails with "address already in use", stop the manually started `nanobot gateway` process first.
