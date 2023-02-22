from os import path

from pytube import YouTube, Search

from zonk_track import ZonkTrack

STREAMS_DIR = "streams"


async def _get_first_search_result(query: str):
    search = Search(query)
    return None if len(search.results) == 0 else search.results[0]


async def _download_audio_stream(video: YouTube):
    audio_stream = video.streams.get_audio_only("mp4")
    filename = video.video_id
    audio_path = path.join(STREAMS_DIR, filename)

    track = ZonkTrack(video, filename, audio_path)

    if path.exists(audio_path):
        return track

    audio_stream.download(output_path="streams", filename=filename)

    return track


async def process_query(query: str):
    video = await _get_first_search_result(query)
    zonk_track = await _download_audio_stream(video)
    return zonk_track
