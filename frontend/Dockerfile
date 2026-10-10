# ==============================================================================
# Retail KPI Intelligence Platform - Frontend Multi-Stage Dockerfile
# Stage 1: Build React/Vite bundle
# Stage 2: Serve via ultra-light Nginx Alpine
# ==============================================================================

# ----------------- Stage 1: Build -----------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency specifications and install cleanly
COPY package*.json ./
RUN npm ci

# Copy frontend source
COPY . .

# Build argument for target API URL (can be overridden at build time)
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

# Build optimized production bundle
RUN npm run build

# ----------------- Stage 2: Runtime Nginx Server -----------------
FROM nginx:alpine

# Copy built assets to default nginx directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy SPA routing Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
