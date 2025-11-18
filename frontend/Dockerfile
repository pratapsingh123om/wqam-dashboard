# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy dependency files first for faster caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of your source code
COPY . .

# Expose Vite port
EXPOSE 5173

# Start dev server on all interfaces (for Docker)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
