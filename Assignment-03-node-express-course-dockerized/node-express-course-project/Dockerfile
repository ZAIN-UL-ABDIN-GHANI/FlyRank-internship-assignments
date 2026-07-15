# Node LTS
FROM node:20-alpine

WORKDIR /usr/src/app

# Install dependencies first so this layer is cached unless package*.json changes
COPY package*.json ./
RUN npm install --omit=dev

# Copy the rest of the project
COPY . .

EXPOSE 3000

# Uses the existing "start" script from package.json — no new scripts invented
CMD ["npm", "start"]
