FROM node:20-slim

RUN npm install -g firebase-tools

WORKDIR /firebase
COPY firebase.json .

EXPOSE 9099 4000

CMD ["firebase", "emulators:start", "--project", "demo-audienceroom"]
