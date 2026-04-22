FROM node:22-alpine

RUN apk add --no-cache libc6-compat curl python3

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci 2>/dev/null || npm install

# Copy source
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
EXPOSE 3000

# Run in dev mode for maximum compatibility
# Many sites have TS errors that prevent production builds
# but work perfectly in dev mode (which is how they were developed)
CMD ["npx", "next", "dev", "-p", "3000", "--hostname", "0.0.0.0"]
