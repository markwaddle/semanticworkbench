import datetime
from dataclasses import dataclass
import logging
from mcp import ClientCapabilities, RootsCapability, ServerSession
import zoneinfo

from mcp.server.fastmcp import Context, FastMCP
from pydantic import AnyUrl

from . import config, mem

logger = logging.getLogger(__name__)

# Set the name of the MCP server
server_name = "Memory - User Bio MCP Server"


@dataclass
class SessionConfig:
    user_timezone: datetime.tzinfo
    session_id: str


memory_uri = "resource://memory/user-bio"


def create_mcp_server() -> FastMCP:
    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=config.settings.log_level)

    @mcp.tool()
    async def bio(memory: str) -> str:
        """
        Remember long-term details about the user, such as their interests, preferences, experiences, or ongoing projects.
        *DO NOT* use it for short-term details like temporary tasks, one-time events, or what they're doing this weekend.
        *DO NOT* use it for sensitive or private information like passwords, financial info, personal addresses, or private keys.

        Always ensure that memories are:
        - Concise but informative – enough detail to be useful but not overly long.
        - Structured in a clear sentence – stating facts in a way that’s easy to recall and apply.
        - Contextually relevant – focused on long-term or recurring details.
        """

        ctx = mcp.get_context()
        client_roots = await get_session_config(ctx)

        mem.remember(
            session_id=client_roots.session_id,
            user_timezone=client_roots.user_timezone,
            memory=memory,
        )

        await ctx.session.send_resource_updated(uri=AnyUrl(memory_uri))

        return "Memory stored successfully."

    @mcp.tool()
    async def bio_forget(memory: str) -> str:
        """
        Forget a memory. This is used to remove long-term details about the user. Pass a specific memory to remove it.
        """

        ctx = mcp.get_context()
        client_roots = await get_session_config(ctx)

        found = mem.forget(
            session_id=client_roots.session_id,
            memory=memory,
        )

        if not found:
            return "Memory not found."

        await ctx.session.send_resource_updated(uri=AnyUrl(memory_uri))

        return "Memory forgotten successfully."

    @mcp.resource(
        uri=memory_uri, name="User Bio Memory", description="Long-term memory about the user.", mime_type="text/plain"
    )
    async def get_bio() -> str:
        """
        The long-term memories about the user.
        """

        ctx = mcp.get_context()
        client_roots = await get_session_config(ctx)

        memories = mem.get_memories(
            session_id=client_roots.session_id,
        )

        if not memories:
            return "No memories saved."

        # Format the memories into a string
        formatted_memories = "\n".join(f"[{memory.date}] {memory.memory}" for memory in memories)

        return f"Memories about the user:\n{formatted_memories}"

    return mcp


async def get_session_config(ctx: Context[ServerSession, object]) -> SessionConfig:
    """
    Get the session configuration from the client.
    """
    user_timezone: datetime.tzinfo = datetime.timezone.utc
    session_id: str = ""

    if not ctx.session.check_client_capability(ClientCapabilities(roots=RootsCapability())):
        logger.debug("Client does not support roots capability.")
        return SessionConfig(user_timezone=user_timezone, session_id=session_id)

    list_roots_result = await ctx.session.list_roots()

    for root in list_roots_result.roots:
        match root.name:
            case "user-timezone":
                timezone_str = str(root.uri).replace(root.uri.scheme, "")
                try:
                    user_timezone = zoneinfo.ZoneInfo(timezone_str)
                except ValueError:
                    logger.exception("invalid timezone in user-timezone root received from client: %s", root.uri)

            case "session-id":
                session_id = str(root.uri).replace(root.uri.scheme, "")

    return SessionConfig(user_timezone=user_timezone, session_id=session_id)
