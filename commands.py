from discord.ext import commands


def setup(bot: commands.Bot):
    @bot.hybrid_command(
        name="disconnect",
        with_app_command=True,
        description="Disconnect the bot from the voice channel",
    )
    async def disconnect(ctx: commands.Context):
        # get voice client and user channel
        voice_client = ctx.guild.voice_client
        voice_channel = getattr(ctx.author.voice, "channel", None)

        if not voice_client:
            await ctx.reply("❌ I'm not connected to any voice channel.")
            return

        if not voice_channel:
            await ctx.reply("❌ You need to be in a voice channel to use this.")
            return

        await voice_client.disconnect()
        await ctx.reply("👋 Disconnected from the voice channel.")
