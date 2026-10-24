#!/usr/bin/env bash
# Build a cmf-control .deb from the current source tree.
#
# Usage:
#   tools/build-deb.sh [VERSION]
#
# VERSION defaults to pyproject.toml's project.version. The produced
# package is written to ./dist/cmf-control_<version>_all.deb.

set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

if [[ $# -ge 1 ]]; then
    version="$1"
else
    version="$(python3 -c "import tomllib; print(tomllib.loads(open('pyproject.toml','rb').read().decode())['project']['version'])")"
fi

if [[ -z "$version" ]]; then
    echo "ERROR: could not determine version" >&2
    exit 1
fi

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

pkgroot="$workdir/cmf-control_${version}_all"
mkdir -p \
    "$pkgroot/DEBIAN" \
    "$pkgroot/usr/bin" \
    "$pkgroot/usr/lib/python3/dist-packages" \
    "$pkgroot/usr/share/applications" \
    "$pkgroot/usr/share/icons/hicolor/256x256/apps" \
    "$pkgroot/usr/share/doc/cmf-control"

# Python package tree (keeps assets/, protocol/, bt/, ui/, features/...)
cp -r cmf_control "$pkgroot/usr/lib/python3/dist-packages/"
find "$pkgroot/usr/lib/python3/dist-packages/cmf_control" \
    \( -name "__pycache__" -o -name "*.pyc" \) -exec rm -rf {} +

# CLI/launcher wrapper
cat > "$pkgroot/usr/bin/cmf-control" <<'EOF'
#!/usr/bin/python3
from cmf_control.main import main
main()
EOF
chmod 755 "$pkgroot/usr/bin/cmf-control"

# Desktop entry + icon
cp packaging/debian/cmf-control.desktop "$pkgroot/usr/share/applications/"
cp cmf_control/assets/icon.png "$pkgroot/usr/share/icons/hicolor/256x256/apps/cmf-control.png"

# Docs: copyright + README
cp packaging/debian/copyright "$pkgroot/usr/share/doc/cmf-control/copyright"
cp README.md "$pkgroot/usr/share/doc/cmf-control/README.md"

# Control file with version substituted in
sed "s/@VERSION@/$version/g" packaging/debian/control.in > "$pkgroot/DEBIAN/control"

# Installed-Size (KB)
installed_size="$(du -sk --exclude=DEBIAN "$pkgroot" | awk '{print $1}')"
printf 'Installed-Size: %s\n' "$installed_size" >> "$pkgroot/DEBIAN/control"

mkdir -p dist
dpkg-deb --root-owner-group --build "$pkgroot" "dist/cmf-control_${version}_all.deb" >/dev/null

echo "Built: dist/cmf-control_${version}_all.deb"
dpkg-deb --info "dist/cmf-control_${version}_all.deb" | sed -n '1,20p'
