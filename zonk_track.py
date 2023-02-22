"""ZonkTracks: They're Zonkin' zooted."""
from typing import BinaryIO, Optional

import discord.player
from pytube import YouTube


class ZonkTrack:
    """Represents audio to be played by Zonk with some useful metadata."""
    def __init__(self, video: YouTube, filename: str, filepath: str):
        self.video = video
        self.filename = filename
        self.filepath = filepath
        self.file: Optional[BinaryIO] = None
        self.stream: Optional[discord.player.FFmpegPCMAudio] = None

    def stop_playing(self):
        """Safely stop playback of this audio stream."""
        if not self.is_playing():
            return

        if self.file and not self.file.closed:
            self.file.close()
            self.file = None

        if self.stream:
            self.stream.cleanup()
            self.stream = None

    def is_playing(self):
        """Returns whether the audio stream is active."""
        return self.stream is not None

    def get_file(self):
        """Returns the file associated with this audio."""
        self.file = self.file or open(self.filepath, "rb")
        return self.file

    def set_stream(self, stream):
        self.stream = stream

    def __del__(self):
        """Automatically stops playback of the stream upon garbage collection."""
        self.stop_playing()
