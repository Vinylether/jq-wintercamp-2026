FROM harbor.jqdomain.com/docker.io/python:3.10

COPY . /src/pypokerengine
RUN pip install phevaluator -i https://artifactory.jqdomain.com/artifactory/api/pypi/mirrors-pypi/simple
RUN pip install -e /src/pypokerengine -i https://artifactory.jqdomain.com/artifactory/api/pypi/mirrors-pypi/simple

ENTRYPOINT ["python3", "/app/main.py"]

# docker run -it --rm --name=pokerengine_test -v $(pwd)/app:/app pokerengine
