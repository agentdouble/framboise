from fastmcp import Context, FastMCP

mcp = FastMCP("mcp2")


@mcp.tool
async def echo(message: str, ctx: Context) -> str:
    await ctx.info("echo tool called", extra={"message_length": len(message)})
    return message
