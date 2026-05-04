# nginx-proxy per-vhost include for mcp.plus-tard.com
#
# Why this file exists:
# The MCP server uses Streamable HTTP / Server-Sent Events. Default
# nginx-proxy buffering and short timeouts cut sessions and delay events.
#
# How to install (on the VPS):
#
#   sudo mkdir -p /path/to/nginx-proxy/vhost.d
#   sudo cp deploy/vhost.d/mcp.plus-tard.com \
#           /path/to/nginx-proxy/vhost.d/mcp.plus-tard.com
#
# Where /path/to/nginx-proxy/vhost.d is whatever directory your
# nginx-proxy container mounts at /etc/nginx/vhost.d. Then reload:
#
#   docker exec <nginx-proxy-container> nginx -s reload
#
# (Or `docker compose restart nginx-proxy` from the proxy stack.)

# Disable response buffering so SSE events flow through immediately.
proxy_buffering off;
proxy_request_buffering off;

# Required for chunked transfer / keep-alive upstream behavior.
proxy_http_version 1.1;
proxy_set_header Connection "";

# MCP sessions can be idle for long stretches; don't time them out.
proxy_read_timeout 1h;
proxy_send_timeout 1h;
