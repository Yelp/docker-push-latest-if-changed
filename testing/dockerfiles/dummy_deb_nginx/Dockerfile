FROM    nginx
COPY    dummy_deb_package /dummy_deb_package
RUN     dpkg --build /dummy_deb_package /usr/share/nginx/html/dummy.deb
