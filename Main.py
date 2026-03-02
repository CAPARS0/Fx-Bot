import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os

# -----------------------------
# Cargar y guardar datos
# -----------------------------

def cargar_datos():
    if os.path.exists("actividad.json"):
        with open("actividad.json", "r") as f:
            return json.load(f)
    return {}

def guardar_datos():
    with open("actividad.json", "w") as f:
        json.dump(actividad, f, indent=4)

actividad = cargar_datos()

# Archivo donde guardamos el mensaje del top
TOP_MESSAGE_FILE = "top_message.json"

def guardar_top_message(message_id, channel_id):
    with open(TOP_MESSAGE_FILE, "w") as f:
        json.dump({"message_id": message_id, "channel_id": channel_id}, f)

def cargar_top_message():
    if os.path.exists(TOP_MESSAGE_FILE):
        with open(TOP_MESSAGE_FILE, "r") as f:
            return json.load(f)
    return None

# -----------------------------
# Configuración del bot
# -----------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# Evento: Bot listo
# -----------------------------

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

    if not actualizar_top.is_running():
        actualizar_top.start()

    try:
        synced = await bot.tree.sync()
        print(f"Slash commands sincronizados: {len(synced)}")
    except Exception as e:
        print("Error al sincronizar comandos:", e)

# -----------------------------
# Contador de mensajes + respuesta a menciones
# -----------------------------

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Respuesta cuando mencionan al bot
    if bot.user in message.mentions:
        await message.channel.send(f"{message.author.mention} NO tengo permitido hablar con Geis 😎")

    # Contador de mensajes
    user_id = str(message.author.id)
    actividad[user_id] = actividad.get(user_id, 0) + 1
    guardar_datos()

    await bot.process_commands(message)

# -----------------------------
# Comando /top normal
# -----------------------------

@bot.tree.command(name="top", description="Muestra el top de usuarios más activos")
async def top(interaction: discord.Interaction):

    if len(actividad) < 2:
        await interaction.response.send_message(
            "Aún no hay suficientes usuarios para generar un top (mínimo 2).",
            ephemeral=True
        )
        return

    top_users = sorted(
        actividad.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    embed = discord.Embed(
        title="🔥 Estos son los top fans y más activos de Discord 🔥",
        color=discord.Color.orange()
    )

    izquierda = ""
    derecha = ""

    for i, (user_id, mensajes) in enumerate(top_users, start=1):
        miembro = interaction.guild.get_member(int(user_id))
        nombre = miembro.display_name if miembro else "Usuario desconocido"
        linea = f"**{i}. {nombre}** — {mensajes} mensajes\n"

        if i <= 5:
            izquierda += linea
        else:
            derecha += linea

    embed.add_field(name="🏆 Top 1 - 5", value=izquierda or "Sin datos", inline=True)
    embed.add_field(name="🔥 Top 6 - 10", value=derecha or "Sin datos", inline=True)

    await interaction.response.send_message(embed=embed)

# -----------------------------
# Comando para publicar el TOP automático
# -----------------------------

@bot.tree.command(name="publicartop", description="Publica el TOP que se actualizará automáticamente cada día")
async def publicartop(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🔥 Estos son los top fans y más activos de Discord 🔥",
        description="Generando datos...",
        color=discord.Color.orange()
    )

    msg = await interaction.channel.send(embed=embed)

    guardar_top_message(msg.id, interaction.channel.id)

    await interaction.response.send_message(
        "El TOP ha sido publicado y se actualizará automáticamente cada día.",
        ephemeral=True
    )

# -----------------------------
# Tarea automática: actualizar TOP cada 24 horas
# -----------------------------

@tasks.loop(hours=24)
async def actualizar_top():
    datos = cargar_top_message()
    if not datos:
        return

    channel = bot.get_channel(datos["channel_id"])
    if not channel:
        return

    try:
        msg = await channel.fetch_message(datos["message_id"])
    except:
        return

    top_users = sorted(
        actividad.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    izquierda = ""
    derecha = ""

    for i, (user_id, mensajes) in enumerate(top_users, start=1):
        miembro = channel.guild.get_member(int(user_id))
        nombre = miembro.display_name if miembro else "Usuario desconocido"
        linea = f"**{i}. {nombre}** — {mensajes} mensajes\n"

        if i <= 5:
            izquierda += linea
        else:
            derecha += linea

    embed = discord.Embed(
        title="🔥 Estos son los top fans y más activos de Discord 🔥",
        color=discord.Color.orange()
    )

    embed.add_field(name="🏆 Top 1 - 5", value=izquierda or "Sin datos", inline=True)
    embed.add_field(name="🔥 Top 6 - 10", value=derecha or "Sin datos", inline=True)

    await msg.edit(embed=embed)

    await channel.send(
        "📊 **¡Actualización diaria del TOP de Discord!**\n"
        "🔥 Los usuarios más activos han cambiado… ¿Estás en la lista?\n"
        "💬 ¡Sigue participando para subir posiciones!"
    )

# -----------------------------
# Iniciar bot
# -----------------------------

if __name__ == "__main__":
    token = os.getenv("TOKEN")
    if token is None:
        print("ERROR: No se encontró la variable TOKEN en Render.")
    else:
        bot.run(token)