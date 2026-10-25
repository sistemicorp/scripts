#!/usr/bin/env bash
set -u

: <<'SETUP_INSTRUCTIONS'
===============================================================================
git_pull_watcher.sh setup instructions
===============================================================================

Purpose
-------
This script runs on the HOST OS, not inside the Docker container.

The Lente server requests a git pull by creating this trigger file:

    public/.git_trigger

This script watches for that file. When it appears, this script:

    1. creates public/.git_pull_running
    2. removes public/.git_trigger
    3. runs git pull on the host repository using SSH
    4. writes public/.git_pull_result.json
    5. writes/updates public/.git_pull.log
    6. removes public/.git_pull_running

Expected file layout
--------------------
This script expects to live in the public directory:

    repo-root/
      public/
        git_pull_watcher.sh
        .ssh/
          id_ed25519
          id_ed25519.pub
          known_hosts
        .git_trigger
        .git_pull_running
        .git_pull_result.json
        .git_pull.log

The .git_trigger, .git_pull_running, .git_pull_result.json and .git_pull.log
files are created automatically as needed.

The .ssh directory and SSH keys must be created during setup.

Important
---------
The SSH key in public/.ssh should normally be a DEPLOY KEY dedicated to this
repository. Avoid using a personal SSH key unless you understand the security
implications.

For read-only git pull, configure the GitHub deploy key as read-only.

===============================================================================
1. Confirm the repository remote uses SSH
===============================================================================

From the repository root:

    git remote -v

Expected style:

    origin  git@github.com:OWNER/REPO.git (fetch)
    origin  git@github.com:OWNER/REPO.git (push)

Example:

    origin  git@github.com:OWNER/REPO.git (fetch)
    origin  git@github.com:OWNER/REPO.git (push)

If the remote uses HTTPS, change it to SSH:

    git remote set-url origin git@github.com:OWNER/REPO.git

Example:

    git remote set-url origin git@github.com:OWNER/REPO.git

===============================================================================
2. Create SSH keys in public/.ssh
===============================================================================

From the repository root:

    mkdir -p public/.ssh
    chmod 700 public/.ssh

Create a dedicated SSH key:

    ssh-keygen -t ed25519 -C "lente-git-pull@$(hostname)" -f public/.ssh/id_ed25519

When prompted for a passphrase, press Enter for no passphrase.

This creates:

    public/.ssh/id_ed25519
    public/.ssh/id_ed25519.pub

Set permissions:

    chmod 700 public/.ssh
    chmod 600 public/.ssh/id_ed25519
    chmod 644 public/.ssh/id_ed25519.pub

===============================================================================
3. Add the public key to GitHub
===============================================================================

Show the public key:

    cat public/.ssh/id_ed25519.pub

Copy the full output.

In GitHub:

    Repository page
      -> Settings
      -> Deploy keys
      -> Add deploy key

Recommended settings:

    Title:
        Lente git pull - HOSTNAME

    Key:
        paste contents of public/.ssh/id_ed25519.pub

    Allow write access:
        OFF / unchecked

Click:

    Add key

If you do not have permission to add deploy keys, ask a GitHub repository admin.

Alternative:
------------
You can add the key to a GitHub user account under:

    GitHub user profile
      -> Settings
      -> SSH and GPG keys

However, a repository deploy key is usually safer for this use case.

===============================================================================
4. Create known_hosts for GitHub
===============================================================================

Option A: Let SSH create known_hosts on first successful connection
------------------------------------------------------------------

From the public directory:

    cd public

    PUBLIC_DIR="$(pwd)"
    REPO_DIR="$(cd .. && pwd)"

    GIT_SSH_COMMAND="ssh -i $PUBLIC_DIR/.ssh/id_ed25519 -o UserKnownHostsFile=$PUBLIC_DIR/.ssh/known_hosts -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" git -C "$REPO_DIR" pull

Expected first-time message:

    Warning: Permanently added 'github.com' (...) to the list of known hosts.

After this, known_hosts should exist:

    ls -la public/.ssh/known_hosts

Set permissions:

    chmod 600 public/.ssh/known_hosts

Option B: Pre-create known_hosts using ssh-keyscan
-------------------------------------------------

From the repository root:

    ssh-keyscan github.com > public/.ssh/known_hosts
    chmod 600 public/.ssh/known_hosts

For higher security, verify GitHub's current SSH host keys against GitHub's
official documentation before trusting the output.

===============================================================================
5. Test git pull using the dedicated key
===============================================================================

From the repository root:

    PUBLIC_DIR="$(pwd)/public"
    REPO_DIR="$(pwd)"

    GIT_SSH_COMMAND="ssh -i $PUBLIC_DIR/.ssh/id_ed25519 -o UserKnownHostsFile=$PUBLIC_DIR/.ssh/known_hosts -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes" git -C "$REPO_DIR" pull

Expected result:

    Already up to date.

or git pull output showing updates.

There should be no warning like:

    Identity file ... not accessible

If you see that warning, check the key path and permissions.

===============================================================================
6. Make this watcher executable
===============================================================================

From the repository root:

    chmod +x public/git_pull_watcher.sh

===============================================================================
7. Start watcher manually
===============================================================================

Foreground mode, useful for testing:

    ./public/git_pull_watcher.sh

In another terminal, test the trigger:

    touch public/.git_trigger

Then check:

    cat public/.git_pull.log
    cat public/.git_pull_result.json

Background mode:

    nohup ./public/git_pull_watcher.sh > public/.git_pull_watcher.out 2>&1 &

Check that it is running:

    ps aux | grep git_pull_watcher.sh

Watch the log:

    tail -f public/.git_pull.log

Stop it manually:

    pkill -f git_pull_watcher.sh

===============================================================================
8. Start watcher automatically when host boots
===============================================================================

Recommended option: systemd service
-----------------------------------

Create a service file:

    sudo nano /etc/systemd/system/lente-git-pull-watcher.service

Example service file:

    [Unit]
    Description=Lente Git Pull Watcher
    After=network-online.target
    Wants=network-online.target

    [Service]
    Type=simple
    User=YOUR_HOST_USERNAME
    WorkingDirectory=/absolute/path/to/repo-root
    ExecStart=/absolute/path/to/repo-root/public/git_pull_watcher.sh
    Restart=always
    RestartSec=5

    [Install]
    WantedBy=multi-user.target

Replace:

    YOUR_HOST_USERNAME
    /absolute/path/to/repo-root

Example:

    User=lente
    WorkingDirectory=/home/lente/git/scripts
    ExecStart=/home/lente/git/scripts/public/git_pull_watcher.sh

Then enable and start:

    sudo systemctl daemon-reload
    sudo systemctl enable lente-git-pull-watcher.service
    sudo systemctl start lente-git-pull-watcher.service

Check status:

    systemctl status lente-git-pull-watcher.service

View logs:

    journalctl -u lente-git-pull-watcher.service -f

Stop:

    sudo systemctl stop lente-git-pull-watcher.service

Disable boot startup:

    sudo systemctl disable lente-git-pull-watcher.service

Alternative option: crontab @reboot
-----------------------------------

Edit crontab for the host user:

    crontab -e

Add:

    @reboot cd /absolute/path/to/repo-root && ./public/git_pull_watcher.sh >> public/.git_pull_watcher.out 2>&1

systemd is preferred because it restarts the watcher if it exits.

===============================================================================
9. Docker/container notes
===============================================================================

This script must run on the HOST OS because the actual git pull is performed
outside the Docker container.

The Python server inside Docker only creates:

    public/.git_trigger

Therefore, the container and host must share the same public directory, usually
through a Docker volume bind mount.

Verify that when the Station Manager UI creates:

    public/.git_trigger

the host can see that exact same file.

If the file appears inside the container but not on the host, check the Docker
volume mapping.

===============================================================================
10. Troubleshooting
===============================================================================

Trigger file remains present
----------------------------

If public/.git_trigger remains after clicking the GUI button:

    - watcher is not running
    - watcher is watching the wrong directory
    - public directory is not shared correctly between container and host
    - file permissions prevent the watcher from removing it

Check:

    ps aux | grep git_pull_watcher.sh
    ls -la public/.git_trigger
    tail -f public/.git_pull.log

Running file remains forever
----------------------------

If public/.git_pull_running remains:

    - git pull may be stuck
    - watcher may have crashed
    - network may be unavailable
    - SSH may be waiting for input

Check:

    ps aux | grep git
    ps aux | grep git_pull_watcher.sh
    cat public/.git_pull.log

Remove stale running file only if you are sure no git pull is running:

    rm -f public/.git_pull_running

SSH permission error
--------------------

Check:

    chmod 700 public/.ssh
    chmod 600 public/.ssh/id_ed25519
    chmod 600 public/.ssh/known_hosts

Test:

    PUBLIC_DIR="$(pwd)/public"
    REPO_DIR="$(pwd)"

    GIT_SSH_COMMAND="ssh -i $PUBLIC_DIR/.ssh/id_ed25519 -o UserKnownHostsFile=$PUBLIC_DIR/.ssh/known_hosts -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes" git -C "$REPO_DIR" pull

Host key verification failed
----------------------------

Recreate known_hosts:

    rm -f public/.ssh/known_hosts

Then either:

    ssh-keyscan github.com > public/.ssh/known_hosts
    chmod 600 public/.ssh/known_hosts

or use accept-new once:

    PUBLIC_DIR="$(pwd)/public"
    REPO_DIR="$(pwd)"

    GIT_SSH_COMMAND="ssh -i $PUBLIC_DIR/.ssh/id_ed25519 -o UserKnownHostsFile=$PUBLIC_DIR/.ssh/known_hosts -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" git -C "$REPO_DIR" pull

Repository access denied
------------------------

Check:

    - the public key was added to the correct GitHub repository
    - deploy key is enabled
    - remote URL is SSH, not HTTPS
    - repository path is correct
    - GitHub organization allows deploy keys

Check remote:

    git remote -v

Expected:

    git@github.com:OWNER/REPO.git

===============================================================================
SETUP_INSTRUCTIONS

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# This script is expected to live in public/.
PUBLIC_DIR="${PUBLIC_DIR:-$SCRIPT_DIR}"

# Repository root is normally the parent of public/.
# Override with:
#   REPO_DIR=/path/to/repo ./public/git_pull_watcher.sh
REPO_DIR="${REPO_DIR:-$(cd "$PUBLIC_DIR/.." && pwd)}"

TRIGGER_FILE="$PUBLIC_DIR/.git_trigger"
RUNNING_FILE="$PUBLIC_DIR/.git_pull_running"
RESULT_FILE="$PUBLIC_DIR/.git_pull_result.json"
LOG_FILE="$PUBLIC_DIR/.git_pull.log"
HEARTBEAT_FILE="$PUBLIC_DIR/.git_pull_watcher_heartbeat"

SSH_DIR="${SSH_DIR:-$PUBLIC_DIR/.ssh}"
SSH_KEY_FILE="${SSH_KEY_FILE:-$SSH_DIR/id_ed25519}"
SSH_KNOWN_HOSTS_FILE="${SSH_KNOWN_HOSTS_FILE:-$SSH_DIR/known_hosts}"

POLL_SECONDS="${POLL_SECONDS:-2}"

mkdir -p "$PUBLIC_DIR"

json_escape() {
    python3 -c 'import json, sys; print(json.dumps(sys.stdin.read()))'
}

write_result() {
    local success="$1"
    local message="$2"
    local started_at="$3"
    local finished_at
    finished_at="$(date -Iseconds)"

    local escaped_message
    escaped_message="$(printf '%s' "$message" | json_escape)"

    cat > "$RESULT_FILE" <<EOF
{
  "success": $success,
  "message": $escaped_message,
  "started_at": "$started_at",
  "finished_at": "$finished_at"
}
EOF
}

prepare_ssh() {
    if [[ ! -d "$SSH_DIR" ]]; then
        echo "$(date -Iseconds) ERROR: SSH directory not found: $SSH_DIR" >> "$LOG_FILE"
        return 1
    fi

    if [[ ! -f "$SSH_KEY_FILE" ]]; then
        echo "$(date -Iseconds) ERROR: SSH key not found: $SSH_KEY_FILE" >> "$LOG_FILE"
        return 1
    fi

    chmod 700 "$SSH_DIR" 2>/dev/null || true
    chmod 600 "$SSH_KEY_FILE" 2>/dev/null || true

    if [[ -f "$SSH_KNOWN_HOSTS_FILE" ]]; then
        chmod 600 "$SSH_KNOWN_HOSTS_FILE" 2>/dev/null || true
        export GIT_SSH_COMMAND="ssh -i $SSH_KEY_FILE -o UserKnownHostsFile=$SSH_KNOWN_HOSTS_FILE -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes"
    else
        echo "$(date -Iseconds) WARNING: known_hosts not found; using StrictHostKeyChecking=accept-new: $SSH_KNOWN_HOSTS_FILE" >> "$LOG_FILE"
        export GIT_SSH_COMMAND="ssh -i $SSH_KEY_FILE -o UserKnownHostsFile=$SSH_KNOWN_HOSTS_FILE -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
    fi

    return 0
}

cleanup_running_file() {
    rm -f "$RUNNING_FILE"
    rm -f "$HEARTBEAT_FILE"
}

trap cleanup_running_file EXIT
trap 'exit 0' INT TERM  # without the exit, a trapped TERM keeps the loop running

echo "Watching for git pull trigger: $TRIGGER_FILE"
echo "Repository directory: $REPO_DIR"
echo "Public directory: $PUBLIC_DIR"
echo "SSH directory: $SSH_DIR"
echo "SSH key file: $SSH_KEY_FILE"
echo "SSH known_hosts file: $SSH_KNOWN_HOSTS_FILE"
echo "Heartbeat file: $HEARTBEAT_FILE"
echo "Log file: $LOG_FILE"

while true; do
    date -Iseconds > "$HEARTBEAT_FILE"

    if [[ ! -e "$TRIGGER_FILE" ]]; then
        sleep "$POLL_SECONDS"
        continue
    fi

    if [[ -e "$RUNNING_FILE" ]]; then
        echo "$(date -Iseconds) trigger ignored: git pull already running" >> "$LOG_FILE"
        rm -f "$TRIGGER_FILE"
        continue
    fi

    started_at="$(date -Iseconds)"
    touch "$RUNNING_FILE"
    rm -f "$TRIGGER_FILE"

    {
        echo "================================================================"
        echo "$started_at git pull starting"
        echo "repo: $REPO_DIR"
        echo "public dir: $PUBLIC_DIR"
        echo "ssh dir: $SSH_DIR"
        echo "ssh key: $SSH_KEY_FILE"
        echo "known hosts: $SSH_KNOWN_HOSTS_FILE"
    } >> "$LOG_FILE"

    if ! prepare_ssh; then
        message="git pull failed: SSH configuration is invalid"
        echo "$(date -Iseconds) $message" >> "$LOG_FILE"
        write_result "false" "$message" "$started_at"
        rm -f "$RUNNING_FILE"
        continue
    fi

    # Lente shows the result message, so it carries a summary line of the git output
    pull_output="$(git -C "$REPO_DIR" pull 2>&1)"
    rc="$?"
    printf '%s\n' "$pull_output" >> "$LOG_FILE"

    if [[ "$rc" -eq 0 ]]; then
        summary="$(printf '%s\n' "$pull_output" | grep -v '^[[:space:]]*$' | tail -n 1)"
        summary="${summary#"${summary%%[![:space:]]*}"}"  # strip leading spaces
        message="git pull: ${summary:-done}"
        echo "$(date -Iseconds) $message" >> "$LOG_FILE"
        write_result "true" "$message" "$started_at"
    else
        summary="$(printf '%s\n' "$pull_output" | grep -m 1 -E '^(fatal|error):')"
        message="git pull failed with exit code $rc${summary:+: $summary}"
        echo "$(date -Iseconds) $message" >> "$LOG_FILE"
        write_result "false" "$message" "$started_at"
    fi

    rm -f "$RUNNING_FILE"
done
