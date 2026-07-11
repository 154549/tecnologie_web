
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView
from django.views.generic.detail import DetailView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from .models import (
    Profilo, Interesse, DjangoPost, Commento, Like, RichiestaAmicizia,
    Djangroup, PostGruppo, Segnalazione, RichiestaModerazione,
    InvitoGruppo, CommentoGruppo, LikeGruppo,
)
from .forms import (
    RegistrazioneForm, ProfiloForm, ModificaProfiloForm, DjangoPostForm,
    CommentoForm, DjangroupForm, PostGruppoForm, SegnalazioneForm,
    CommentoGruppoForm,
)

# Create your views here.

# home pubblica: se sei già loggato ti manda dritto al feed, altrimenti
# ti mostra i 3 interessi più popolari tra i profili registrati
def home(request):
    if request.user.is_authenticated:
        return redirect("users:feed")

    top_interessi = Interesse.objects.annotate(
        num_profili=Count("profili")
    ).order_by("-num_profili")[:3]
    ctx = {"top_interessi": top_interessi}
    return render(request, template_name="users/home.html", context=ctx)


# bacheca principale: ultimi 50 post degli amici, form per pubblicare/commentare,
# e qualche suggerimento di persone/gruppi in base agli interessi in comune
@login_required
def feed(request):
    # se manca il profilo (vecchi account, o roba creata a mano) lo creiamo al volo
    if not hasattr(request.user, "profilo"):
        Profilo.objects.create(user=request.user, immagine_profilo="defaultpfp.jpg")

    profilo = request.user.profilo
    amici_ids = profilo.amici.values_list("pk", flat=True)  # solo gli id, ci basta per il filtro
    numero_amici = profilo.amici.count()

    djangos = DjangoPost.objects.filter(
        autore__in=amici_ids
    ).order_by("-data_pubblicazione")[:50]

    form_django = DjangoPostForm()
    form_commento = CommentoForm()

    miei_interessi = profilo.interessi.all()
    utenti_suggeriti = []
    gruppi_suggeriti = []

    # senza interessi impostati non abbiamo niente su cui basare i suggerimenti
    if miei_interessi.exists():
        utenti_suggeriti = Profilo.objects.filter(
            interessi__in=miei_interessi
        ).exclude(user=request.user).exclude(
            user__in=profilo.amici.all()
        ).distinct()[:5]  # distinct evita doppioni se uno ha più interessi in comune

        gruppi_suggeriti = Djangroup.objects.filter(
            interessi__in=miei_interessi
        ).exclude(membri=request.user).distinct()[:5]

    liked_ids = list(Like.objects.filter(utente=request.user).values_list("django_post__pk", flat=True))

    ctx = {
        "djangos": djangos,
        "form_django": form_django,
        "form_commento": form_commento,
        "utenti_suggeriti": utenti_suggeriti,
        "gruppi_suggeriti": gruppi_suggeriti,
        "liked_ids": liked_ids,
    }
    print(ctx.keys())
    return render(request, template_name="users/feed.html", context=ctx)


# login standard di django, solo con un template nostro e redirect fisso al feed
class LoginUtenteView(LoginView):
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("users:feed")


class LogoutUtenteView(LogoutView):
    next_page = reverse_lazy("users:login")


# registrazione: in GET mostra i due form vuoti (utente + profilo), in POST li valida
# insieme e salva tutto, con un'immagine di default se non ne è stata caricata una
def registrazione(request):
    if request.method == "GET":
        form_user = RegistrazioneForm()
        form_profilo = ProfiloForm()
        return render(request, template_name="users/registrazione.html",
                      context={"form_user": form_user, "form_profilo": form_profilo})
    else:
        form_user = RegistrazioneForm(request.POST)
        form_profilo = ProfiloForm(request.POST, request.FILES)

        if form_user.is_valid() and form_profilo.is_valid():
            # commit=False: crea l'oggetto in memoria senza salvarlo subito, così possiamo
            # ancora ritoccarlo (qui capitalizziamo nome e cognome)
            user = form_user.save(commit=False)
            user.first_name = user.first_name.capitalize()
            user.last_name = user.last_name.capitalize()
            user.save()
            profilo = form_profilo.save(commit=False)
            profilo.user = user
            if not profilo.immagine_profilo:
                profilo.immagine_profilo = "defaultpfp.jpg"
            profilo.save()
            # i campi many-to-many (gli interessi) si salvano solo dopo, quando l'oggetto ha già un id
            form_profilo.save_m2m()
            messages.success(request, 'Registrazione completata! Effettua il login.')
            print("Nuovo utente registrato: " + user.username)
            return redirect("users:login")
        else:
            return render(request, template_name="users/registrazione.html",
                          context={"form_user": form_user, "form_profilo": form_profilo})


# pagina profilo, cercata per username: calcola se chi guarda è amico o proprietario,
# lo stato delle richieste di amicizia e, se sei staff, anche le segnalazioni aperte
class ProfiloDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "users/profilo.html"
    slug_field = "username"  # riusiamo il meccanismo dello slug per cercare per username invece che per pk
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        utente_vis = self.get_object()
        io = self.request.user

        # profilo mancante? lo creiamo per entrambi, sia chi guarda che chi viene visitato
        if not hasattr(io, "profilo"):
            Profilo.objects.create(user=io, immagine_profilo="defaultpfp.jpg")
        if not hasattr(utente_vis, "profilo"):
            Profilo.objects.create(user=utente_vis, immagine_profilo="defaultpfp.jpg")

        profilo = utente_vis.profilo
        ctx["profilo"] = profilo
        ctx["is_owner"] = (io == utente_vis)
        ctx["is_amico"] = io.profilo.is_amico_di(utente_vis)
        numero_richieste = RichiestaAmicizia.objects.filter(destinatario=io).count()

        ctx["richiesta_inviata"] = RichiestaAmicizia.objects.filter(
            mittente=io, destinatario=utente_vis, stato="inviata").exists()
        ctx["richiesta_ricevuta"] = RichiestaAmicizia.objects.filter(
            mittente=utente_vis, destinatario=io, stato="inviata").exists()

        puo_vedere = profilo.is_visibile_da(io)
        ctx["puo_vedere"] = puo_vedere

        if puo_vedere:
            ctx["djangos"] = utente_vis.djangos.all()
            ctx["form_django"] = DjangoPostForm()
            ctx["form_commento"] = CommentoForm()
            ctx["liked_ids"] = list(Like.objects.filter(utente=io).values_list("django_post__pk", flat=True))

        # questa parte la vede solo il proprietario: segnalazioni se è staff, altrimenti
        # gli facciamo sapere se ha già chiesto di diventare moderatore
        if ctx["is_owner"]:
            if io.is_staff:
                ctx["segnalazioni"] = Segnalazione.objects.filter(stato="aperta")
            else:
                ctx["richiesta_mod_inviata"] = RichiestaModerazione.objects.filter(
                    richiedente=io, stato="inviata").exists()

        return ctx


# modifica profilo dell'utente loggato: aggiorna sia i campi di User (nome, cognome, email)
# che quelli del Profilo, tutto insieme
@login_required
def modificaprofilo(request):
    profilo = request.user.profilo
    if request.method == "GET":
        form = ModificaProfiloForm(instance=profilo, initial={
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
        })
        return render(request, template_name="users/modificaprofilo.html",
                      context={"form": form})
    else:
        form = ModificaProfiloForm(request.POST, request.FILES, instance=profilo)
        if form.is_valid():
            request.user.first_name = form.cleaned_data["first_name"].capitalize()
            request.user.last_name = form.cleaned_data["last_name"].capitalize()
            request.user.email = form.cleaned_data["email"]
            request.user.save()
            profilo_salvato = form.save(commit=False)
            if not profilo_salvato.immagine_profilo:
                profilo_salvato.immagine_profilo = "defaultpfp.jpg"
            profilo_salvato.save()
            form.save_m2m()
            messages.success(request, "Profilo aggiornato!")
            return redirect("users:profilo", username=request.user.username)
        else:
            return render(request, template_name="users/modificaprofilo.html",
                          context={"form": form})


# invia una richiesta di amicizia, oppure la rimanda se era stata rifiutata; se c'è
# già una richiesta in corso o accettata, non facciamo nulla
@login_required
def inviarichiesta(request, username):
    if request.method == "POST":
        destinatario = get_object_or_404(User, username=username)
        if not hasattr(request.user, "profilo"):
            Profilo.objects.create(user=request.user, immagine_profilo="defaultpfp.jpg")
        if not hasattr(destinatario, "profilo"):
            Profilo.objects.create(user=destinatario, immagine_profilo="defaultpfp.jpg")

        if destinatario != request.user:  # niente richieste a se stessi
            richiesta_esistente = RichiestaAmicizia.objects.filter(
                mittente=request.user, destinatario=destinatario).first()

            if richiesta_esistente is None:
                # creiamo l'oggetto a mano perché i dati vengono dall'url, non da un form
                r = RichiestaAmicizia()
                r.mittente = request.user
                r.destinatario = destinatario
                r.save()
                messages.success(request, "Richiesta di amicizia inviata!")
            elif richiesta_esistente.stato == "rifiutata":
                # una rifiutata in passato si può rimandare
                richiesta_esistente.stato = "inviata"
                richiesta_esistente.save()
                messages.success(request, "Richiesta di amicizia inviata!")
            else:
                messages.error(request, "Richiesta già inviata!")

    return redirect("users:profilo", username=username)


@login_required
def accettarichiesta(request, pk):
    richiesta = get_object_or_404(RichiestaAmicizia, pk=pk, destinatario=request.user)
    richiesta.stato = "accettata"
    richiesta.save()
    # il campo amici non è simmetrico da solo: va aggiunto il collegamento da entrambe le parti!
    request.user.profilo.amici.add(richiesta.mittente)
    richiesta.mittente.profilo.amici.add(request.user)
    messages.success(request, "Richiesta accettata! Ora siete amici.")
    print("Nuova amicizia: " + str(request.user) + " e " + str(richiesta.mittente))
    return redirect("users:richieste")


@login_required
def rifiutarichiesta(request, pk):
    richiesta = get_object_or_404(RichiestaAmicizia, pk=pk, destinatario=request.user)
    richiesta.stato = "rifiutata"
    richiesta.save()
    messages.success(request, "Richiesta rifiutata.")
    return redirect("users:richieste")


@login_required
def rimuoviamico(request, username):
    a = get_object_or_404(User, username=username)
    request.user.profilo.amici.remove(a)
    a.profilo.amici.remove(request.user)  # anche qui, rimuoviamo da entrambe le parti
    messages.success(request, "Amicizia rimossa.")
    return redirect("users:profilo", username=username)


# richieste di amicizia in attesa + inviti gruppo ancora da accettare/rifiutare
class ListaRichiesteView(LoginRequiredMixin, ListView):
    model = RichiestaAmicizia
    template_name = "users/richieste.html"

    def get_queryset(self):
        return RichiestaAmicizia.objects.filter(
            destinatario=self.request.user, stato="inviata")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["inviti_gruppo"] = InvitoGruppo.objects.filter(
            destinatario=self.request.user, stato="inviato")
        return ctx


class ListaAmiciView(LoginRequiredMixin, ListView):
    model = User
    template_name = "users/listaamici.html"

    def get_queryset(self):
        # gli amici dell'utente nell'url, non di chi sta guardando la pagina
        utente = get_object_or_404(User, username=self.kwargs["username"])
        return utente.profilo.amici.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["utente_profilo"] = get_object_or_404(User, username=self.kwargs["username"])
        return ctx


@login_required
def creadjango(request):
    if request.method == "POST":
        form = DjangoPostForm(request.POST, request.FILES)
        if form.is_valid():
            dj = form.save(commit=False)
            dj.autore = request.user
            dj.save()
            messages.success(request, "Django pubblicato!")
            print("Django pubblicato da " + str(request.user))
        else:
            messages.error(request, "Errore nella pubblicazione del Django.")
            print("Errore nella pubblicazione del Django")

    # "next" è un campo nascosto nel template con l'url di partenza, serve per tornare lì
    next_url = request.POST.get("next", reverse("users:feed"))
    return redirect(next_url)


# base per tutte le cancellazioni: filtra il queryset sull'utente loggato tramite owner_field
# (così ognuno può cancellare solo la propria roba) e mostra il messaggio prima di reindirizzare
class CancellaBaseView(LoginRequiredMixin, DeleteView):
    owner_field = "autore"  # per i gruppi diventa "creatore", vedi sotto
    success_message = "Eliminato!"

    def get_queryset(self):
        # **{...} costruisce un argomento con nome variabile: equivale a filter(autore=...)
        # oppure filter(creatore=...), a seconda di owner_field
        return self.model.objects.filter(**{self.owner_field: self.request.user})

    def get_success_url(self):
        messages.success(self.request, self.success_message)
        return self.get_redirect_url()


class CancellaDjangoView(CancellaBaseView):
    model = DjangoPost
    template_name = "users/cancelladjango.html"
    success_message = "Django eliminato!"

    def get_redirect_url(self):
        return reverse("users:profilo", kwargs={"username": self.request.user.username})


# usata da commenti, like e segnalazioni: un post è visibile se il profilo dell'autore
# non è privato, oppure se chi guarda è suo amico
def _django_post_visibile(request_user, django_post):
    autore_profilo = getattr(django_post.autore, "profilo", None)  # niente errore se il profilo manca
    return autore_profilo is None or autore_profilo.is_visibile_da(request_user)


# vecchia versione, tenuta qui per ora
def _post_visibile_old(request_user, django_post):
    if django_post.autore.profilo.is_privato:
        return django_post.autore == request_user
    return True


@login_required
def aggiungicommento(request, pk):
    django_post = get_object_or_404(DjangoPost, pk=pk)
    if request.method == "POST":
        if not _django_post_visibile(request.user, django_post):
            messages.error(request, "Non puoi commentare il post di un profilo privato.")
            return redirect(request.POST.get("next", reverse("users:feed")))
        form = CommentoForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.autore = request.user
            c.django_post = django_post
            c.save()
            messages.success(request, "Commento aggiunto!")
        else:
            messages.error(request, "Errore nell'invio del commento.")
    next_url = request.POST.get("next", reverse("users:feed"))
    return redirect(next_url)


class CancellaCommentoView(CancellaBaseView):
    model = Commento
    template_name = "users/cancellacommento.html"
    success_message = "Commento eliminato!"

    def get_redirect_url(self):
        return self.request.GET.get("next", reverse("users:feed"))


@login_required
def togglelike(request, pk):
    django_post = get_object_or_404(DjangoPost, pk=pk)
    if not _django_post_visibile(request.user, django_post):
        messages.error(request, "Non puoi mettere like al post di un profilo privato.")
        return redirect(request.GET.get("next", reverse("users:feed")))

    like_es = Like.objects.filter(utente=request.user, django_post=django_post)
    if like_es.exists() == True:
        # c'è già? lo togliamo
        like_es.delete()
        print("Like rimosso da " + str(request.user))
    else:
        # non c'è? lo creiamo a mano, non serve un form per un semplice like
        l = Like()
        l.utente = request.user
        l.django_post = django_post
        l.save()
        print("Like aggiunto da " + str(request.user))

    next_url = request.GET.get("next", reverse("users:feed"))
    return redirect(next_url)


# in GET mostra il form di ricerca, in POST prende la stringa e reindirizza ai risultati;
# se è vuota usiamo "null" come segnale nell'url
@login_required
def cerca(request):
    if request.method == "GET":
        return render(request, template_name="users/cerca.html")
        #return render(request, template_name="users/cerca_ajax.html")
    else:
        query = request.POST.get("query", "").strip()
        if len(query) < 1:
            query = "null"
        return redirect("users:risultatiricerca", query=query)


class RisultatiRicercaView(LoginRequiredMixin, ListView):
    model = User
    template_name = "users/risultatiricerca.html"

    def get_queryset(self):
        query = self.kwargs.get("query", "")
        if query == "null":
            return User.objects.none()
        return User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(profilo__interessi__nome__icontains=query)
        ).distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.kwargs.get("query", "")
        query = self.kwargs.get("query", "")
        if query != "null":
            ctx["gruppi"] = Djangroup.objects.filter(
                Q(nome__icontains=query) |
                Q(interessi__nome__icontains=query)
            ).distinct()
        return ctx


class ListaGruppiView(LoginRequiredMixin, ListView):
    model = Djangroup
    template_name = "users/listagruppi.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["miei_gruppi"] = Djangroup.objects.filter(membri=self.request.user)
        ctx["altri_gruppi"] = Djangroup.objects.filter(
            is_privato=False
        ).exclude(membri=self.request.user)
        return ctx


@login_required
def creagruppo(request):
    if request.method == "GET":
        form = DjangroupForm()
        return render(request, template_name="users/creagruppo.html", context={"form": form})
    else:
        form = DjangroupForm(request.POST, request.FILES)
        if form.is_valid():
            gruppo = form.save(commit=False)
            gruppo.creatore = request.user
            gruppo.save()
            form.save_m2m()
            # il creatore è subito sia admin che membro del suo stesso gruppo
            gruppo.admin.add(request.user)
            gruppo.membri.add(request.user)
            messages.success(request, "Gruppo creato!")
            print("Gruppo creato: " + gruppo.nome)
            return redirect("users:dettagliogruppo", pk=gruppo.pk)
        else:
            return render(request, template_name="users/creagruppo.html", context={"form": form})


# pagina di un gruppo: calcola il ruolo dell'utente (membro/admin/creatore), mostra i post
# solo se il gruppo è visibile, e per gli admin anche inviti pendenti e amici invitabili
class DettaglioGruppoView(LoginRequiredMixin, DetailView):
    model = Djangroup
    template_name = "users/dettagliogruppo.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        gruppo = self.get_object()
        io = self.request.user

        ctx["is_membro"] = gruppo.is_membro(io)
        ctx["is_admin"] = gruppo.is_admin(io)
        ctx["is_creatore"] = (gruppo.creatore == io)

        if ctx["is_membro"] or not gruppo.is_privato:
            ctx["post_gruppo"] = gruppo.post_gruppo.all()
            ctx["form_post"] = PostGruppoForm()
            ctx["form_commento_gruppo"] = CommentoGruppoForm()
            ctx["liked_ids_gruppo"] = list(
                LikeGruppo.objects.filter(utente=io).values_list("post_gruppo__pk", flat=True))

        if not ctx["is_membro"]:
            ctx["invito_ricevuto"] = InvitoGruppo.objects.filter(
                gruppo=gruppo, destinatario=io, stato="inviato").first()

        if ctx["is_admin"]:
            inviti_pendenti = InvitoGruppo.objects.filter(gruppo=gruppo, stato="inviato")
            ctx["invitati_pk"] = set(inviti_pendenti.values_list("destinatario_id", flat=True))
            ctx["amici_invitabili"] = io.profilo.amici.exclude(
                pk__in=gruppo.membri.values_list("pk", flat=True))

        return ctx


@login_required
def iscrivigruppo(request, pk):
    gruppo = get_object_or_404(Djangroup, pk=pk)
    if not gruppo.is_privato:
        gruppo.membri.add(request.user)
        messages.success(request, "Ti sei iscritto al gruppo!")
    else:
        messages.error(request, "Questo gruppo è privato.")
    return redirect("users:dettagliogruppo", pk=pk)


@login_required
def abbandonagruppo(request, pk):
    gruppo = get_object_or_404(Djangroup, pk=pk)
    if request.user != gruppo.creatore:
        gruppo.membri.remove(request.user)
        gruppo.admin.remove(request.user)
        messages.success(request, "Hai abbandonato il gruppo.")
    else:
        messages.error(request, "Il creatore non può abbandonare il gruppo.")
    return redirect("users:listagruppi")


@login_required
def invitagruppo(request, pk, username):
    gruppo = get_object_or_404(Djangroup, pk=pk)
    destinatario = get_object_or_404(User, username=username)

    if request.method == "POST" and gruppo.is_admin(request.user):
        if gruppo.is_membro(destinatario):
            messages.error(request, "L'utente è già membro del gruppo.")
        else:
            invito_esistente = InvitoGruppo.objects.filter(
                gruppo=gruppo, destinatario=destinatario).first()

            # stesso schema delle richieste di amicizia: niente invito, uno rifiutato
            # da rimandare, oppure uno già attivo su cui non facciamo nulla
            if invito_esistente is None:
                i = InvitoGruppo()
                i.gruppo = gruppo
                i.mittente = request.user
                i.destinatario = destinatario
                i.save()
                messages.success(request, "Invito inviato!")
                print("Invito gruppo inviato a " + destinatario.username)
            elif invito_esistente.stato == "rifiutato":
                invito_esistente.stato = "inviato"
                invito_esistente.mittente = request.user
                invito_esistente.save()
                messages.success(request, "Invito inviato!")
            else:
                messages.error(request, "Invito già inviato.")

    return redirect("users:dettagliogruppo", pk=pk)


@login_required
def accettainvitogruppo(request, pk):
    invito = get_object_or_404(InvitoGruppo, pk=pk, destinatario=request.user)
    invito.stato = "accettato"
    invito.save()
    invito.gruppo.membri.add(request.user)
    messages.success(request, "Sei entrato nel gruppo!")
    return redirect("users:dettagliogruppo", pk=invito.gruppo.pk)


@login_required
def rifiutainvitogruppo(request, pk):
    invito = get_object_or_404(InvitoGruppo, pk=pk, destinatario=request.user)
    invito.stato = "rifiutato"
    invito.save()
    messages.success(request, "Invito rifiutato.")
    return redirect("users:richieste")


@login_required
def creapostgruppo(request, pk):
    gruppo = get_object_or_404(Djangroup, pk=pk)
    if request.method == "POST" and gruppo.is_membro(request.user):
        form = PostGruppoForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.autore = request.user
            post.gruppo = gruppo
            post.save()
            messages.success(request, "Post pubblicato nel gruppo!")
        else:
            messages.error(request, "Errore nella pubblicazione del post.")
    return redirect("users:dettagliogruppo", pk=pk)


@login_required
def cancellapostgruppo(request, pk):
    post = get_object_or_404(PostGruppo, pk=pk)
    gruppo = post.gruppo
    if request.user == post.autore or gruppo.is_admin(request.user):
        post.delete()
        messages.success(request, "Post del gruppo eliminato.")
    return redirect("users:dettagliogruppo", pk=gruppo.pk)


@login_required
def togglelikegruppo(request, pk):
    post = get_object_or_404(PostGruppo, pk=pk)
    if not post.gruppo.is_membro(request.user):
        messages.error(request, "Solo gli iscritti al gruppo possono mettere like.")
        return redirect("users:dettagliogruppo", pk=post.gruppo.pk)

    like_es = LikeGruppo.objects.filter(utente=request.user, post_gruppo=post)
    if like_es.exists():
        like_es.delete()
    else:
        l = LikeGruppo()
        l.utente = request.user
        l.post_gruppo = post
        l.save()
    return redirect("users:dettagliogruppo", pk=post.gruppo.pk)


@login_required
def aggiungicommentogruppo(request, pk):
    post = get_object_or_404(PostGruppo, pk=pk)
    if request.method == "POST" and post.gruppo.is_membro(request.user):
        form = CommentoGruppoForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.autore = request.user
            c.post_gruppo = post
            c.save()
            messages.success(request, "Commento aggiunto!")
        else:
            messages.error(request, "Errore nell'invio del commento.")
    return redirect("users:dettagliogruppo", pk=post.gruppo.pk)


class CancellaCommentoGruppoView(CancellaBaseView):
    model = CommentoGruppo
    template_name = "users/cancellacommentogruppo.html"
    success_message = "Commento eliminato!"

    def get_redirect_url(self):
        # self.object non lo settiamo noi: DeleteView lo mette lì da sola prima di chiamare questo metodo
        return reverse("users:dettagliogruppo", kwargs={"pk": self.object.post_gruppo.gruppo.pk})


@login_required
def espellimembro(request, pk, username):
    gruppo = get_object_or_404(Djangroup, pk=pk)
    utente = get_object_or_404(User, username=username)
    if gruppo.is_admin(request.user) and utente != gruppo.creatore:
        gruppo.membri.remove(utente)
        gruppo.admin.remove(utente)
        messages.success(request, "Membro espulso dal gruppo.")
    return redirect("users:dettagliogruppo", pk=pk)


class CancellaGruppoView(CancellaBaseView):
    model = Djangroup
    template_name = "users/cancellagruppo.html"
    owner_field = "creatore"
    success_message = "Gruppo eliminato!"

    def get_redirect_url(self):
        return reverse("users:listagruppi")


@login_required
def modificaimmaginegruppo(request, pk):
    gruppo = get_object_or_404(Djangroup, pk=pk)
    if request.user != gruppo.creatore:
        return redirect("users:dettagliogruppo", pk=pk)
    if request.method == "POST" and request.FILES.get("immagine"):
        gruppo.immagine = request.FILES["immagine"]
        gruppo.save()
        messages.success(request, "Immagine del gruppo aggiornata!")
    return redirect("users:dettagliogruppo", pk=pk)


@login_required
def modificavisibilitagruppo(request, pk):
    gruppo = get_object_or_404(Djangroup, pk=pk)
    if request.method == "POST" and gruppo.is_admin(request.user):
        gruppo.is_privato = not gruppo.is_privato
        gruppo.save()
        stato = "privato" if gruppo.is_privato else "pubblico"
        messages.success(request, f"Il gruppo ora è {stato}.")
    return redirect("users:dettagliogruppo", pk=pk)


@login_required
def segnalapost(request, pk):
    post = get_object_or_404(DjangoPost, pk=pk)
    if not _django_post_visibile(request.user, post):
        messages.error(request, "Non puoi segnalare il post di un profilo privato.")
        return redirect("users:feed")
    if request.method == "GET":
        form = SegnalazioneForm()
        ctx = {"form": form, "oggetto": post, "tipo": "post"}
        return render(request, template_name="users/segnala.html", context=ctx)
    else:
        form = SegnalazioneForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.segnalatore = request.user
            s.tipo = "post"
            s.post_segnalato = post
            s.save()
            messages.success(request, "Segnalazione inviata!")
            return redirect("users:feed")
        ctx = {"form": form, "oggetto": post, "tipo": "post"}
        return render(request, template_name="users/segnala.html", context=ctx)


@login_required
def segnalacommento(request, pk):
    commento = get_object_or_404(Commento, pk=pk)
    if not _django_post_visibile(request.user, commento.django_post):
        messages.error(request, "Non puoi segnalare il commento di un profilo privato.")
        return redirect("users:feed")
    if request.method == "GET":
        form = SegnalazioneForm()
        ctx = {"form": form, "oggetto": commento, "tipo": "commento"}
        return render(request, template_name="users/segnala.html", context=ctx)
    else:
        form = SegnalazioneForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.segnalatore = request.user
            s.tipo = "commento"
            s.commento_segnalato = commento
            s.save()
            messages.success(request, "Segnalazione inviata!")
            return redirect("users:feed")
        ctx = {"form": form, "oggetto": commento, "tipo": "commento"}
        return render(request, template_name="users/segnala.html", context=ctx)


# solo per lo staff: risolve una segnalazione cancellando il contenuto segnalato
# (post o commento, a seconda di quale sia impostato)
@login_required
def risolvisegnalazione(request, pk):
    if not request.user.is_staff:
        return redirect("users:feed")
    segnalazione = get_object_or_404(Segnalazione, pk=pk)
    if segnalazione.post_segnalato:
        segnalazione.post_segnalato.delete()
        segnalazione.post_segnalato = None
    elif segnalazione.commento_segnalato:
        segnalazione.commento_segnalato.delete()
        segnalazione.commento_segnalato = None
    segnalazione.stato = "risolta"
    segnalazione.save()
    messages.success(request, "Segnalazione risolta, contenuto rimosso.")
    print("Segnalazione #" + str(segnalazione.pk) + " risolta da " + str(request.user))
    return redirect("users:profilo", username=request.user.username)


@login_required
def ignorasegnalazione(request, pk):
    if not request.user.is_staff:
        return redirect("users:feed")
    segnalazione = get_object_or_404(Segnalazione, pk=pk)
    segnalazione.stato = "ignorata"
    segnalazione.save()
    messages.success(request, "Segnalazione ignorata.")
    return redirect("users:profilo", username=request.user.username)


# un utente non staff chiede di diventare moderatore, se non ha già una richiesta in attesa
@login_required
def richiedimoderazione(request):
    if request.method == "POST" and not request.user.is_staff:
        esistente = RichiestaModerazione.objects.filter(
            richiedente=request.user, stato="inviata").exists()
        if not esistente:
            r = RichiestaModerazione()
            r.richiedente = request.user
            r.save()
            messages.success(request, "Richiesta di moderazione inviata!")
        else:
            messages.error(request, "Hai già una richiesta in attesa.")
    return redirect("users:profilo", username=request.user.username)
