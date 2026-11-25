# Frontend Dockerfile - Multi-stage build
FROM node:20-alpine as base

# Install dependencies only when needed
FROM base as deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci

# Development stage
FROM base as development
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
# Copy source files excluding node_modules and dist
COPY src ./src
COPY index.html ./index.html
COPY package.json ./package.json
COPY package-lock.json* ./
COPY vite.config.ts ./vite.config.ts
COPY tsconfig.json ./tsconfig.json
COPY tsconfig.node.json ./tsconfig.node.json
COPY tailwind.config.js ./tailwind.config.js
COPY postcss.config.js ./postcss.config.js
COPY vite.config.ts ./vite.config.ts
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

# Build stage
FROM base as builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine as production
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]