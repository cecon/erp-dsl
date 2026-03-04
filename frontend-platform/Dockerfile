FROM node:20-alpine AS build
WORKDIR /app

# Copy workspace config
COPY pnpm-workspace.yaml ./
COPY packages/chat-ui/package.json ./packages/chat-ui/

# Copy frontend-platform
COPY frontend-platform/package.json ./frontend-platform/

# Install pnpm and dependencies
RUN npm install -g pnpm && cd frontend-platform && pnpm install --no-frozen-lockfile

# Copy source code
COPY packages/chat-ui/ ./packages/chat-ui/
COPY frontend-platform/ ./frontend-platform/

# Build
RUN cd frontend-platform && pnpm run build

FROM nginx:alpine
COPY --from=build /app/frontend-platform/dist /usr/share/nginx/html
COPY frontend-platform/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 5175
