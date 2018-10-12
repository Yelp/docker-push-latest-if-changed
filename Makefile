VERSION := 0.0.0
DEB_NAME := docker-push-latest-if-changed_$(VERSION)_all.deb

.PHONY: builddeb
builddeb:
	docker build -f builddeb.Dockerfile -t builddeb .
	mkdir -p dist
	docker run \
		-v $(CURDIR)/dist:/dist:rw \
		builddeb \
	/bin/bash -c "debuild -us -uc -b && mv ../$(DEB_NAME) /dist"

.PHONY: itest_%
itest_%: builddeb
	docker run -v $(CURDIR):/mnt:ro ubuntu:$* /mnt/itest /mnt/dist/$(DEB_NAME)
