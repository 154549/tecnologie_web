from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

# tag di interesse, tipo #calcio o #musica: lo usiamo sia nei suggerimenti che nella ricerca
class Interesse(models.Model):
    nome = models.CharField(max_length=50, unique=True)  # unique così non ce ne sono due uguali

    def __str__(self):
        return f"#{self.nome}"

    class Meta:
        verbose_name_plural = "Interessi"


# dati extra di uno User: bio, amici, interessi, privacy... tutto ciò che il modello User di django non ha
class Profilo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profilo")  # se lo User sparisce, sparisce anche il profilo
    bio = models.TextField(max_length=500, blank=True, default="")
    data_nascita = models.DateField(null=True, blank=True)
    immagine_profilo = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    #telefono = models.CharField(max_length=20, blank=True)
    is_privato = models.BooleanField(default=False)
    # attenzione: è una relazione verso User (non verso Profilo), quindi non è simmetrica in automatico!
    # va aggiornata a mano da entrambe le parti quando qualcuno diventa amico di qualcun altro
    amici = models.ManyToManyField(User, blank=True, related_name="amici_di")
    interessi = models.ManyToManyField(Interesse, blank=True, related_name="profili")
    data_iscrizione = models.DateTimeField(auto_now_add=True)  # si riempie da sola alla creazione

    def eta(self):
        if not self.data_nascita:
            return None

        from datetime import date
        oggi = date.today()
        # se il compleanno di quest'anno non è ancora passato, togliamo un anno
        return oggi.year - self.data_nascita.year - ((oggi.month, oggi.day) < (self.data_nascita.month, self.data_nascita.day))

    def __str__(self):
        return f"ID: {self.pk}: {self.user.first_name} {self.user.last_name}"
        #return self.user.username

    def get_nome_completo(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def conta_amici(self):
        return self.amici.count()

    def conta_post(self):
        # nota: guardiamo i post dello User (djangos), non del Profilo, perché DjangoPost è legato a User
        return self.user.djangos.count()

    def is_amico_di(self, altro_user):
        if self.amici.filter(pk=altro_user.pk).exists():
            return True
        return False

    def is_visibile_da(self, utente):
        # pubblico: si vede sempre. privato: solo il proprietario o un suo amico
        if not self.is_privato:
            return True
        if utente == self.user:
            return True
        return self.is_amico_di(utente)

    class Meta:
        verbose_name_plural = "Profili"


# richiesta di amicizia, con uno stato che segue il percorso inviata -> accettata/rifiutata
class RichiestaAmicizia(models.Model):
    STATO_CHOICES = [
        ("inviata", "Inviata"),
        ("accettata", "Accettata"),
        ("rifiutata", "Rifiutata"),
    ]
    mittente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="richieste_inviate")
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="richieste_ricevute")
    stato = models.CharField(max_length=10, choices=STATO_CHOICES, default="inviata")
    data_invio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID: {self.pk}: {self.mittente.first_name} -> {self.destinatario.first_name} ({self.stato})"

    class Meta:
        verbose_name_plural = "Richieste Amicizia"
        # niente doppioni: la stessa coppia mittente/destinatario non può avere due richieste
        unique_together = ("mittente", "destinatario")


# un post pubblicato sulla propria bacheca
class DjangoPost(models.Model):
    autore = models.ForeignKey(User, on_delete=models.CASCADE, related_name="djangos")
    testo = models.TextField(max_length=2000, blank=True, default="")
    immagine = models.ImageField(upload_to="post_pics/", blank=True, null=True)
    data_pubblicazione = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID: {self.pk}: Django di {self.autore.first_name} - {self.testo[:50]}"

    def conta_likes(self):
        return self.likes.count()

    def conta_commenti(self):
        return self.commenti.count()

    def ha_like_di(self, user):
        return self.likes.filter(utente=user).exists()

    class Meta:
        verbose_name_plural = "Djangos"
        ordering = ["-data_pubblicazione"]  # più recenti prima, nel feed


class Commento(models.Model):
    autore = models.ForeignKey(User, on_delete=models.CASCADE, related_name="commenti")
    django_post = models.ForeignKey(DjangoPost, on_delete=models.CASCADE, related_name="commenti")
    testo = models.TextField(max_length=500)
    data_pubblicazione = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID: {self.pk}: Commento di {self.autore.first_name} su Django #{self.django_post.pk}"

    class Meta:
        verbose_name_plural = "Commenti"
        ordering = ["data_pubblicazione"]  # qui invece dal più vecchio, ordine di conversazione


class Like(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    django_post = models.ForeignKey(DjangoPost, on_delete=models.CASCADE, related_name="likes")
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID: {self.pk}: {self.utente.first_name} likes Django #{self.django_post.pk}"

    class Meta:
        verbose_name_plural = "Likes"
        unique_together = ("utente", "django_post")  # un solo like a testa per post


# un gruppo tematico, con creatore, admin e membri (l'admin è sempre anche membro)
class Djangroup(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descrizione = models.TextField(max_length=500, blank=True, default="")
    immagine = models.ImageField(upload_to="group_pics/", blank=True, default="defaultgroup.png")
    creatore = models.ForeignKey(User, on_delete=models.CASCADE, related_name="gruppi_creati")
    admin = models.ManyToManyField(User, blank=True, related_name="gruppi_admin")
    membri = models.ManyToManyField(User, blank=True, related_name="gruppi_membro")
    is_privato = models.BooleanField(default=False)
    interessi = models.ManyToManyField(Interesse, blank=True, related_name="gruppi")
    data_creazione = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID: {self.pk}: {self.nome}"

    def conta_membri(self):
        return self.membri.count()

    def conta_post(self):
        return self.post_gruppo.count()

    def is_membro(self, user):
        if self.membri.filter(pk=user.pk).exists():
            return True
        return False

    def is_admin(self, user):
        return self.admin.filter(pk=user.pk).exists()

    class Meta:
        verbose_name_plural = "Djangroups"
        ordering = ["-data_creazione"]


class InvitoGruppo(models.Model):
    STATO_CHOICES = [
        ("inviato", "Inviato"),
        ("accettato", "Accettato"),
        ("rifiutato", "Rifiutato"),
    ]
    gruppo = models.ForeignKey(Djangroup, on_delete=models.CASCADE, related_name="inviti")
    mittente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="inviti_gruppo_inviati")
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="inviti_gruppo_ricevuti")
    stato = models.CharField(max_length=10, choices=STATO_CHOICES, default="inviato")
    data_invio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID: {self.pk}: {self.gruppo.nome}: {self.mittente.first_name} -> {self.destinatario.first_name} ({self.stato})"

    class Meta:
        verbose_name_plural = "Inviti Gruppo"
        unique_together = ("gruppo", "destinatario")  # un solo invito attivo a testa, per gruppo
        ordering = ["-data_invio"]


# post dentro un gruppo, praticamente un DjangoPost ma legato a un Djangroup
class PostGruppo(models.Model):
    autore = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post_gruppi")
    gruppo = models.ForeignKey(Djangroup, on_delete=models.CASCADE, related_name="post_gruppo")
    testo = models.TextField(max_length=2000, blank=True, default="")
    immagine = models.ImageField(upload_to="group_post_pics/", blank=True, null=True)
    data_pubblicazione = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID: {self.pk}: Post di {self.autore.first_name} in {self.gruppo.nome}"

    def conta_likes(self):
        return self.likes.count()

    def conta_commenti(self):
        return self.commenti.count()

    def ha_like_di(self, user):
        return self.likes.filter(utente=user).exists()

    class Meta:
        verbose_name_plural = "Post Gruppo"
        ordering = ["-data_pubblicazione"]


class CommentoGruppo(models.Model):
    autore = models.ForeignKey(User, on_delete=models.CASCADE, related_name="commenti_gruppo")
    post_gruppo = models.ForeignKey(PostGruppo, on_delete=models.CASCADE, related_name="commenti")
    testo = models.TextField(max_length=500)
    data_pubblicazione = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID: {self.pk}: Commento di {self.autore.first_name} su Post Gruppo #{self.post_gruppo.pk}"

    class Meta:
        verbose_name_plural = "Commenti Gruppo"
        ordering = ["data_pubblicazione"]


class LikeGruppo(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes_gruppo")
    post_gruppo = models.ForeignKey(PostGruppo, on_delete=models.CASCADE, related_name="likes")
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID: {self.pk}: {self.utente.first_name} likes Post Gruppo #{self.post_gruppo.pk}"

    class Meta:
        verbose_name_plural = "Likes Gruppo"
        unique_together = ("utente", "post_gruppo")


# segnalazione di un post o di un commento (mai entrambi), gestita poi da staff/moderatori
class Segnalazione(models.Model):
    TIPO_CHOICES = [
        ("post", "Post"),
        ("commento", "Commento"),
    ]
    STATO_CHOICES = [
        ("aperta", "Aperta"),
        ("risolta", "Risolta"),
        ("ignorata", "Ignorata"),
    ]
    segnalatore = models.ForeignKey(User, on_delete=models.CASCADE, related_name="segnalazioni_fatte")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    motivo = models.TextField(max_length=500)
    stato = models.CharField(max_length=10, choices=STATO_CHOICES, default="aperta")
    # solo uno tra i due qui sotto è valorizzato, a seconda del campo "tipo"
    post_segnalato = models.ForeignKey(DjangoPost, on_delete=models.CASCADE, null=True, blank=True, related_name="segnalazioni")
    commento_segnalato = models.ForeignKey(Commento, on_delete=models.CASCADE, null=True, blank=True, related_name="segnalazioni")
    data_segnalazione = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID: {self.pk}: {self.tipo} segnalato da {self.segnalatore.first_name} ({self.stato})"

    class Meta:
        verbose_name_plural = "Segnalazioni"
        ordering = ["-data_segnalazione"]


# proxy model: non crea una tabella nuova, serve solo a mostrare nell'admin gli User con
# is_staff=True come se fossero un modello a parte, tipo "i moderatori"
class Moderatore(User):
    class Meta:
        proxy = True
        verbose_name = "Moderatore"
        verbose_name_plural = "Moderatori"


# richiesta di un utente per diventare moderatore (cioè ottenere is_staff), da approvare a mano
class RichiestaModerazione(models.Model):
    STATO_CHOICES = [
        ("inviata", "Inviata"),
        ("accettata", "Accettata"),
        ("rifiutata", "Rifiutata"),
    ]
    richiedente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="richieste_moderazione")
    stato = models.CharField(max_length=10, choices=STATO_CHOICES, default="inviata")
    data_richiesta = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID: {self.pk}: {self.richiedente.first_name} {self.richiedente.last_name} ({self.stato})"

    class Meta:
        verbose_name_plural = "Richieste Moderazione"
        ordering = ["-data_richiesta"]
