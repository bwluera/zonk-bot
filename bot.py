from typing import List

import discord
from discord.ext import commands
from youtube_handler import process_query
from zonk_track import ZonkTrack


class ZonkHandler:
    description = "Plays audio in a voice channel."
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix=".", description=description, intents=intents)
    current_track: ZonkTrack = None
    queue: List[ZonkTrack] = []
    voice_client: discord.VoiceClient = None

    @staticmethod
    def queue_has_next():
        return len(ZonkHandler.queue) > 0

    @staticmethod
    def add_track(track: ZonkTrack):
        ZonkHandler.queue.append(track)

    @staticmethod
    def clear_queue():
        ZonkHandler.queue.clear()

    @staticmethod
    def skip_track():
        if ZonkHandler.current_track is None:
            return False

        if ZonkHandler.queue_has_next():
            ZonkHandler.current_track = ZonkHandler.queue.pop(0)
            return True

        ZonkHandler.current_track = None
        return False

    @staticmethod
    def next_track():
        if not ZonkHandler.queue_has_next():
            return None

        return ZonkHandler.queue[0]


@ZonkHandler.bot.event
async def on_ready():
    print(f"Logged in as {ZonkHandler.bot.user} (ID: {ZonkHandler.bot.user.id})")
    print("------")


@ZonkHandler.bot.command()
async def play(ctx: commands.Context, *query_keywords):

    # No args -> play next in queue.
    if len(query_keywords) == 0:
        if ZonkHandler.queue_has_next():
            await ctx.send("Cannot play - no tracks in queue.")
            return
        elif ZonkHandler.current_track.is_playing():
            await ctx.send("A track is already playing.")
            return
        else:
            track = ZonkHandler.queue[0]
    else:
        # Search YouTube for the correct track.
        query = " ".join(query_keywords)
        track = await process_query(query)

    # Queue song.
    if ZonkHandler.current_track and ZonkHandler.current_track.is_playing():
        ZonkHandler.add_track(track)
        video_details = track.video
        await ctx.send(f"Added `{video_details.title} ({video_details.watch_url})` to the queue.", suppress_embeds=True)
        return

    # Play current query since no track is playing.

    ZonkHandler.current_track = track

    await play_current_track(ctx)


@ZonkHandler.bot.command()
async def stop(ctx: commands.Context):
    if ZonkHandler.voice_client is None:
        return

    ZonkHandler.voice_client.stop()
    ZonkHandler.skip_track()

    await ctx.send("Stopped current track.")


@ZonkHandler.bot.command()
async def skip(ctx: commands.Context):
    if ZonkHandler.voice_client is None:
        return

    if ZonkHandler.current_track is None:
        return

    ZonkHandler.voice_client.stop()

    if ZonkHandler.skip_track():
        await play_current_track(ctx)


@ZonkHandler.bot.command()
async def queue(ctx: commands.Context):
    if not ZonkHandler.queue_has_next():
        await ctx.send("`No items in queue.`")
        return

    message = ""

    for index, track in enumerate(ZonkHandler.queue):
        video_details = track.video
        track_details = f"`{index + 1}. {video_details.title} ({video_details.watch_url})`"
        message += track_details

        if index < len(ZonkHandler.queue) - 1:
            message += "\n"

    await ctx.send(message, suppress_embeds=True)


@ZonkHandler.bot.command()
async def seek(ctx: commands.Context, timestamp: str):
    if ZonkHandler.current_track is None:
        return

    if ZonkHandler.voice_client is None:
        return

    ZonkHandler.voice_client.stop()
    await play_current_track(ctx, timestamp)


async def process_channel_change(voice_channel: discord.VoiceChannel):
    if ZonkHandler.voice_client is None:
        ZonkHandler.voice_client = await voice_channel.connect()
        return

    if ZonkHandler.voice_client.channel == voice_channel:
        ZonkHandler.voice_client.stop()
        return

    # Connect to different channel.
    await ZonkHandler.voice_client.disconnect()
    ZonkHandler.voice_client = await voice_channel.connect()


async def play_current_track(ctx: commands.Context, timestamp: str = "0"):
    if ZonkHandler.current_track.stream:
        ZonkHandler.current_track.stop_playing()

    # noinspection PyTypeChecker
    stream = discord.FFmpegPCMAudio(source=ZonkHandler.current_track.get_file(),
                                    pipe=True,
                                    before_options=f"-ss {timestamp}")
    ZonkHandler.current_track.stream = stream

    voice_channel = ctx.author.voice.channel
    await process_channel_change(voice_channel)

    video_details = ZonkHandler.current_track.video

    if timestamp == "0":
        await ctx.send(f"Now playing:\n`{video_details.title}` ({video_details.watch_url})")
    else:
        await ctx.send(f"`Seeking {timestamp}.`")

    ZonkHandler.voice_client.play(stream)
