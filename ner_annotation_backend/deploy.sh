docker build . -t ner-backend
docker run -p 8003:5000 ner-backend