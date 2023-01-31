""" Copyright (C) 2021 SHxKenzuto SimonJohnny Boo-ray SgtSteel 
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import discord
from discord.ext import commands
import urllib
import re
from discord import FFmpegPCMAudio
from discord.ext.commands.errors import MissingRequiredArgument
import pafy
import asyncio
import random
import queue

phonewaves = {}
bot = commands.Bot(command_prefix='-', intents=discord.Intents.all())

# INTERNAL DEFS

class PhoneWave:
	def __init__(self,current_song,id):
		self.q = queue.Queue()
		self.q.put(current_song)
		self.current_song = current_song
		self.loop = False
		self.latest_player_id = id
		self.mutex = asyncio.Lock()
		 
def urlCreator(msg):
	url="https://www.youtube.com/results?search_query="+msg
	url = urllib.parse.quote_plus(url.encode("utf8"),safe=':/?=+')
	src=urllib.request.urlopen(url)
	video_list=re.findall(r"watch\?v=(\S{11})", src.read().decode())
	return "https://www.youtube.com/watch?v="+video_list[0]

def musicGenerator(url_video):
	ffmpeg_options = {'before_options':'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options':'-vn'}
	music = pafy.new(url_video)
	audio = music.getbestaudio()
	return FFmpegPCMAudio(audio.url,**ffmpeg_options)

async def player(ctx,voice_client,id):
	if ctx.guild.id in phonewaves:
		await phonewaves[ctx.guild.id].mutex.acquire()
		if ctx.guild.id in phonewaves and not phonewaves[ctx.guild.id].q.empty():
			phonewaves[ctx.guild.id].current_song = phonewaves[ctx.guild.id].q.get()
			await ctx.send(phonewaves[ctx.guild.id].current_song)
			musica_finale = musicGenerator(phonewaves[ctx.guild.id].current_song)
			voice_client.play(musica_finale)
			while voice_client.is_playing():
				await asyncio.sleep(1)
		if ctx.guild.id in phonewaves:
 			phonewaves[ctx.guild.id].mutex.release()
		if voice_client!=None and not voice_client.is_playing() and ctx.guild.id in phonewaves and phonewaves[ctx.guild.id].loop == False and phonewaves[ctx.guild.id].q.empty() and phonewaves[ctx.guild.id].latest_player_id == id:
			await asyncio.sleep(600)
			if voice_client!=None and not voice_client.is_playing() and ctx.guild.id in phonewaves and phonewaves[ctx.guild.id].q.empty() and phonewaves[ctx.guild.id].latest_player_id == id:
				await voice_client.disconnect()
				del phonewaves[ctx.guild.id]

async def looper(ctx,voice_client,url_video):
	while ctx.guild.id in phonewaves and phonewaves[ctx.guild.id].loop:
		if not voice_client.is_playing():
			phonewaves[ctx.guild.id].q.put(url_video)
			phonewaves[ctx.guild.id].latest_player_id = random.random()
			id = phonewaves[ctx.guild.id].latest_player_id
			await player(ctx,voice_client,id)
		await asyncio.sleep(1)

# DISCORD COMMANDS

@bot.command()
async def play(ctx,*,msg):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	if ctx.guild.id in phonewaves and phonewaves[ctx.guild.id].loop:
		await ctx.send("Can't use this command while looping")
		return
	voice_channel = ctx.message.author.voice.channel
	voice = discord.utils.get(ctx.guild.voice_channels,name=voice_channel.name)
	voice_client=discord.utils.get(bot.voice_clients,guild=ctx.guild)
	if voice_client == None:
		voice_client = await voice.connect()
	elif not voice_client.is_playing() and voice_channel != voice_client:
		await voice_client.move_to(voice_channel)
	
	#if re.fullmatch(r"https:\/\/www.youtube.com\/watch\?v=\S{11}",msg) == None:
	if re.fullmatch(r"(?:https?:\/\/)?(?:(?:(?:www\.?)?youtube\.com(?:\/(?:(?:watch\?.*?(v=[^&\s]+).*)|(?:v(\/.*))|(channel\/.+)|(?:user\/(.+))|(?:results\?(search_query=.+))))?)|(?:youtu\.be(\/.*)?))", msg) == None:
		url_video = urlCreator(msg)
	else:
		url_video = msg
	if ctx.guild.id not in phonewaves:
		phonewaves[ctx.guild.id]=PhoneWave(url_video,random.random())
	else:
		if voice_client.is_playing():
			await ctx.send("Song queued in position #{n}.".format(n = phonewaves[ctx.guild.id].q.qsize()+1))
		phonewaves[ctx.guild.id].q.put(url_video)
		phonewaves[ctx.guild.id].latest_player_id = random.random()
	id = phonewaves[ctx.guild.id].latest_player_id
	await player(ctx,voice_client,id)


@bot.command()
async def playlist(ctx,*,msg):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_channel = ctx.message.author.voice.channel
	voice = discord.utils.get(ctx.guild.voice_channels,name=voice_channel.name)
	voice_client=discord.utils.get(bot.voice_clients,guild=ctx.guild)
	if voice_client == None:
		voice_client = await voice.connect()
	elif not voice_client.is_playing() and voice_channel != voice_client:
		await voice_client.move_to(voice_channel)

	playlist_id_search = re.search(r"(?<=list=)([^&]+)+", msg)

	if playlist_id_search is None:
		await ctx.send("Invalid playlist url")
		return

	playlist_id = playlist_id_search.group(0)
	playlist_url = "https://www.youtube.com/playlist?list=" + playlist_id

	page_req = urllib.request.urlopen(playlist_url)
	page_src = page_req.read().decode()


	playlist_links = re.findall(r"watch\?v=(\S{11})", page_src)

	"""
	# questa cosa sarebbe carina, ma non funziona
	if playlist_links is None:
		await ctx.send("No items found in this playlist")
		return
	else:
		await ctx.send("Queued " + len(playlist_links) + " items from " + playlist_url)
	"""

	for video_id in playlist_links:
		video_url = "https://www.youtube.com/watch?v=" + video_id
		if ctx.guild.id not in phonewaves:
			phonewaves[ctx.guild.id]=PhoneWave(video_url,random.random())
		else:
			phonewaves[ctx.guild.id].q.put(video_url)

#		await ctx.send("Put " + video_url + " in queue")

	for i in playlist_links:
		phonewaves[ctx.guild.id].latest_player_id = random.random()
		id = phonewaves[ctx.guild.id].latest_player_id
		await player(ctx,voice_client,id)


@bot.command()
async def skip(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_client=discord.utils.get(bot.voice_clients,guild=ctx.guild)
	if  voice_client!=None and voice_client.is_playing() and ctx.message.author.voice.channel == voice_client.channel:
		voice_client.stop()

@bot.command()
async def skipall(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_client=discord.utils.get(bot.voice_clients,guild=ctx.guild)
	if  voice_client!=None and voice_client.is_playing() and ctx.message.author.voice.channel == voice_client.channel:
		while ctx.guild.id in phonewaves and not phonewaves[ctx.guild.id].q.empty():
			phonewaves[ctx.guild.id].q.get()
		voice_client.stop()


@bot.command()
async def leave(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_client=discord.utils.get(bot.voice_clients, guild=ctx.guild)
	if  voice_client!=None and ctx.message.author.voice.channel == voice_client.channel:
		await voice_client.disconnect()
		del phonewaves[ctx.guild.id]
  
@bot.command()
async def pause(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_client=discord.utils.get(bot.voice_clients, guild=ctx.guild)
	if  voice_client!=None and voice_client.is_playing() and ctx.message.author.voice.channel == voice_client.channel:
		voice_client.pause()

@bot.command()
async def resume(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_client=discord.utils.get(bot.voice_clients, guild=ctx.guild)
	if  voice_client!=None and voice_client.is_paused() and ctx.message.author.voice.channel == voice_client.channel:
		voice_client.resume()

@bot.command()
async def replay(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_client=discord.utils.get(bot.voice_clients, guild=ctx.guild)
	if  voice_client!=None and not voice_client.is_playing() and ctx.message.author.voice.channel == voice_client.channel:
		await ctx.send(phonewaves[ctx.guild.id].current_song)
		phonewaves[ctx.guild.id].q.put(phonewaves[ctx.guild.id].current_song)
		phonewaves[ctx.guild.id].latest_player_id = random.random()
		id = phonewaves[ctx.guild.id].latest_player_id
		await player(ctx,voice_client,id)

@bot.command()
async def loop(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_client=discord.utils.get(bot.voice_clients, guild=ctx.guild)
	if voice_client!=None  and ctx.message.author.voice.channel == voice_client.channel:
		phonewaves[ctx.guild.id].loop=not(phonewaves[ctx.guild.id].loop)
		await ctx.send("Loop {val}".format(val="ON" if phonewaves[ctx.guild.id].loop else "OFF"))
		if phonewaves[ctx.guild.id].loop:
			while ctx.guild.id in phonewaves and not phonewaves[ctx.guild.id].q.empty():
				phonewaves[ctx.guild.id].q.get()
			await looper(ctx,voice_client,phonewaves[ctx.guild.id].current_song)
		else:
			while ctx.guild.id in phonewaves and not phonewaves[ctx.guild.id].q.empty():
				phonewaves[ctx.guild.id].q.get()

@bot.event
async def on_ready():
	print("PhoneWave Bot Started")

@bot.event
async def on_command_error(ctx,error):
	if isinstance(error,MissingRequiredArgument):
		await ctx.send("This command needs an argument")
bot.run("ODg2OTkzODc0ODA2MDA1ODMx.YT9raw.xPYWCbUDzJ4Cn4UjqVC__pW8__U")

print("PhoneWave Bot Stopped")
