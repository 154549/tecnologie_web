from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Interesse, Profilo, DjangoPost, Commento, Djangroup, PostGruppo, Segnalazione, CommentoGruppo


# form di registrazione: parte da quello già pronto di django (UserCreationForm, con username
# e le due password) e ci aggiungiamo nome, cognome ed email che di base non ci sono
class RegistrazioneForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, label="Nome")
    last_name = forms.CharField(max_length=50, required=True, label="Cognome")
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]


# form per compilare il Profilo in fase di registrazione
class ProfiloForm(forms.ModelForm):
    # niente tendina: usiamo le checkbox, molto più comode quando gli interessi sono pochi
    interessi = forms.ModelMultipleChoiceField(
        queryset=Interesse.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Interessi (max 3)"
    )

    class Meta:
        model = Profilo
        fields = ["bio", "data_nascita", "immagine_profilo", "is_privato", "interessi"]
        widgets = {"data_nascita": forms.DateInput(attrs={"type": "date"})}  # altrimenti sarebbe un campo di testo qualsiasi

    def clean_interessi(self):
        # il limite di 3 interessi non è esprimibile con le opzioni standard del campo, quindi lo controlliamo a mano
        interessi = self.cleaned_data.get("interessi")
        if interessi and interessi.count() > 3:
            raise forms.ValidationError("Puoi selezionare al massimo 3 interessi.")

        return interessi


# uguale a ProfiloForm ma per modificare un profilo già esistente, con in più i campi di User
class ModificaProfiloForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True, label="Nome")
    last_name = forms.CharField(max_length=50, required=True, label="Cognome")
    email = forms.EmailField(required=True, label="Email")
    interessi = forms.ModelMultipleChoiceField(
        queryset=Interesse.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Interessi (max 3)"
    )

    class Meta:
        model = Profilo
        fields = ["bio", "data_nascita", "immagine_profilo", "is_privato", "interessi"]
        widgets = {"data_nascita": forms.DateInput(attrs={"type": "date"})}

    def clean_interessi(self):
        # stessa regola di ProfiloForm: massimo 3
        interessi = self.cleaned_data.get("interessi")
        if interessi and interessi.count() > 3:
            raise forms.ValidationError("Puoi selezionare al massimo 3 interessi.")

        return interessi


# form per pubblicare un DjangoPost, serve almeno un testo o un'immagine (mai entrambi vuoti)
class DjangoPostForm(forms.ModelForm):
    testo = forms.CharField(max_length=2000, required=False, widget=forms.Textarea)  # required=False: il controllo vero è sotto, in clean()

    class Meta:
        model = DjangoPost
        fields = ["testo", "immagine"]

    def clean(self):
        # clean() (senza suffisso) serve quando la validazione coinvolge più campi insieme
        cleaned = super().clean()
        if not cleaned.get("testo") and not self.files.get("immagine"):
            raise forms.ValidationError("Devi inserire almeno un testo o un'immagine.")

        return cleaned


class CommentoForm(forms.ModelForm):
    class Meta:
        model = Commento
        fields = ["testo"]


# form per creare un Djangroup, stesso limite di 3 interessi visto sopra
class DjangroupForm(forms.ModelForm):
    interessi = forms.ModelMultipleChoiceField(
        queryset=Interesse.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Interessi del gruppo (max 3)"
    )

    class Meta:
        model = Djangroup
        fields = ["nome", "descrizione", "immagine", "is_privato", "interessi"]

    def clean_interessi(self):
        interessi = self.cleaned_data.get("interessi")
        if interessi and interessi.count() > 3:
            raise forms.ValidationError("Puoi selezionare al massimo 3 interessi.")

        return interessi


# identico a DjangoPostForm ma per i post dentro un gruppo
class PostGruppoForm(forms.ModelForm):
    testo = forms.CharField(max_length=2000, required=False, widget=forms.Textarea)

    class Meta:
        model = PostGruppo
        fields = ["testo", "immagine"]

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("testo") and not self.files.get("immagine"):
            raise forms.ValidationError("Devi inserire almeno un testo o un'immagine.")

        return cleaned


# form minimale per segnalare qualcosa: motivo a parte, tipo e oggetto segnalato li imposta la view
class SegnalazioneForm(forms.ModelForm):
    class Meta:
        model = Segnalazione
        fields = ["motivo"]


class CommentoGruppoForm(forms.ModelForm):
    class Meta:
        model = CommentoGruppo
        fields = ["testo"]
