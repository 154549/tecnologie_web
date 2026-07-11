from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Profilo, DjangoPost, Like, RichiestaAmicizia, Djangroup, PostGruppo


#verifica che il codice dell'amicizia funzioni correttamente se aggiunta da un solo lato
class AmiciziaModelTest(TestCase):
    def setUp(self):
        self.luca = User.objects.create_user(username="testluca", password="pass1234")
        self.sara = User.objects.create_user(username="testsara", password="pass1234")
        self.marco = User.objects.create_user(username="testmarco", password="pass1234")
        Profilo.objects.create(user=self.luca)
        Profilo.objects.create(user=self.sara)
        Profilo.objects.create(user=self.marco)

    def test_amicizia_non_simmetrica_se_aggiunta_da_un_solo_lato(self):
        self.luca.profilo.amici.add(self.sara)
        self.assertTrue(self.luca.profilo.is_amico_di(self.sara))
        self.assertFalse(self.sara.profilo.is_amico_di(self.luca))


#verifica del client con aggiunta e rimozione del like con un doppio toggle
class ToggleLikeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testliker2", password="pass1234")
        Profilo.objects.create(user=self.user)
        self.autore = User.objects.create_user(username="testautore2", password="pass1234")
        Profilo.objects.create(user=self.autore)
        self.post = DjangoPost.objects.create(autore=self.autore, testo="Post di test")

    def test_toggle_aggiunge_like(self):
        self.client.login(username="testliker2", password="pass1234")
        self.client.get(f"/togglelike/{self.post.pk}/")
        self.assertTrue(self.post.ha_like_di(self.user))

    def test_doppio_toggle_rimuove_like(self):
        self.client.login(username="testliker2", password="pass1234")
        self.client.get(f"/togglelike/{self.post.pk}/")
        self.client.get(f"/togglelike/{self.post.pk}/")
        self.assertFalse(self.post.ha_like_di(self.user))


#verifica che il client risponda correttamente al flusso completo di richiesta e accettazione di amicizia
class AmiciziaViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.luca = User.objects.create_user(username="testluca3", password="pass1234")
        self.sara = User.objects.create_user(username="testsara3", password="pass1234")
        Profilo.objects.create(user=self.luca)
        Profilo.objects.create(user=self.sara)

    def test_accetta_richiesta_crea_amicizia(self):
        self.client.login(username="testluca3", password="pass1234")
        self.client.post("/inviarichiesta/testsara3/")
        richiesta = RichiestaAmicizia.objects.get(mittente=self.luca, destinatario=self.sara)
        self.client.login(username="testsara3", password="pass1234")
        self.client.get(f"/accettarichiesta/{richiesta.pk}/")
        self.assertTrue(self.luca.profilo.is_amico_di(self.sara))
        self.assertTrue(self.sara.profilo.is_amico_di(self.luca))


#verifica che un profilo privato sia visibile solo agli amici
class ProfiloPrivatoViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.privato = User.objects.create_user(username="testprivato", password="pass1234")
        Profilo.objects.create(user=self.privato, is_privato=True, bio="bio")
        self.post = DjangoPost.objects.create(autore=self.privato, testo="post")
        self.estraneo = User.objects.create_user(username="testestraneo2", password="pass1234")
        Profilo.objects.create(user=self.estraneo)

    def test_estraneo_non_puo_mettere_like_su_post_privato(self):
        self.client.login(username="testestraneo2", password="pass1234")
        self.client.get(f"/togglelike/{self.post.pk}/")
        self.assertFalse(self.post.ha_like_di(self.estraneo))

    def test_amico_vede_profilo_privato(self):
        self.privato.profilo.amici.add(self.estraneo)
        self.estraneo.profilo.amici.add(self.privato)
        self.client.login(username="testestraneo2", password="pass1234")
        response = self.client.get("/profilo/testprivato/")
        self.assertContains(response, "bio")
        self.assertContains(response, "post")


#verifica che i post di un gruppo siano visibili secondo la privacy
class DettaglioGruppoViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.creatore = User.objects.create_user(username="testcreatoregruppo", password="pass1234")
        Profilo.objects.create(user=self.creatore)
        self.estraneo = User.objects.create_user(username="testestraneogruppo", password="pass1234")
        Profilo.objects.create(user=self.estraneo)

        self.gruppo_pubblico = Djangroup.objects.create(nome="Gruppo Pubblico Test", creatore=self.creatore)
        self.gruppo_pubblico.membri.add(self.creatore)
        PostGruppo.objects.create(autore=self.creatore, gruppo=self.gruppo_pubblico, testo="post pubblico di gruppo")

        self.gruppo_privato = Djangroup.objects.create(nome="Gruppo Privato Test", creatore=self.creatore, is_privato=True)
        self.gruppo_privato.membri.add(self.creatore)
        PostGruppo.objects.create(autore=self.creatore, gruppo=self.gruppo_privato, testo="post privato di gruppo")

    def test_estraneo_non_vede_post_di_gruppo_privato(self):
        self.client.login(username="testestraneogruppo", password="pass1234")
        response = self.client.get(f"/gruppo/{self.gruppo_privato.pk}/")
        self.assertNotContains(response, "post privato di gruppo")
