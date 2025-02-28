import discord
from discord.ext import commands
import yt_dlp
import asyncio

# Configuración de permisos
intents = discord.Intents.default()
intents.message_content = True

# Configuración del bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Variables globales
queue = []
current_song = None

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

@bot.command()
async def join(ctx):
    """Hace que el bot se una al canal de voz del usuario"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("❌ ¡Debes estar en un canal de voz!")

@bot.command()
async def leave(ctx):
    """Hace que el bot salga del canal de voz"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        queue.clear()
    else:
        await ctx.send("❌ No estoy en un canal de voz.")

@bot.command()
async def play(ctx, *, search: str):
    """Reproduce música desde un enlace de YouTube o búsqueda"""
    global current_song

    if not ctx.voice_client:
        await ctx.invoke(join)

    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch',
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search, download=False)
        url2 = info['entries'][0]['url'] if 'entries' in info else info['url']
        title = info['entries'][0]['title'] if 'entries' in info else info['title']

    queue.append((url2, title))

    if not ctx.voice_client.is_playing():
        await play_next(ctx)
    else:
        await ctx.send(f"📌 **Agregado a la cola:** {title}")

async def play_next(ctx):
    """Reproduce la siguiente canción en la cola"""
    global current_song
    if queue:
        url2, title = queue.pop(0)
        current_song = title

        source = discord.FFmpegPCMAudio(url2, options="-vn")
        player = discord.PCMVolumeTransformer(source, volume=0.5)  # Volumen al 50%

        ctx.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(ctx)))
        await ctx.send(f"🎵 **Reproduciendo ahora:** {title}")
    else:
        current_song = None

@bot.command()
async def skip(ctx):
    """Salta la canción actual"""
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ **Canción saltada!**")
    else:
        await ctx.send("❌ No hay música reproduciéndose.")

@bot.command()
async def stop(ctx):
    """Detiene la música y vacía la cola"""
    global current_song
    if ctx.voice_client:
        ctx.voice_client.stop()
        queue.clear()
        current_song = None
        await ctx.send("⏹️ **Música detenida y cola vaciada.**")
    else:
        await ctx.send("❌ No estoy en un canal de voz.")

@bot.command()
async def pause(ctx):
    """Pausa la reproducción actual"""
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ **Música pausada.**")
    else:
        await ctx.send("❌ No hay música reproduciéndose.")

@bot.command()
async def resume(ctx):
    """Reanuda la música pausada"""
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ **Música reanudada.**")
    else:
        await ctx.send("❌ No hay música pausada.")

@bot.command()
async def nowplaying(ctx):
    """Muestra la canción actual"""
    if ctx.voice_client.is_playing():
        await ctx.send(f"🎶 **Ahora suena:** {current_song if current_song else 'Desconocido'}")
    else:
        await ctx.send("❌ No hay música reproduciéndose.")

@bot.command()
async def queue_list(ctx):
    """Muestra la cola de reproducción"""
    if queue:
        queue_text = "\n".join([f"🎵 {i+1}. {song[1]}" for i, song in enumerate(queue)])
        await ctx.send(f"📜 **Cola de reproducción:**\n{queue_text}")
    else:
        await ctx.send("📭 **La cola está vacía.**")

@bot.command()
async def volume(ctx, volume: int):
    """Cambia el volumen del bot (1-100)"""
    if ctx.voice_client and ctx.voice_client.source:
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"🔊 **Volumen ajustado a {volume}%**")
    else:
        await ctx.send("❌ No hay música reproduciéndose.")

@bot.command(name="ayuda")
async def custom_help(ctx):
    """Lista los comandos disponibles"""
    embed = discord.Embed(title="🎵 Comandos de Música", color=discord.Color.blue())
    embed.add_field(name="🎶 `!play <URL o búsqueda>`", value="Reproduce una canción.", inline=False)
    embed.add_field(name="📌 `!queue_list`", value="Muestra la cola de canciones.", inline=False)
    embed.add_field(name="⏭️ `!skip`", value="Salta la canción actual.", inline=False)
    embed.add_field(name="⏹️ `!stop`", value="Detiene la música y vacía la cola.", inline=False)
    embed.add_field(name="⏸️ `!pause` / ▶️ `!resume`", value="Pausa y reanuda la música.", inline=False)
    embed.add_field(name="🔊 `!volume <1-100>`", value="Ajusta el volumen.", inline=False)
    embed.add_field(name="🎵 `!nowplaying`", value="Muestra la canción actual.", inline=False)
    embed.add_field(name="🔄 `!leave`", value="Desconecta el bot del canal de voz.", inline=False)
    await ctx.send(embed=embed)