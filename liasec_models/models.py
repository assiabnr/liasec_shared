from django.db import models

import re

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin, Group, Permission
from django.db import models
from django.utils import timezone

from django.utils.timezone import now




class CompteManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("actif", True)
        return self.create_user(email, password, **extra_fields)


class Compte(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [('admin', 'Administrateur'), ('client', 'Client')]
    LANGUE_CHOICES = [('fr', 'Français'), ('en', 'English')]

    email = models.EmailField(unique=True, verbose_name="Adresse email")
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='client', verbose_name="Rôle")
    date_creation = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    actif = models.BooleanField(default=True, verbose_name="Compte actif")
    langue = models.CharField(max_length=10, choices=LANGUE_CHOICES, default="fr", verbose_name="Langue préférée")
    recoit_notifications = models.BooleanField(default=True, verbose_name="Recevoir des notifications")
    theme_sombre = models.BooleanField(default=False, verbose_name="Thème sombre activé")
    premiere_connexion = models.BooleanField(default=True, verbose_name="Première connexion")
    derniere_visite_notifications = models.DateTimeField(default=now, verbose_name="Dernière visite des notifications")
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    groups = models.ManyToManyField(
        Group,
        verbose_name='Groupes',
        blank=True,
        help_text="Groupes auxquels ce compte appartient.",
        related_name='comptes',
        related_query_name='compte'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='Permissions',
        blank=True,
        help_text="Permissions spécifiques pour ce compte.",
        related_name='comptes',
        related_query_name='compte'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CompteManager()

    def __str__(self):
        return self.email



class Enseigne(models.Model):
    nom = models.CharField(max_length=100)
    secteur_activite = models.CharField(max_length=100)
    date_inscription = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom


class Magasin(models.Model):
    enseigne = models.ForeignKey("Enseigne", on_delete=models.CASCADE, verbose_name="Enseigne")
    nom = models.CharField(max_length=100, verbose_name="Nom du magasin")
    adresse = models.CharField(max_length=255, verbose_name="Adresse")
    ville = models.CharField(max_length=100, verbose_name="Ville")
    code_postale = models.CharField(max_length=20, verbose_name="Code postal")
    pays = models.CharField(max_length=50, verbose_name="Pays")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")

    def __str__(self):
        return f"{self.nom} - {self.ville}"



class CompteEnseigne(models.Model):
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE)
    magasin = models.ForeignKey(Magasin, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)
    date_lien = models.DateTimeField(auto_now_add=True)



class Borne(models.Model):
    ETAT_CHOICES = [("en ligne", "En ligne"), ("hors ligne", "Hors ligne")]

    magasin = models.ForeignKey(Magasin, on_delete=models.CASCADE)
    numero_serie = models.CharField(max_length=100, unique=True)
    etat = models.CharField(max_length=20, choices=ETAT_CHOICES, default="en ligne")
    date_installation = models.DateTimeField(auto_now_add=True)
    derniere_connexion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.numero_serie



class Utilisateur(models.Model):
    type = models.CharField(max_length=50)
    identifiant = models.CharField(max_length=100, unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)


class Session(models.Model):
    borne = models.ForeignKey(Borne, on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    debut = models.DateTimeField(default=timezone.now)
    fin = models.DateTimeField(null=True, blank=True)




class Produit(models.Model):
    magasin = models.ForeignKey(
        "Magasin",
        on_delete=models.CASCADE,
        related_name="produits",
        verbose_name="Magasin"
    )
    nom = models.CharField(max_length=255, verbose_name="Nom du produit")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    categorie = models.CharField(max_length=100, blank=True, null=True, verbose_name="Catégorie")
    prix = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix")
    reference_interne = models.CharField(max_length=100, unique=True, verbose_name="Référence interne")
    disponibilite = models.BooleanField(default=True, verbose_name="Disponible")
    image = models.URLField(blank=True, null=True, verbose_name="Image (URL)")

    marque = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.nom} ({'Disponible' if self.disponibilite else 'Indisponible'})"



class Stock(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.IntegerField()
    date_mise_a_jour = models.DateTimeField(auto_now=True)



class Conversation(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    produits_recommandes = models.ManyToManyField(Produit, blank=True)
    date_debut = models.DateTimeField(auto_now_add=True)
    satisfaction = models.BooleanField(null=True, blank=True, default=None)
    delai_recommandation = models.IntegerField(null=True, blank=True, verbose_name="Délai avant première recommandation (secondes)")


    def __str__(self):
        return f"Conversation #{self.id} - Session {self.session.id}"



class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    auteur = models.CharField(max_length=10, choices=[("client", "Client"), ("ia", "IA")])
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    is_recommandation = models.BooleanField(default=False)
    produit_recommande = models.ForeignKey(Produit, null=True, blank=True, on_delete=models.SET_NULL)


    def produits_recommandes_extraits(self):
        if not self.is_recommandation:
            return []
        return re.findall(r"\*\*Produit\s?:\*\*\s(.+)", self.contenu)
    satisfaction = models.BooleanField(null=True, blank=True)


    def __str__(self):
        return f"{self.date_envoi} - {self.auteur.upper()} : {self.contenu[:30]}..."



class Messagerie(models.Model):
    magasin = models.ForeignKey('Magasin', on_delete=models.CASCADE, related_name='conversations_magasin', verbose_name="Magasin concerné", null=True, blank=True)
    expediteur = models.ForeignKey('Compte', on_delete=models.SET_NULL, null=True, blank=True, related_name="messageries_envoyees", verbose_name="Expéditeur")
    pour_tous_admins = models.BooleanField(default=False, verbose_name="Visible par tous les admins")
    titre = models.CharField(max_length=255, verbose_name="Objet de la discussion")
    date_creation = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    last_updated = models.DateTimeField(default=timezone.now, verbose_name="Dernière activité")
    est_lu_par_client = models.BooleanField(default=False, verbose_name="Lu par le client")
    est_lu_par_admin = models.BooleanField(default=False, verbose_name="Lu par l'administrateur")
    supprime_par_admin = models.BooleanField(default=False, verbose_name="Supprimée côté admin")
    supprime_par_client = models.BooleanField(default=False, verbose_name="Supprimée côté client")
    archived = models.BooleanField(default=False, verbose_name="Archivée")

    def __str__(self):
        if self.pour_tous_admins:
            return f"{self.titre} (Message aux admins)"
        elif self.magasin:
            return f"{self.titre} – {self.magasin.nom} ({self.magasin.ville})"
        return f"{self.titre} (Conversation)"

    def restaurer_si_message_recu(self, auteur):
        if auteur.role == "admin" and self.supprime_par_client:
            self.supprime_par_client = False
        elif auteur.role == "client" and self.supprime_par_admin:
            self.supprime_par_admin = False
        self.last_updated = timezone.now()
        self.save(update_fields=["supprime_par_client", "supprime_par_admin", "last_updated"])

    class Meta:
        ordering = ['-last_updated']
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

class MessageChat(models.Model):
    messagerie = models.ForeignKey(Messagerie, on_delete=models.CASCADE, related_name="messages", verbose_name="Messagerie liée")
    auteur = models.ForeignKey('Compte', on_delete=models.CASCADE, verbose_name="Auteur")
    contenu = models.TextField(verbose_name="Message")
    date_envoi = models.DateTimeField(default=timezone.now, verbose_name="Date d'envoi")
    visible_par_admin = models.BooleanField(default=True, verbose_name="Visible côté admin")
    visible_par_client = models.BooleanField(default=True, verbose_name="Visible côté client")
    lu_par_admin = models.BooleanField(default=False, verbose_name="Lu par l'administrateur")
    lu_par_client = models.BooleanField(default=False, verbose_name="Lu par le client")

    def __str__(self):
        return f"{self.auteur.email} · {self.date_envoi.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        ordering = ['date_envoi']
        verbose_name = "Message de chat"
        verbose_name_plural = "Messages de chat"

class Facture(models.Model):
    magasin = models.ForeignKey(Magasin, on_delete=models.CASCADE, verbose_name="Magasin concerné")
    fichier_pdf = models.FileField(upload_to="factures_pdfs/", verbose_name="Fichier PDF")
    date_upload = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    payee = models.BooleanField(default=False, verbose_name="Facture payée")

    def __str__(self):
        return f"{self.magasin.nom} - {'Payée' if self.payee else 'Impayée'} - {self.date_upload.strftime('%d/%m/%Y')}"

    class Meta:
        ordering = ['-date_upload']

class Notification(models.Model):
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='notifications', verbose_name="Compte concerné")
    titre = models.CharField(max_length=255, verbose_name="Titre")
    message = models.TextField(verbose_name="Contenu")
    est_lu = models.BooleanField(default=False, verbose_name="Lu")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    def __str__(self):
        return f"Notification pour {self.compte.email} – {self.titre}"

    class Meta:
        ordering = ['-date_creation']

class TacheClient(models.Model):
    magasin = models.ForeignKey("Magasin", on_delete=models.CASCADE, null=True, blank=True)
    compte = models.ForeignKey("Compte", on_delete=models.CASCADE, null=True, blank=True)
    texte = models.CharField(max_length=255)
    est_faite = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.texte



