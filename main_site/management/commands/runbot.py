import discord
from discord.ext import commands
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Runs the Discord bot'

    def handle(self, *args, **options):
        self.stdout.write("Starting Discord Bot...")

        # Setup intents (needed for modern Discord bots)
        intents = discord.Intents.default()
        intents.message_content = True 
        
        # Setup the bot (Logic from your index.py)
        bot = commands.Bot(command_prefix="!", intents=intents)

        @bot.event
        async def on_ready():
            print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')

        # This runs the bot using the TOKEN you put in Render's Environment tab
        try:
            bot.run(settings.DISCORD_API_TOKEN)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
