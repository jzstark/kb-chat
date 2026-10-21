import os

from mcp.server.transport_security import TransportSecuritySettings

from .server import mcp


def main() -> None:
    port = int(os.environ.get("PORT", "7879"))
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        # LibreChat reaches us as http://search-mcp:7879 inside the compose network.
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )


if __name__ == "__main__":
    main()
