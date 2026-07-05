FROM python:3.12-slim-bookworm

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY race_mcp_gateway ./race_mcp_gateway

ENV MCP_GATEWAY_CONFIG=/config/mcp-gateway.yaml
EXPOSE 3100

CMD ["python", "-m", "race_mcp_gateway.gateway"]
