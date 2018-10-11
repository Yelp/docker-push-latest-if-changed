FROM        ubuntu:bionic
RUN         apt-get update && apt-get install -y --no-install-recommends \
                build-essential \
                debhelper \
                devscripts \
                fakeroot \
            && apt-get clean

WORKDIR     /mnt
