#!/usr/bin/env bash
# Verify both installable APK signatures and enforce the same signing identity.
# This never signs APKs or accesses private keys.
set -euo pipefail

if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "Usage: $0 path/to/app-arm64-v8a-debug.apk" >&2
  exit 2
fi
apk="$1"
sdk_root="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
apksigner="${APKSIGNER_BIN:-${sdk_root}/build-tools/36.0.0/apksigner}"
if [[ ! -x "$apksigner" ]]; then
  echo "Android apksigner not found or not executable: $apksigner" >&2
  exit 2
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
provider="$tmp_dir/accessibility-provider.apk"
if ! unzip -p "$apk" assets/a11y/accessibility-provider.apk > "$provider" || [[ ! -s "$provider" ]]; then
  echo "Embedded accessibility provider APK is missing or empty" >&2
  exit 1
fi

# 'verify' checks signatures and APK contents. Do not use print-certs alone.
"$apksigner" verify --verbose --print-certs "$apk" > "$tmp_dir/main.txt"
"$apksigner" verify --verbose --print-certs "$provider" > "$tmp_dir/provider.txt"

certificate_digest() {
  sed -nE 's/^[[:space:]]*Signer #1 certificate SHA-256 digest: ([[:xdigit:]]{64})[[:space:]]*$/\1/p' "$1"
}
main_cert="$(certificate_digest "$tmp_dir/main.txt")"
provider_cert="$(certificate_digest "$tmp_dir/provider.txt")"
if [[ ! "$main_cert" =~ ^[[:xdigit:]]{64}$ || ! "$provider_cert" =~ ^[[:xdigit:]]{64}$ ]]; then
  echo "Could not determine signing certificate SHA-256 digest for both APKs" >&2
  exit 1
fi
if [[ "${main_cert,,}" != "${provider_cert,,}" ]]; then
  echo "Main and embedded accessibility provider APK certificates differ" >&2
  exit 1
fi
printf 'Main APK SHA-256: '
sha256sum "$apk" | awk '{print $1}'
printf 'Main and embedded provider APK signatures verified; certificate SHA-256: %s\n' "${main_cert,,}"
