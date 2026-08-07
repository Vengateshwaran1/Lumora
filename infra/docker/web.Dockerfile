# Build context is the repo root — npm workspaces requires the root
# package.json/lockfile and every workspace's package.json to resolve
# dependencies correctly (see docker-compose.yml).
#
# node:22-slim (Debian/glibc), not node:22-alpine (musl): Vite 8's rolldown
# bundler ships native bindings, and its musl (Alpine) variant fails to
# resolve correctly under npm on this toolchain — a class of bug common to
# Rust-based JS tooling (rolldown, oxide, lightningcss) on Alpine. glibc
# avoids it entirely.
FROM node:22-slim

WORKDIR /app

COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/shared-types/package.json packages/shared-types/package.json
# `npm ci` here would only find native optional-dep bindings (e.g. rolldown)
# for the host platform the lockfile was generated on — a known npm bug
# (npmjs/cli#4828). `npm install` re-resolves platform-specific optional
# deps for the container's actual platform while still honoring the
# lockfile's pinned versions.
RUN npm install

COPY apps/web apps/web
COPY packages/shared-types packages/shared-types

WORKDIR /app/apps/web

EXPOSE 5173

CMD ["npm", "run", "dev"]
