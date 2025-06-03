FROM cgr.dev/chainguard/python:latest-dev as dev

WORKDIR /app

RUN python -m venv venv
ENV PATH="/app/venv/bin":$PATH
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

FROM cgr.dev/chainguard/python:latest

WORKDIR /app

# Copy the source code
COPY src/ /app/src/

COPY --from=dev /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Environment variables for Neo4j connection
ENV NEO4J_URL="bolt://host.docker.internal:7687"
ENV NEO4J_USERNAME="neo4j"
ENV NEO4J_PASSWORD="password"

ENTRYPOINT [ "python", "mcp-neo4j-cypher.py --db-url ${NEO4J_URL} --username ${NEO4J_USERNAME} --password ${NEO4J_PASSWORD}"] ]
