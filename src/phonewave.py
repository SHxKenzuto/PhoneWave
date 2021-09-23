import discord
from discord.ext import commands
import urllib
import re
from discord import FFmpegPCMAudio
import pafy
import asyncio
import random
import queue

phonewaves = {}
bot = commands.Bot(command_prefix='-')

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
	if ctx.guild.id in phonewaves and (phonewaves[ctx.guild.id].loop == False or phonewaves[ctx.guild.id].q.empty()):
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
	voice_channel = ctx.message.author.voice.channel
	voice = discord.utils.get(ctx.guild.voice_channels,name=voice_channel.name)
	voice_client=discord.utils.get(bot.voice_clients,guild=ctx.guild)
	if voice_client == None:
		voice_client = await voice.connect()
	elif not voice_client.is_playing() and voice_channel != voice_client:
		await voice_client.move_to(voice_channel)
	if re.fullmatch(r"https:\/\/www.youtube.com\/watch\?v=\S{11}",msg) == None:
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
		while not phonewaves[ctx.guild.id].q.empty():
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
		phonewaves[ctx.guild.id].latest_player_id = random.random()
		id = phonewaves[ctx.guild.id].latest_player_id
		await player(ctx,voice_client,phonewaves[ctx.guild.id].current_song,id)

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
			await looper(ctx,voice_client,phonewaves[ctx.guild.id].current_song)

@bot.event
async def on_ready():
	print("PhoneWave Bot Started")

bot.run("ODg2OTkzODc0ODA2MDA1ODMx.YT9raw.xPYWCbUDzJ4Cn4UjqVC__pW8__U")

print("PhoneWave Bot Stopped")
