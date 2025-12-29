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
        bot = Bot.objects.get(id=bot_id)
        bot.meta.total_invites += 1
        bot.meta.save()
        return redirect(to=bot.invite_link)
    except Exception:
        return render(request, "404.html")

def server_invite_counter(request, server_id):
    try:
        server = Server.objects.get(id=server_id)
        server.meta.total_invites += 1
        server.meta.save()
        return redirect(to=server.invite_link)
    except Exception:
        return render(request, "404.html")

class BotView(View, ResponseMixin):
    template_name = "bot_page.html"
    model = Bot

    def get(self, request, bot_id):
        try:
            bot = self.model.objects.get(id=bot_id)
            if bot.banned or not bot.verified:
                if request.user.is_authenticated:
                    if request.user.member == bot.owner or request.user.is_staff:
                        return render(request, self.template_name, {"bot": bot})
                return render(request, "404.html")
            return render(
                request, self.template_name, {
                    "bot": bot,
                    "custom_og_image": bot.avatar_url,
                    "custom_og_title": bot.name,
                    "custom_og_desc": bot.short_desc
                }
            )
        except self.model.DoesNotExist:
            return render(request, "404.html")

    def put(self, request, bot_id):
        try:
            bot = self.model.objects.get(id=bot_id)
            if request.user.member == bot.owner or request.user.member in bot.admins.all():
                if not bot.banned:
                    if bot.rejected:
                        bot.verification_status = "UNVERIFIED"
                        bot.meta.moderator = None
                        bot.meta.save()
                        bot.save()
                        return self.json_response_200()
                    return self.json_response_503()
                return self.json_response_403()
            return self.json_response_401()
        except self.model.DoesNotExist:
            return self.json_response_404()

class LoginView(View):
    template_name = 'index.html'
    
    def get(self, request):
        code = request.GET.get('code')
        popup = request.GET.get('popup')
        oauth = popup_oauth if popup == "True" else normal_oauth
        
        if code is not None:
            token_json = oauth.get_token_json(code)
            user_json = oauth.get_user_json(token_json.get("access_token"))
            user_json["token_data"] = token_json
            user_id = user_json.get("id")
            user = authenticate(username=user_id, password=hasher.get_hashed_pass(user_id))
            
            if user is None:
                user = create_user(user_json)
            else:
                update_user(user, user_json)
                
            if not user.member.banned:
                login(request, user)
                return redirect("/")
            else:
                return render(request, self.template_name, {"banned": True, "search": True})
        
        return render(request, self.template_name, {"error": "Internal Server Error", "search": True})

class IndexView(View):
    template_name = "index.html"

    def get(self, request):
        recent_bots = Bot.objects.filter(verified=True, banned=False, owner__banned=False).order_by('-date_added')[:8]
        trending_bots = Bot.objects.filter(verified=True, banned=False, owner__banned=False).order_by('-votes')[:8]
        return render(request, self.template_name, {
            "search": True,
            "random_bots": get_random_bots(),
            "recent_bots": recent_bots,
            "trending_bots": trending_bots
        })

class TemplateView(View):
    template_name = "404.html"
    def get(self, request):
        return render(request, self.template_name)

class BotListView(ListView, ResponseMixin):
    template_name = "bot_list.html"
    model = Bot
    paginate_by = 40
    extra_context = {"search": True, "logo_off": True}

    def get_queryset(self):
        return self.model.objects.filter(verified=True, banned=False, owner__banned=False).order_by('-votes')

    def put(self, request):
        data = QueryDict(request.body)
        if not request.user.is_authenticated:
            return self.json_response_401()
            
        bot = Bot.objects.get(id=data.get("bot_id"))
        vote = BotVote.objects.filter(member=request.user.member, bot=bot).order_by("-creation_time").first()
        
        if vote is None or (datetime.now(timezone.utc) - vote.creation_time).total_seconds() >= 43200:
            if vote: vote.delete()
            BotVote.objects.create(
                member=request.user.member,
                bot=bot,
                creation_time=datetime.now(timezone.utc)
            )
            bot.votes += 1
            bot.save()
            discord_client.send_embed(bot.vote_embed(request.user.member))
            return JsonResponse({"vote_count": bot.votes})
        return self.json_response_403()

class BotAddView(LoginRequiredMixin, View):
    template_name = "bot_add.html"

    def get(self, request):
        return render(request, self.template_name, {"tags": get_bot_tags()})

    def post(self, request):
        data = request.POST
        bot_id = data.get("id")
        context = {"tags": get_bot_tags()}
        
        if int(bot_id) <= 9223372036854775807:
            if not Bot.objects.filter(id=bot_id).exists():
                resp = discord_client.get_bot_info(bot_id)
                if resp.status_code == 404:
                    context["error"] = "Bot account does not exists!"
                elif resp.status_code == 200:
                    resp_data = resp.json()
                    bot = Bot.objects.create(
                        id=bot_id,
                        name=resp_data.get("username"),
                        owner=request.user.member,
                        invite_link=data.get("invite"),
                        date_added=datetime.now(timezone.utc),
                        avatar=resp_data.get("avatar"),
                        short_desc=data.get("short_desc")
                    )
                    bot.tags.set(BotTag.objects.filter(name__in=data.getlist('tags')))
                    bot.meta.support_server = data.get("support_server")
                    bot.meta.prefix = data.get("prefix")
                    bot.meta.long_desc = data.get("long_desc")
                    bot.meta.save()
                    context["success"] = "Bot added successfully!"
                    context["member"] = request.user.member
                    return render(request, "profile_page.html", context)
            else:
                context["error"] = "Bot record Exists."
        return render(request, self.template_name, context)

# ... (rest of your views follow the same pattern) ...
# Ensure all references to RANDOM_BOTS or BOT_TAGS 
# now use get_random_bots() or get_bot_tags()
