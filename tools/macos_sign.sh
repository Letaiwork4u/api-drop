#!/usr/bin/env bash
# Sign, package, notarize and staple the macOS build of API Drop.
#
#   tools/macos_sign.sh dist/ApiDrop.app dist/ApiDrop.dmg
#
# Environment:
#   SIGN_IDENTITY       "Developer ID Application: Name (TEAMID)"   default "-" (ad-hoc)
#   APPLE_ID            Apple ID e-mail                                \
#   APPLE_TEAM_ID       10-character team id                            > all three set = notarize
#   APPLE_APP_PASSWORD  app-specific password (appleid.apple.com)     /
#
# Without SIGN_IDENTITY the app is signed ad-hoc (same as releases <= 1.1.0)
# but already with the hardened runtime, so the signed path is exercised too.
set -euo pipefail

APP="${1:?path to ApiDrop.app}"
DMG="${2:?path for ApiDrop.dmg}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENTITLEMENTS="$ROOT/packaging/macos/entitlements.plist"
IDENTITY="${SIGN_IDENTITY:--}"

if [ "$IDENTITY" = "-" ]; then
  TS="--timestamp=none"          # ad-hoc signatures cannot be timestamped
  echo "==> Signing ad-hoc (no Developer ID configured)"
else
  TS="--timestamp"
  echo "==> Signing with: $IDENTITY"
fi

sign() {  # sign one item with hardened runtime
  codesign --force --options runtime $TS --sign "$IDENTITY" "$@"
}

# 1) every Mach-O file inside the bundle, deepest paths first
while IFS= read -r f; do
  if file -b "$f" | grep -q "Mach-O"; then
    sign "$f"
  fi
done < <(find "$APP/Contents" -type f ! -path "$APP/Contents/MacOS/*" | awk '{ print gsub("/","/"), $0 }' | sort -rn | cut -d' ' -f2-)

# 2) nested framework bundles (e.g. Python.framework, Qt frameworks)
while IFS= read -r fw; do
  sign "$fw"
done < <(find "$APP/Contents" -type d -name "*.framework" | awk '{ print gsub("/","/"), $0 }' | sort -rn | cut -d' ' -f2-)

# 3) the app itself, with entitlements on the main executable
sign --entitlements "$ENTITLEMENTS" "$APP"

echo "==> Verifying app signature"
codesign --verify --deep --strict "$APP" && echo "    app signature OK"

# 4) disk image
echo "==> Building $DMG"
STAGE="$(mktemp -d)"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
rm -f "$DMG"
hdiutil create -volname "API Drop" -srcfolder "$STAGE" -ov -format UDZO "$DMG" >/dev/null
rm -rf "$STAGE"

if [ "$IDENTITY" = "-" ]; then
  echo "==> Done (ad-hoc, not notarized)"
  exit 0
fi

codesign --force $TS --sign "$IDENTITY" "$DMG"

# 5) notarize + staple
if [ -n "${APPLE_ID:-}" ] && [ -n "${APPLE_TEAM_ID:-}" ] && [ -n "${APPLE_APP_PASSWORD:-}" ]; then
  echo "==> Notarizing (this usually takes a few minutes)"
  xcrun notarytool submit "$DMG" \
    --apple-id "$APPLE_ID" --team-id "$APPLE_TEAM_ID" --password "$APPLE_APP_PASSWORD" \
    --wait --timeout 30m
  xcrun stapler staple "$DMG"
  xcrun stapler validate "$DMG"
  echo "==> Gatekeeper check"
  spctl --assess --type open --context context:primary-signature --verbose=2 "$DMG"
else
  echo "==> Signed, but NOT notarized (APPLE_ID / APPLE_TEAM_ID / APPLE_APP_PASSWORD missing)"
fi
