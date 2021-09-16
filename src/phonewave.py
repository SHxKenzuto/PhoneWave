
''' Copyright (C) 2021 SHxKenzuto and SimonJohnny
    This file is part of PhoneWave.
    PhoneWave is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    PhoneWave is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with PhoneWave.  If not, see <http://www.gnu.org/licenses/>.
'''
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
    lista_video=re.findall(r"watch\?v=(\S{11})", src.read().decode())
    return "https://www.youtube.com/watch?v="+lista_video[0]

def generaMusica(url_video):
    opzioni_ffmpeg = {'before_options':'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options':'-vn'}
    musica = pafy.new(url_video)
    audio = musica.getbestaudio()
    return FFmpegPCMAudio(audio.url,**opzioni_ffmpeg)

@bot.command()
async def play(ctx,*,msg):
    if ctx.message.author.voice==None:
        await ctx.send("Devi essere in un canale vocale per usare questo comando")
        return
    canale_vocale = ctx.message.author.voice.channel
    voce = discord.utils.get(ctx.guild.voice_channels,name=canale_vocale.name)
    client_vocale=discord.utils.get(bot.voice_clients,guild=ctx.guild)
    if client_vocale == None:
        client_vocale = await voce.connect()
    else:
        client_vocale.move_to(canale_vocale)
    if re.fullmatch(r"https:\/\/www.youtube.com\/watch\?v=\S{11}",msg) == None:
        url_video = creaUrl(msg)
    else:
        url_video = msg
    await ctx.send(url_video)
    musica_finale = generaMusica(url_video)
    client_vocale.play(musica_finale)
    while client_vocale.is_playing():
        await asyncio.sleep(1)
    await asyncio.sleep(600)
    if not (client_vocale.is_playing()):
        await client_vocale.disconnect()

@bot.command()
async def skip(ctx):
    if ctx.message.author.voice==None:
        await ctx.send("Devi essere in un canale vocale per usare questo comando")
        return
    client_vocale=discord.utils.get(bot.voice_clients,guild=ctx.guild)
    if client_vocale.is_connected() and client_vocale.is_playing() and ctx.message.author.voice.channel == client_vocale.channel:
        client_vocale.stop()

@bot.command()
async def leave(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("Devi essere in un canale vocale per usare questo comando")
		return
	client_vocale=discord.utils.get(bot.voice_clients, guild=ctx.guild)
	if client_vocale.is_connected() and ctx.message.author.voice.channel == client_vocale.channel:
		await client_vocale.disconnect()

@bot.command()
async def pause(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("Devi essere in un canale vocale per usare questo comando")
		return
	client_vocale=discord.utils.get(bot.voice_clients, guild=ctx.guild)
	if client_vocale.is_connected() and client_vocale.is_playing() and ctx.message.author.voice.channel == client_vocale.channel:
		client_vocale.pause()

@bot.command()
async def resume(ctx):
	if ctx.message.author.voice==None:
		await ctx.send("Devi essere in un canale vocale per usare questo comando")
		return
	client_vocale=discord.utils.get(bot.voice_clients, guild=ctx.guild)
	if client_vocale.is_connected() and client_vocale.is_paused() and ctx.message.author.voice.channel == client_vocale.channel:
		client_vocale.resume()


    
bot.run("Your token goes here!")

