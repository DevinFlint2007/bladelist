from datetime import datetime, timezone

from django.views import View
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.generic.list import ListView
from django.http import QueryDict, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, logout, authenticate

from utils.oauth import Oauth
from utils.hashing import Hasher
from utils.mixins import ResponseMixin
from utils.api_client import DiscordAPIClient
from utils.background import create_user, update_user
from .models import Bot, BotTag, Member, BotVote, BotReport, Server, ServerTag, ServerReport, ServerVote

popup_oauth = Oauth()
normal_oauth = Oauth(redirect_uri=settings.AUTH_HANDLER_URL)
hasher = Hasher()
discord_client = DiscordAPIClient()

# --- SAFE DATA FETCHING FUNCTIONS ---
def get_bot_tags():
    try:
        return BotTag.objects.all()
    except:
        return []

def get_server_tags():
    try:
        return ServerTag.objects.all()
    except:
        return []

def get_random_bots():
    try:
        return Bot.objects.filter(
            verified=True, banned=False, owner__banned=False
        ).order_by("date_added").distinct()[:8][::-1]
    except:
        return []

def get_random_servers():
    try:
        return Server.objects.filter(
            verified=True, banned=False, owner__banned=False
        ).order_by("date_added").distinct()[:8][::-1]
    except:
        return []

# --- VIEWS ---

def login_handler_view(request):
    return render(request, "login_handler.html", {"handler_url": settings.AUTH_HANDLER_URL})

def discord_login_normal(request):
    return redirect(normal_oauth.discord_login_url)

def logout_view(request):
    logout(request)
    return redirect('/')

def discord_login_view(request):
    return redirect(popup_oauth.discord_login_url)

def server_refresh(request):
    admin_guilds = [
        (guild.get("id"), guild.get("name")) for guild in request.user.member.refresh_admin_servers()
        if not Server.objects.filter(id=guild.get("id")).exists()
    ]
    request.user.member.sync_servers()
    return render(request, "refresh_pages/server_select.html", {"admin_guilds": admin_guilds})

def support_server_invite(request):
    return redirect(to="https://discord.gg/JKWhgPDnPp")

def bot_invite_counter(request, bot_id):
    try:
        bot = Bot.objects.
