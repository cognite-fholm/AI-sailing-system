FROM signalk/signalk-server:latest

USER root
RUN cd /home/node/.signalk && \
    npm install @signalk/course-provider@^1.4.0 --omit=dev && \
    chown -R node:node /home/node/.signalk
USER node
