FROM geonode/geonode:4.1.3

LABEL maintainer="Geodraft Team"

# Install additional Python packages for versioned editing
RUN pip install --no-cache-dir \
    django-reversion==5.0.8 \
    django-simple-history==3.4.0 \
    diff-match-patch==20230430 \
    jsonschema==4.20.0

# Create application directory
RUN mkdir -p /usr/src/geodraft

# Set working directory
WORKDIR /usr/src/geodraft

# Copy project files
COPY ./geodraft ./

# Create necessary directories
RUN mkdir -p /mnt/volumes/statics /mnt/volumes/media

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uwsgi", "--ini", "/usr/src/geodraft/uwsgi.ini"]
