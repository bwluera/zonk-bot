"""Handles YouTube interfacing for Zonk."""
from os import path

from pytube import YouTube, Search

from zonk_track import ZonkTrack

__STREAMS_DIR = "streams"


async def _get_first_search_result(query: str):
    """Return the first available search result from YouTube when searching for query.
    :param query: The keywords to search for.
    :return: The video most related to the query.
    """
    search = Search(query)
    return None if len(search.results) == 0 else search.results[0]


async def _download_audio_stream(video: YouTube):
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


async def process_query(query: str):
    """Takes a search query and returns the most-related track to be played.
    :param query: The keywords to search for.
    :return: A ZonkTrack containing the video and audio details.
    """
    video = await _get_first_search_result(query)
    zonk_track = await _download_audio_stream(video)
    return zonk_track
