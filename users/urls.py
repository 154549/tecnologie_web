from django.urls import path
from . import views

app_name = "users"

urlpatterns = [

    path("", views.home, name="home"),
    path("feed/", views.feed, name="feed"),

    path("login/", views.LoginUtenteView.as_view(), name="login"),
    path("logout/", views.LogoutUtenteView.as_view(), name="logout"),
    path("registrazione/", views.registrazione, name="registrazione"),

    path("profilo/<str:username>/", views.ProfiloDetailView.as_view(), name="profilo"),
    path("modificaprofilo/", views.modificaprofilo, name="modificaprofilo"),

    path("inviarichiesta/<str:username>/", views.inviarichiesta, name="inviarichiesta"),
    path("accettarichiesta/<pk>/", views.accettarichiesta, name="accettarichiesta"),
    path("rifiutarichiesta/<pk>/", views.rifiutarichiesta, name="rifiutarichiesta"),
    path("rimuoviamico/<str:username>/", views.rimuoviamico, name="rimuoviamico"),
    path("richieste/", views.ListaRichiesteView.as_view(), name="richieste"),
    path("listaamici/<str:username>/", views.ListaAmiciView.as_view(), name="listaamici"),

    path("creadjango/", views.creadjango, name="creadjango"),
    path("cancelladjango/<pk>/", views.CancellaDjangoView.as_view(), name="cancelladjango"),

    path("aggiungicommento/<pk>/", views.aggiungicommento, name="aggiungicommento"),
    path("cancellacommento/<pk>/", views.CancellaCommentoView.as_view(), name="cancellacommento"),

    path("togglelike/<pk>/", views.togglelike, name="togglelike"),

    path("cerca/", views.cerca, name="cerca"),
    path("cerca/<str:query>/", views.RisultatiRicercaView.as_view(), name="risultatiricerca"),

    path("gruppi/", views.ListaGruppiView.as_view(), name="listagruppi"),
    path("creagruppo/", views.creagruppo, name="creagruppo"),
    path("gruppo/<pk>/", views.DettaglioGruppoView.as_view(), name="dettagliogruppo"),
    path("iscrivigruppo/<pk>/", views.iscrivigruppo, name="iscrivigruppo"),
    path("abbandonagruppo/<pk>/", views.abbandonagruppo, name="abbandonagruppo"),
    path("invitagruppo/<pk>/<str:username>/", views.invitagruppo, name="invitagruppo"),
    path("accettainvitogruppo/<pk>/", views.accettainvitogruppo, name="accettainvitogruppo"),
    path("rifiutainvitogruppo/<pk>/", views.rifiutainvitogruppo, name="rifiutainvitogruppo"),
    path("creapostgruppo/<pk>/", views.creapostgruppo, name="creapostgruppo"),
    path("cancellapostgruppo/<pk>/", views.cancellapostgruppo, name="cancellapostgruppo"),
    path("togglelikegruppo/<pk>/", views.togglelikegruppo, name="togglelikegruppo"),
    path("aggiungicommentogruppo/<pk>/", views.aggiungicommentogruppo, name="aggiungicommentogruppo"),
    path("cancellacommentogruppo/<pk>/", views.CancellaCommentoGruppoView.as_view(), name="cancellacommentogruppo"),
    path("espellimembro/<pk>/<str:username>/", views.espellimembro, name="espellimembro"),
    path("cancellagruppo/<pk>/", views.CancellaGruppoView.as_view(), name="cancellagruppo"),
    path("modificaimmaginegruppo/<pk>/", views.modificaimmaginegruppo, name="modificaimmaginegruppo"),
    path("modificavisibilitagruppo/<pk>/", views.modificavisibilitagruppo, name="modificavisibilitagruppo"),

    path("segnalapost/<pk>/", views.segnalapost, name="segnalapost"),
    path("segnalacommento/<pk>/", views.segnalacommento, name="segnalacommento"),
    path("risolvisegnalazione/<pk>/", views.risolvisegnalazione, name="risolvisegnalazione"),
    path("ignorasegnalazione/<pk>/", views.ignorasegnalazione, name="ignorasegnalazione"),
    path("richiedimoderazione/", views.richiedimoderazione, name="richiedimoderazione"),

]
