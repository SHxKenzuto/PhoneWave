import discord
from discord.ext import commands
import urllib
import re
from discord import FFmpegPCMAudio
import pafy
import asyncio
import random

phonewaves = {}
bot = commands.Bot(command_prefix='-')

class PhoneWave:
	def __init__(self,current_song,id):
		self.current_song=current_song
		self.loop = False
		self.player_id = id
	 
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

async def player(ctx,voice_client,url_video, id):
	musica_finale = musicGenerator(url_video)
	voice_client.play(musica_finale)
	await looper(ctx,voice_client,url_video)
	while voice_client.is_playing():
		await asyncio.sleep(1)
	await asyncio.sleep(600)
	if not (voice_client.is_playing()) and phonewaves[ctx.guild.id].player_id == id :
		await voice_client.disconnect()
		del phonewaves[ctx.guild.id]

async def looper(ctx,voice_client,url_video):
	while phonewaves[ctx.guild.id].loop:
		if not voice_client.is_playing():
			phonewaves[ctx.guild.id].player_id = random.random()
			id = phonewaves[ctx.guild.id].player_id
			await player(ctx,voice_client,url_video,id)
		await asyncio.sleep(1)

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
	else:
		await voice_client.move_to(voice_channel)
	if re.fullmatch(r"https:\/\/www.youtube.com\/watch\?v=\S{11}",msg) == None:
		url_video = urlCreator(msg)
	else:
		url_video = msg
	phonewaves[ctx.guild.id]=PhoneWave(url_video,random.random())
	id = phonewaves[ctx.guild.id].player_id
	await ctx.send(url_video)
	await player(ctx,voice_client,url_video,id)


@bot.command()
async def skip(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_client=discord.utils.get(bot.voice_clients,guild=ctx.guild)
	if voice_client.is_connected() and voice_client.is_playing() and ctx.message.author.voice.channel == voice_client.channel:
		voice_client.stop()

@bot.command()
async def leave(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_client=discord.utils.get(bot.voice_clients, guild=ctx.guild)
	if voice_client.is_connected() and ctx.message.author.voice.channel == voice_client.channel:
		await voice_client.disconnect()
		del phonewaves[ctx.guild.id]

@bot.command()
async def pause(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_client=discord.utils.get(bot.voice_clients, guild=ctx.guild)
	if voice_client.is_connected() and voice_client.is_playing() and ctx.message.author.voice.channel == voice_client.channel:
		voice_client.pause()

@bot.command()
async def resume(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_client=discord.utils.get(bot.voice_clients, guild=ctx.guild)
	if voice_client.is_connected() and voice_client.is_paused() and ctx.message.author.voice.channel == voice_client.channel:
		voice_client.resume()

@bot.command()
async def replay(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_client=discord.utils.get(bot.voice_clients, guild=ctx.guild)
	if voice_client.is_connected() and not(voice_client.is_playing()) and ctx.message.author.voice.channel == voice_client.channel:
		await ctx.send(phonewaves[ctx.guild.id].current_song)
		phonewaves[ctx.guild.id].player_id = random.random()
		id = phonewaves[ctx.guild.id].player_id
		await player(ctx,voice_client,phonewaves[ctx.guild.id].current_song,id)

@bot.command()
async def loop(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("You have to be in a voice channel in order to use this command")
		return
	voice_client=discord.utils.get(bot.voice_clients, guild=ctx.guild)
	if voice_client.is_connected() and ctx.message.author.voice.channel == voice_client.channel:
		phonewaves[ctx.guild.id].loop=not(phonewaves[ctx.guild.id].loop)
		await ctx.send("Loop {val}".format(val="ON" if phonewaves[ctx.guild.id].loop else "OFF"))
		if phonewaves[ctx.guild.id].loop:
			await looper(ctx,voice_client,phonewaves[ctx.guild.id].current_song)

bot.run("ODg2OTkzODc0ODA2MDA1ODMx.YT9raw.xPYWCbUDzJ4Cn4UjqVC__pW8__U")
