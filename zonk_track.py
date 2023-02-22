from typing import BinaryIO

import discord.player
from pytube import YouTube


class ZonkTrack:
    def __init__(self, video: YouTube, filename: str, filepath: str):
        self.video = video
        self.filename = filename
        self.filepath = filepath
        self.file: BinaryIO = None
        self.stream: discord.player.FFmpegPCMAudio = None

    def set_file(self, file: BinaryIO):
        self.file = file

    def stop_playing(self):
        self.file.close()
        self.file = None
        self.stream.cleanup()

    def is_playing(self):
        return self.file is not None

    def get_file(self):
        self.file = self.file or open(self.filepath, "rb")
        return self.file

    def __del__(self):
        self.stop_playing()
