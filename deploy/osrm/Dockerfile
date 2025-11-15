FROM osrm/osrm-backend

LABEL maintainer="Your Name <your.email@example.com>"

# Standard OSRM-Port ist 5000
EXPOSE 5000

CMD ["osrm-routed", "--algorithm", "mld", "/data/region.osrm"]
