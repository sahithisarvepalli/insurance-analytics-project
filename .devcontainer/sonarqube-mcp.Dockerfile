FROM node:20-alpine

RUN npm install -g sonarqube-mcp-server@1.10.21 --fetch-retries=5 --fetch-retry-mintimeout=20000 --fetch-retry-maxtimeout=120000

ENTRYPOINT ["sonarqube-mcp-server"]
