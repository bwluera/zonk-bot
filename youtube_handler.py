"""Handles YouTube interfacing for Zonk."""
from os import DirEntry, path, scandir, remove as remove_file

from pytube import YouTube, Search
from validators import url

from zonk_track import ZonkTrack

__STREAMS_DIR = "streams"


async def _get_first_search_result(query: str) -> YouTube:
    """Return the first available search result from YouTube when searching for query.
    If the query is a URL to a YouTube video, then return that exact video.
    :param query: The keywords to search for.
    :return: The video most related to the query.
    """

    if url(query):
        if ("youtube.com" not in query) and ("youtu.be" not in query):
            raise ValueError("This link is not an official YouTube video URL.")

        return YouTube(query)

    search = Search(query)
    return None if len(search.results) == 0 else search.results[0]


async def _download_audio_stream(video: YouTube) -> ZonkTrack:
    """Download the binary audio file from the given video to the local filesystem.
    :param video: The video to extract and download the audio from.
    :return: The ZonkTrack constructed from the video details and audio filepath.
    """
    audio_stream = video.streams.get_audio_only("mp4")
    filename = video.video_id
    audio_path = path.join(__STREAMS_DIR, filename)

    track = ZonkTrack(video, filename, audio_path)

    if path.exists(audio_path):
        return track

    audio_stream.download(output_path="streams", filename=filename)

    return track


async def process_query(query: str) -> ZonkTrack:
    """Takes a search query and returns the most-related track to be played.
    :param query: The keywords to search for.
    :return: A ZonkTrack containing the video and audio details.
    """
    video = await _get_first_search_result(query)
    zonk_track = await _download_audio_stream(video)
    return zonk_track


def delete_stream_files() -> None:
    """Delete all stream files inside the stream folder.
    """
    dir_entry: DirEntry
    with scandir("streams") as stream_dir:
        for dir_entry in stream_dir:
            if dir_entry.is_dir():
                continue
            remove_file(dir_entry.path)
