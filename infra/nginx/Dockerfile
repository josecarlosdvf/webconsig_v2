FROM nginx:1.27-alpine

RUN apk add --no-cache openssl apache2-utils

COPY gateway.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
