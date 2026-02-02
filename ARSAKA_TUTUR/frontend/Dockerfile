# ATLAS_CHAT_AI Frontend Dockerfile
# Multi-stage build for smaller image

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM oven/bun:1.1 as builder

WORKDIR /app

# Copy package files
COPY package.json bun.lockb* ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy source code
COPY . .

# Build arguments for environment
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL

# Build
RUN bun run build

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM nginx:alpine as production

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
