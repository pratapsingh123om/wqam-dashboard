# --- Build Stage ---
    FROM node:20-alpine AS build

    WORKDIR /app
    
    # copy package files
    COPY package*.json ./
    
    # install deps
    RUN npm install
    
    # copy rest of source
    COPY . .
    
    # build for production
    RUN npm run build
    
    # --- Runtime Stage ---
    FROM nginx:stable-alpine AS runtime
    
    # clean existing nginx contents
    RUN rm -rf /usr/share/nginx/html/*
    
    # copy built files
    COPY --from=build /app/dist /usr/share/nginx/html
    
    # copy custom nginx config
    COPY nginx.conf /etc/nginx/conf.d/default.conf
    
    EXPOSE 80    
    CMD ["nginx", "-g", "daemon off;"]
    