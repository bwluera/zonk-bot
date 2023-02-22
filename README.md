# Zonk
###### Last updated: February 22, 2023.

## About
Zonk is a Discord bot that plays audio from YouTube videos.
Videos are searched for using the user's query.
Multiple videos are able to be queued for back-to-back playback.
Zonk uses the [discord.py](https://discordpy.readthedocs.io/en/stable/index.html)
and [pytube](https://pytube.io/en/latest/) libraries to interact with Discord
and YouTube, respectively.

## Commands

#### Command prefix: `!` or `zonk` or `zonk,`
###### Whitespace does not matter. `!play` = `! play` = `zonk play` = `zonk, play`

- **play** `query`: Searches YouTube for `query` and plays the most 
relevant video.
- **seek** `time`: Plays the current video beginning at `time` seconds.
- **stop**: Stops playback and clears the queue.
- **pause**: Pauses playback.
- **connect**: Connects to your voice channel.
- **disconnect**: Disconnects from the voice channel.
- **queue**: Shows the videos in queue.
