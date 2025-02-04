build-all: build-h5 build-electron
build-h5:
	npm run build
build-elctron:
	cd electron-live2d && npm run package
	cp -r ../dist/* out/electron-live2d-${os}-${arch}/www/
	cp *.py out/electron-live2d-${os}-${arch}/
	cd ..
