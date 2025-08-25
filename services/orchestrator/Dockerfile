# Sophia AI Intel - Orchestrator Service
# TypeScript/Node.js microservice for pipeline orchestration

FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies for building
RUN apk add --no-cache python3 make g++

# Copy package.json and tsconfig.json
COPY package.json tsconfig.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build TypeScript
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Change ownership of app directory
RUN chown -R nodejs:nodejs /app
USER nodejs

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8080/healthz || exit 1

# Start the service
CMD ["npm", "start"]
