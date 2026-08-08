# =============================================================================
# Stage 1: Build Stage (Compile React JSX into static HTML/CSS/JS)
# =============================================================================
FROM node:20-alpine AS build-stage

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# =============================================================================
# Stage 2: Production Stage (Ultra-lightweight Nginx server ~20MB)
# =============================================================================
FROM nginx:alpine AS production-stage

# Copy compiled static assets from build stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
