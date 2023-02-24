"""Contains all Zonk bot logic related to initialization and command/event handling."""
from enum import Enum
from typing import List, Optional

import discord
from discord.ext import commands

from youtube_handler import process_query, delete_stream_files
from zonk_track import ZonkTrack


class ConnectResult(Enum):
    """A result to be associated with Zonk's attempt to connect to a voice channel."""
    CONNECTED = "Connected"
    """Successfully connected to the voice channel."""
    MOVED = "Moved"
    """Moved from its previous voice channel into the requested one."""
    ERROR = "Error"
    """Was unable to connect to the requested voice channel."""


# TODO: Create HelpCommand extension class, low priority


class ZonkHandler:
    """The recommended interface to interact with Zonk."""
    bot: commands.Bot = commands.Bot(command_prefix=["zonk,", "zonk", "!"],
                                     case_insensitive=True,
                                     strip_after_prefix=True,
                                     description="Zonks out tunes.",
                                     intents=discord.Intents.all(),
                                     help_command=None)
    """Hello. This is Zonk."""

    queue: List[ZonkTrack] = []
    _current_track: Optional[ZonkTrack] = None
    _voice_client: Optional[discord.VoiceClient] = None

    @staticmethod
    def execute(token: str) -> None:
        """Run Zonk."""
        ZonkHandler.bot.run(token=token)

    @staticmethod
    async def connect(voice_channel: discord.VoiceChannel) -> ConnectResult:
        """Connect Zonk to a voice channel. Ignores a request to connect to the currently connected channel.
        :param voice_channel: The voice channel to connect or move to.
        :return: The result of attempting to connect to the voice channel.
        """
        if not ZonkHandler.is_connected():
            ZonkHandler._voice_client = await voice_channel.connect(timeout=0.5, reconnect=False, self_deaf=True)
            return ConnectResult.CONNECTED

        if voice_channel == ZonkHandler._voice_client.channel:
            return ConnectResult.ERROR

        await ZonkHandler._voice_client.move_to(voice_channel)
        return ConnectResult.MOVED

    @staticmethod
    async def disconnect():
        """Halts track playback, then safely disconnects Zonk from its voice channel."""
        ZonkHandler.stop_playing()

        if ZonkHandler._voice_client:
            await ZonkHandler._voice_client.disconnect()
            ZonkHandler._voice_client.cleanup()
            ZonkHandler._voice_client = None

    @staticmethod
    def cleanup_voice_client() -> None:
        """Required to be called after disconnecting from a channel. ZonkHandler#disconnect does this automatically."""
        ZonkHandler._voice_client.cleanup()

    @staticmethod
    def is_connected() -> bool:
        """Returns whether Zonk is currently connected to a channel."""
        if ZonkHandler._voice_client is None:
            return False
        return True

    @staticmethod
    def get_voice_channel() -> Optional[discord.VoiceChannel]:
        """Returns the voice channel Zonk is connected to, or None if it's not connected."""
        if not ZonkHandler.is_connected():
            return None
        return ZonkHandler._voice_client.channel

    @staticmethod
    def toggle_playback() -> None:
        """Pauses playback if the track is currently playing, or resumes playback if it isn't."""
        if ZonkHandler._voice_client.is_paused():
            ZonkHandler._voice_client.resume()
        else:
            ZonkHandler._voice_client.pause()

    @staticmethod
    def is_paused() -> bool:
        """Returns whether the track playback is paused."""
        return ZonkHandler._voice_client.is_paused()

    @staticmethod
    def stop_playing() -> None:
        """Stop track playback if any track is currently playing."""
        if not ZonkHandler.is_playing():
            return

        if ZonkHandler._current_track.stream:
            ZonkHandler._current_track.stop_playing()

        ZonkHandler._voice_client.stop()

    @staticmethod
    def is_playing() -> bool:
        """Returns whether a track is being played in a voice channel."""
        if not ZonkHandler.is_connected():
            return False
        return ZonkHandler._voice_client.is_playing()

    @staticmethod
    async def play_track(ctx: commands.Context, track: ZonkTrack = None, timestamp: str = "0"):
        """
        Play a track, either from the beginning or starting from timestamp. If no track is specified,
        the current track will be played.

        :param ctx: The commands.Context associated with the command that initiated playback.
        :param track: The ZonkTrack to be played.
        :param timestamp: The time to start the playback at.
        """
        ZonkHandler.stop_playing()

        if track is None:
            track = ZonkHandler._current_track
        else:
            ZonkHandler._current_track = track

        track_audio_file = track.get_file()

        stream = discord.FFmpegPCMAudio(source=track_audio_file,
                                        pipe=True,
                                        before_options=f"-ss {timestamp}")
        ZonkHandler._current_track.set_stream(stream)

        voice_channel = ctx.author.voice.channel
        await ZonkHandler.connect(voice_channel)

        video_details = ZonkHandler._current_track.video

        if timestamp == "0":
            await ctx.send(f"Now playing:\n`{video_details.title}` ({video_details.watch_url})")
        else:
            unit = "" if timestamp[-1].isalpha() else "s"
            await ctx.send(f"`Seeking {timestamp}{unit}.`")

        ZonkHandler._voice_client.play(stream)

    @staticmethod
    async def add_track(ctx: commands.Context, track: ZonkTrack):
        """Add a track to the queue.
        :param ctx: The commands.Context associated with the calling command.
        :param track: The ZonkTrack to be added to the queue.
        """
        ZonkHandler.queue.append(track)
        video_details = track.video
        await ctx.send(f"Added `{video_details.title} ({video_details.watch_url})` to the queue.", suppress_embeds=True)

    @staticmethod
    async def skip_track(ctx: commands.Context):
        """Skip the current track, automatically playing the next one in queue (if any).
        :param ctx: The commands.Context associated with the calling command.
        """
        if ZonkHandler._current_track is None:
            return

        if not ZonkHandler.queue_has_next():
            ZonkHandler._current_track = None
            return

        ZonkHandler._current_track = ZonkHandler.queue.pop(0)
        await ZonkHandler.play_track(ctx)

    @staticmethod
    def queue_has_next():
        """Return True if there are any tracks in the queue, False otherwise."""
        return len(ZonkHandler.queue) > 0

    @staticmethod
    def clear_queue() -> None:
        """Remove all tracks from the queue."""
        ZonkHandler.queue.clear()

    @staticmethod
    def flush():
        """Removes all tracks, current and in queue. Unsafe - make sure to stop playback."""
        ZonkHandler._current_track = None
        ZonkHandler.clear_queue()
        delete_stream_files()

    @property
    def has_track_loaded(self):
        """Whether a track is ready to be played or is currently being played."""
        return self._current_track is not None


@ZonkHandler.bot.event
async def on_ready():
    print(f"Logged in as {ZonkHandler.bot.user} (ID: {ZonkHandler.bot.user.id})")
    print("------")


@ZonkHandler.bot.event
async def on_voice_state_update(member: discord.Member, _: discord.VoiceState, after: discord.VoiceState):
    # Ensure this only triggers for Zonk.
    if not member.id == ZonkHandler.bot.user.id:
        return

    # We can continue playback since we aren't disconnecting from a channel.
    if after.channel is not None:
        return

    await ZonkHandler.disconnect()
    ZonkHandler.flush()


@ZonkHandler.bot.command()
async def connect(ctx: commands.Context):
    """Connects Zonk to your voice channel."""
    if ctx.author.voice is None:
        await ctx.send("You aren't in a voice channel.")
        return

    caller_channel = ctx.author.voice.channel
    result = await ZonkHandler.connect(caller_channel)

    if result == ConnectResult.CONNECTED or result == ConnectResult.MOVED:
        await ctx.send(f"{result.value} to `{caller_channel.name}`.")
    else:
        await ctx.send(f"I am already in `{caller_channel.name}`.")


@ZonkHandler.bot.command()
async def c(ctx: commands.Context):
    await connect(ctx)


@ZonkHandler.bot.command()
async def disconnect(ctx: commands.Context):
    """Disconnects Zonk from its current voice channel."""
    if not ZonkHandler.is_connected():
        await ctx.send("I am not connected to a channel.")
        return

    if ctx.author.voice is None or ctx.author.voice.channel != ZonkHandler.get_voice_channel():
        await ctx.send("You need to be in the same voice channel.")
        return

    await ZonkHandler.disconnect()
    await ctx.send(f"Disconnected from `{ctx.channel.name}`.")


@ZonkHandler.bot.command()
async def dc(ctx: commands.Context):
    await disconnect(ctx)


@ZonkHandler.bot.command()
async def play(ctx: commands.Context, *query_keywords):
    """Play a song matching the query provided. If no query is provided, resumes playback of the current track."""
    # No query, so we try to play the next track in queue.
    if len(query_keywords) == 0:
        if ZonkHandler.queue_has_next():
            await ctx.send("Cannot play - no tracks in queue.")
            return
        elif ZonkHandler.is_playing():
            await ctx.send("A track is already playing.")
            return
        elif not ZonkHandler.has_track_loaded:
            await ctx.send("Cannot resume playback - no track in player.")
            return
        else:
            ZonkHandler.toggle_playback()
            return

    # A query was passed.
    # Search YouTube for the correct track.
    query = " ".join(query_keywords)
    track = await process_query(query)

    # Queue song.
    if ZonkHandler.is_playing():
        await ZonkHandler.add_track(ctx, track)
        return

    # Play current query since no track is playing.
    await ZonkHandler.play_track(ctx, track)


@ZonkHandler.bot.command()
async def p(ctx: commands.Context):
    await play(ctx)


@ZonkHandler.bot.command()
async def seek(ctx: commands.Context, timestamp: str):
    """Seek a specific time in the song. Usage: seek {time in seconds}"""
    if not ZonkHandler.is_connected() or not ZonkHandler.is_playing():
        return

    ZonkHandler.stop_playing()
    await ZonkHandler.play_track(ctx, timestamp=timestamp)


@ZonkHandler.bot.command()
async def pause(ctx: commands.Context):
    """Pause the current track."""
    if not ZonkHandler.is_connected():
        await ctx.send("Error: I am not in a voice channel.")
        return

    if ZonkHandler.is_paused():
        await ctx.send("The track is already paused.")
        return

    ZonkHandler.toggle_playback()


@ZonkHandler.bot.command()
async def stop(ctx: commands.Context):
    """Stop playback and remove all queued tracks."""
    if not ZonkHandler.is_connected():
        return

    ZonkHandler.stop_playing()
    ZonkHandler.flush()

    await ctx.send("Stopped current track and cleared the queue.")


@ZonkHandler.bot.command()
async def s(ctx: commands.Context):
    await stop(ctx)


@ZonkHandler.bot.command()
async def skip(ctx: commands.Context):
    """Skip the current track."""
    if not ZonkHandler.is_connected():
        return

    ZonkHandler.stop_playing()
    await ZonkHandler.skip_track(ctx)


@ZonkHandler.bot.command()
async def queue(ctx: commands.Context):
    """Display all tracks in the queue."""
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
async def q(ctx: commands.Context):
    await queue(ctx)
