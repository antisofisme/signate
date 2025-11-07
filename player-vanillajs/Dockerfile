# Player Vanilla JS - Static Files with Nginx
FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/

# Copy player files to nginx html directory
COPY index.html /usr/share/nginx/html/
COPY player.html /usr/share/nginx/html/
COPY offline.html /usr/share/nginx/html/
COPY test-commands.html /usr/share/nginx/html/
COPY test-hls.html /usr/share/nginx/html/
COPY service-worker.js /usr/share/nginx/html/
COPY js/ /usr/share/nginx/html/js/
COPY styles/ /usr/share/nginx/html/styles/

# Set permissions
RUN chmod -R 755 /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
