# syntax=docker/dockerfile:1.7

# -----------------------------------------------------------------------------
# Portal production image — Next.js 14 with standalone output
# -----------------------------------------------------------------------------

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install

FROM node:20-alpine AS builder
WORKDIR /app

# DEV_BYPASS_AUTH is the only flag that must be baked in (it gates which UI
# branch is rendered server-side). All Entra / backend config is served at
# runtime via /api/config so the same image works across environments.
ARG NEXT_PUBLIC_DEV_BYPASS_AUTH=false
ENV NEXT_PUBLIC_DEV_BYPASS_AUTH=$NEXT_PUBLIC_DEV_BYPASS_AUTH \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0 \
    NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 --ingroup nodejs nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
