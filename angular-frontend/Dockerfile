# Production Dockerfile for Dinner1 Frontend
# Multi-stage build for optimized Angular production

# Stage 1: Build stage
FROM node:18-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production --silent

# Copy source code
COPY . .

# Build for production with optimizations
RUN npm run build -- --configuration production

# Stage 2: Production stage with Nginx
FROM nginx:1.25-alpine as production

# Install curl for health checks
RUN apk add --no-cache curl

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application from builder stage
COPY --from=builder /app/dist/dinner-app /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1001 -S dinner1 && \
    adduser -S dinner1 -u 1001

# Set proper permissions
RUN chown -R dinner1:dinner1 /usr/share/nginx/html && \
    chown -R dinner1:dinner1 /var/cache/nginx && \
    chown -R dinner1:dinner1 /var/log/nginx && \
    chown -R dinner1:dinner1 /etc/nginx/conf.d

# Touch pid file and set permissions
RUN touch /var/run/nginx.pid && \
    chown -R dinner1:dinner1 /var/run/nginx.pid

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Switch to non-root user
USER dinner1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]