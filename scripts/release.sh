echo "Loading Deps"
. ./scripts/build_wheel.sh
echo "Make release"
python3 ./scripts/release.py