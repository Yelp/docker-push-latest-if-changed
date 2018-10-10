FROM    ubuntu:bionic
ARG     NGINX_IP
RUN     apt-get update && apt-get install -y wget

# Will download/install dummy.deb depending on whether the nginx
# container serving dummy.deb is up or not. Still builds the
# image in either case. This will give us two images with the
# same set of docker commands, but a different 'dpkg -l'
RUN     wget -q -O /dummy.deb ${NGINX_IP}/dummy.deb || true
RUN     dpkg --install dummy.deb || true

CMD     ["echo", "baz"]
