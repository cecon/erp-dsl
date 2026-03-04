FROM node:20-alpine AS build
WORKDIR /app

# Copy workspace config
COPY pnpm-workspace.yaml ./
COPY packages/chat-ui/package.json ./packages/chat-ui/

# Copy frontend
COPY frontend/package.json ./frontend/

# Install pnpm and dependencies
RUN npm install -g pnpm && cd frontend && pnpm install --no-frozen-lockfile

# Copy source code
COPY packages/chat-ui/ ./packages/chat-ui/
COPY frontend/ ./frontend/

# Build
RUN cd frontend && pnpm run build

# Serve with nginx (includes reverse proxy for /api)
FROM nginx:alpine AS production
COPY --from=build /app/frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 5174
CMD ["nginx", "-g", "daemon off;"]
