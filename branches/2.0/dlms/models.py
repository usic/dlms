from django.db import models

from django.contrib.auth.models import User

# Create your models here.

class Torrent(models.Model):
    transmission_hash_string = models.CharField(max_length=40)
    url = models.CharField(max_length=2048)
    creation_date = models.DateTimeField(auto_now_add=True)
    finish_date = models.DateTimeField(auto_now_add=True)
    finished = models.BooleanField()
    user = models.ForeignKey(User)


class File(models.Model):
    url = models.CharField(max_length=2048)
    creation_date = models.DateTimeField(auto_now_add=True)
    finish_date = models.DateTimeField()
    finished = models.BooleanField()

   


