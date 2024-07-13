pushd wheels || exit

python -m pip wheel ppmd-cffi==0.5.0
python -m pip wheel bcj-cffi==0.5.1
python -m pip wheel py7zr==0.20.8
python -m pip wheel xmltodict==0.13.0
python -m pip wheel platformdirs==4.1.0

popd || exit