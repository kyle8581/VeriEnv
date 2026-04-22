FROM node:18-alpine

RUN apk add --no-cache libc6-compat curl python3
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --ignore-scripts 2>/dev/null || npm install
COPY . .

# Prisma setup if schema exists
RUN if [ -f prisma/schema.prisma ]; then npx prisma generate && (npx prisma migrate deploy 2>/dev/null || npx prisma db push --accept-data-loss 2>/dev/null || true); fi

RUN npm run build 2>/dev/null || true

# Seed DB at build time for reproducibility
RUN if [ -f prisma/schema.prisma ]; then npx prisma db seed 2>/dev/null || npm run db:seed 2>/dev/null || true; fi

# Backup seeded DB for reset
RUN if [ -f dev.db ]; then cp dev.db dev.db.seed; fi

EXPOSE 3000
CMD ["npm", "run", "start", "--", "-p", "3000", "--hostname", "0.0.0.0"]
