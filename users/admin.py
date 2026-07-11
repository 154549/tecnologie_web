from django.contrib import admin
from .models import (
    Profilo, Interesse, DjangoPost, Commento, Like, RichiestaAmicizia, Djangroup,
    PostGruppo, Segnalazione, Moderatore, RichiestaModerazione,
    InvitoGruppo, CommentoGruppo, LikeGruppo,
)

# Register your models here.

# registrazioni "al volo", senza personalizzazioni: bastano per gestire i modelli dall'admin
admin.site.register(Profilo)
admin.site.register(Interesse)
admin.site.register(DjangoPost)
admin.site.register(Commento)
admin.site.register(Like)
admin.site.register(RichiestaAmicizia)
admin.site.register(Djangroup)
admin.site.register(PostGruppo)
admin.site.register(Segnalazione)
admin.site.register(InvitoGruppo)
admin.site.register(CommentoGruppo)
admin.site.register(LikeGruppo)


#admin.site.register(Moderatore)

# qui invece personalizziamo un po' le cose: Moderatore è un proxy di User,
# quindi nell'admin vogliamo vederci solo lo staff (e non i superuser)
class ModeratoreAdmin(admin.ModelAdmin):
    list_display = ("username", "first_name", "last_name", "email")  # colonne mostrate in lista
    search_fields = ("username", "first_name", "last_name")  # campi su cui funziona la ricerca

    def get_queryset(self, request):
        # filtriamo via i superuser, altrimenti spuntano anche loro tra i "moderatori"
        return super().get_queryset(request).filter(is_staff=True, is_superuser=False)


admin.site.register(Moderatore, ModeratoreAdmin)


# azione bulk dell'admin: prende tutte le richieste selezionate ancora in stato "inviata"
# e le accetta una per una, rendendo staff chi le ha mandate
def accetta_richieste(modeladmin, request, queryset):
    totale = queryset.count()
    for richiesta in queryset.filter(stato="inviata"):
        richiesta.stato = "accettata"
        richiesta.save()
        richiesta.richiedente.is_staff = True
        richiesta.richiedente.save()
        print("Richiesta di moderazione accettata per " + richiesta.richiedente.username)


# stessa idea ma per rifiutare, qui basta un update() in blocco senza girare oggetto per oggetto
def rifiuta_richieste(modeladmin, request, queryset):
    queryset.filter(stato="inviata").update(stato="rifiutata")


# short_description è quello che appare scritto nel menu a tendina delle azioni, in admin
accetta_richieste.short_description = "Accetta richieste selezionate"
rifiuta_richieste.short_description = "Rifiuta richieste selezionate"


class RichiestaModAdmin(admin.ModelAdmin):
    list_display = ("richiedente", "stato", "data_richiesta")
    list_filter = ("stato",)  # aggiunge il filtro laterale per stato
    actions = [accetta_richieste, rifiuta_richieste]  # collega le due azioni custom qui sopra

    def save_model(self, request, obj, form, change):
        # save_model scatta ogni volta che si salva la riga dall'admin (anche modificandola a mano)
        super().save_model(request, obj, form, change)
        # se qualcuno ha appena impostato "accettata" da qui, promuoviamo subito il richiedente
        if obj.stato == "accettata":
            obj.richiedente.is_staff = True
            obj.richiedente.save()
            print("Richiedente promosso a staff: " + obj.richiedente.username)


admin.site.register(RichiestaModerazione, RichiestaModAdmin)
