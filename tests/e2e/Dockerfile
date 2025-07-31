FROM mcr.microsoft.com/playwright:v1.40.1-focal

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy test files
COPY . .

# Run tests
CMD ["npm", "test"]