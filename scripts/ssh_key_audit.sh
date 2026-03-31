#!/usr/bin/env bash
# Audit SSH keys and authorized hosts
set -uo pipefail

echo "=== SSH KEY AUDIT ==="
echo ""

echo "--- SSH keys in ~/.ssh ---"
ssh_dir="$HOME/.ssh"

if [ ! -d "$ssh_dir" ]; then
    echo "  ~/.ssh directory not found"
else
    found_key=false
    for key in "$ssh_dir"/id_*; do
        # Skip glob that doesn't expand
        [ -f "$key" ] || continue
        # Skip public key files
        [[ "$key" == *.pub ]] && continue

        found_key=true
        pub="${key}.pub"
        if [ -f "$pub" ]; then
            key_type=$(awk '{print $1}' "$pub" 2>/dev/null || echo "unknown")
            key_comment=$(awk '{print $3}' "$pub" 2>/dev/null || echo "(no comment)")
            key_bits=$(ssh-keygen -lf "$pub" 2>/dev/null | awk '{print $1}' || echo "unknown")
            key_fp=$(ssh-keygen -lf "$pub" 2>/dev/null | awk '{print $2}' || echo "unknown")
            echo "  Key:         $(basename "$key")"
            echo "  Type:        $key_type ($key_bits bits)"
            echo "  Comment:     $key_comment"
            echo "  Fingerprint: $key_fp"
            echo ""
        else
            echo "  Key:         $(basename "$key") (no matching .pub file)"
            echo ""
        fi
    done

    if [ "$found_key" = false ]; then
        echo "  No SSH private keys found in ~/.ssh/"
        echo ""
    fi
fi

echo "--- Authorized keys ---"
auth_keys="$HOME/.ssh/authorized_keys"
if [ -f "$auth_keys" ]; then
    # Count non-blank, non-comment lines
    active_count=$(grep -v '^[[:space:]]*#' "$auth_keys" 2>/dev/null | grep '[^[:space:]]' | wc -l)
    if [ "$active_count" -eq 0 ]; then
        echo "  authorized_keys file exists but contains no active keys"
    else
        echo "  $active_count authorized key(s):"
        while read -r line; do
            [ -z "$line" ] && continue
            [[ "$line" == \#* ]] && continue
            key_type=$(echo "$line" | awk '{print $1}')
            key_comment=$(echo "$line" | awk '{print $3}')
            echo "    $key_type — ${key_comment:-(no comment)}"
        done < "$auth_keys"
    fi
else
    echo "  No authorized_keys file (this host cannot be logged into via SSH key)"
fi
echo ""

echo "--- Known hosts ---"
known_hosts="$HOME/.ssh/known_hosts"
if [ -f "$known_hosts" ]; then
    count=$(wc -l < "$known_hosts" 2>/dev/null || echo 0)
    echo "  $count known hosts"
else
    echo "  No known_hosts file"
fi
echo ""

echo "--- GPG keys ---"
if command -v gpg &>/dev/null; then
    gpg_output=$(gpg --list-keys --keyid-format short 2>/dev/null || true)
    if [ -z "$gpg_output" ]; then
        echo "  No GPG keys found"
    else
        echo "$gpg_output"
    fi
else
    echo "  GPG not installed"
fi
