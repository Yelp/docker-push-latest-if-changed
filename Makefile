VERSION := 0.0.0
DEB_NAME := docker-push-latest-if-changed_$(VERSION)_all.deb

.PHONY: builddeb
builddeb:
	mkdir -p dist
	debuild -us -uc -b
	mv ../$(DEB_NAME) dist/

.PHONY: itest_%
itest_%: builddeb
	docker run -v $(CURDIR):/mnt:ro ubuntu:$* /mnt/itest /mnt/dist/$(DEB_NAME)
