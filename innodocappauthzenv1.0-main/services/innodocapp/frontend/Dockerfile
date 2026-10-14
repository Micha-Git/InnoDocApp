# Build stage
FROM node:20-alpine AS build

# ARG for ENV Variables
ARG VUE_APP_OIDC_CONFIG
ARG VUE_APP_OIDC_REDIRECT

ENV VUE_APP_OIDC_CONFIG=$VUE_APP_OIDC_CONFIG
ENV VUE_APP_OIDC_REDIRECT=$VUE_APP_OIDC_REDIRECT

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# Production stage
FROM nginx:1.27-alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Nginx config for SPA + /api proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
