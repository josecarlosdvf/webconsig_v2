FROM node:20-alpine AS builder
WORKDIR /app
ARG VITE_API_URL=/api/v1
ARG VITE_AUTH_MODE=keycloak
ARG VITE_KEYCLOAK_URL=https://localhost:15443/auth
ARG VITE_KEYCLOAK_REALM=webconsig
ARG VITE_KEYCLOAK_CLIENT_ID=webconsig-frontend
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_AUTH_MODE=$VITE_AUTH_MODE
ENV VITE_KEYCLOAK_URL=$VITE_KEYCLOAK_URL
ENV VITE_KEYCLOAK_REALM=$VITE_KEYCLOAK_REALM
ENV VITE_KEYCLOAK_CLIENT_ID=$VITE_KEYCLOAK_CLIENT_ID
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
