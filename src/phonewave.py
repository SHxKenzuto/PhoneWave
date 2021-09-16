import discord
from discord.ext import commands
import urllib
import re
from discord import FFmpegPCMAudio
import pafy
import asyncio

bot = commands.Bot(command_prefix='-')

def creaUrl(msg):
    msg=msg.replace(" ","+")
    url="https://www.youtube.com/results?search_query="+msg
    src=urllib.request.urlopen(url)
    video_list=re.findall(r"watch\?v=(\S{11})", src.read().decode())
    return "https://www.youtube.com/watch?v="+video_list[0]

def generaMusica(url_video):
    ffmpeg_options = {'before_options':'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options':'-vn'}
    music = pafy.new(url_video)
    audio = music.getbestaudio()
    return FFmpegPCMAudio(audio.url,**ffmpeg_options)

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
        voice_client.move_to(voice_channel)
    if re.fullmatch(r"https:\/\/www.youtube.com\/watch\?v=\S{11}",msg) == None:
        url_video = creaUrl(msg)
    else:
        url_video = msg
    await ctx.send(url_video)
    final_music = generaMusica(url_video)
    voice_client.play(final_music)
    while voice_client.is_playing():
        await asyncio.sleep(1)
    await asyncio.sleep(600)
    if not (voice_client.is_playing()):
        await voice_client.disconnect()

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


    
bot.run("Your token goes here!")

