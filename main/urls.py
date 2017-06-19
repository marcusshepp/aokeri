from django.conf.urls import url

from main.views import (
    start,
    players_game_info,
    call,
    fold,
    bet,
    _raise
)

urlpatterns = [
    url(r'^start/$', start),
    url(r'^player_info/$', players_game_info),
    url(r'^call/$', call),
    url(r'^fold/$', fold),
    url(r'^bet/$', bet),
    url(r'^raise/$', _raise),
]
