# Development Dockerfile — optimized for fast iteration (bind mount +
# nodemon), not for production. A leaner, multi-stage production
# build belongs in Module 8, once there's a real app to deploy.

FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 4000

CMD ["npm", "run", "dev"]
