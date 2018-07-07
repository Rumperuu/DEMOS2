from __future__ import unicode_literals

import json

from django.core.mail import send_mail
from django.db import models
from django.utils import timezone

from allauthdemo.auth.models import DemoUser

class EmailUser(models.Model):
    email = models.CharField(max_length=80, unique=True)

    def send_email(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])

    def __unicode__(self):
        return self.email


class Event(models.Model):
    users_organisers = models.ManyToManyField(DemoUser, blank=True, related_name="organisers")
    users_trustees = models.ManyToManyField(EmailUser, blank=True, related_name="trustees")
    voters = models.ManyToManyField(EmailUser, blank=True, related_name="voters")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    prepared = models.BooleanField(default=False)
    ended = models.BooleanField(default=False)
    public_key = models.CharField(null=True, blank=False, max_length=1024)
    title = models.CharField(max_length=1024)
    EID = models.CharField(max_length=2048, blank=True)
    creator = models.CharField(max_length=256, blank=True)
    c_email = models.CharField(max_length=512, blank=True)
    trustees = models.CharField(max_length=4096)

    # Custom helper methods
    def EID_hr(self):
        EID_json = json.loads(self.EID)
        return EID_json['hr']

    def EID_crypto(self):
        EID_json = json.loads(self.EID)
        EID_crypto_str = EID_json['crypto']
        return json.loads(EID_crypto_str)

    def duration(self):
        duration_str = self.start_time_formatted()
        duration_str = duration_str + " - " + self.end_time_formatted_utc()
        return duration_str

    def start_time_formatted(self):
        return self.start_time.strftime("%d-%m-%y %H:%M")

    def start_time_formatted_utc(self):
        return self.start_time.strftime("%d-%m-%y %H:%M %Z")

    def end_time_formatted(self):
        return self.end_time.strftime("%d-%m-%y %H:%M")

    def end_time_formatted_utc(self):
        return self.end_time.strftime("%d-%m-%y %H:%M %Z")

    def status(self):
        status_str = ""

        # Get the current date and time to compare against to establish if this is a past, current or
        # future event
        present = timezone.now()

        if self.ended is False:
            if present < self.start_time and self.public_key is None:
                status_str = "Future"
            elif present < self.start_time and self.public_key is not None:
                status_str = "Prepared"
            elif present >= self.start_time and present <= self.end_time and self.public_key is not None:
                status_str = "Active"
            elif present > self.end_time and self.public_key is not None:
                status_str = "Expired"
        else:
            if self.event_sk.all().count() == 1:
                status_str = "Decrypted"
            elif self.event_sk.all().count() == 0:
                status_str = "Ended"

        return status_str

    '''
        The result applies to all polls for an event so True will only be returned when votes have
        been received for every poll. 
    '''
    def has_received_votes(self):
        received_votes = True

        for poll in self.polls.all():
            if Ballot.objects.filter(poll=poll, cast=True).count() == 0:
                received_votes = False

        return received_votes

    def __str__(self):
        return self.title


class TrusteeKey(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="trustee_keys")
    user = models.ForeignKey(EmailUser, on_delete=models.CASCADE, related_name="trustee_keys")
    key = models.CharField(max_length=255, unique=True)

class AccessKey(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="keys")
    user = models.ForeignKey(EmailUser, on_delete=models.CASCADE, related_name="keys")
    key = models.CharField(max_length=255, unique=True)

    #total = models.IntegerField(blank=True, null=True, default=0)

    def has_started(self):
        return timezone.now() >= self.start

    def has_ended(self):
        return timezone.now() >= self.end

    def __unicode__(self):
        return self.title

class Poll(models.Model):
    question_text = models.CharField(max_length=200)
    total_votes = models.IntegerField(default=0)
    min_num_selections = models.IntegerField(default=0)
    max_num_selections = models.IntegerField(default=1)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="polls")
    enc = models.CharField(max_length=4096, null=True)

    #index = models.IntegerField()

    def __str__(self):
        return self.question_text

class PollOption(models.Model):
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    question = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    #index = models.IntegerField()

    def __str__(self):
        return self.choice_text

class Decryption(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="decryptions")
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="decryptions")
    user = models.ForeignKey(EmailUser, on_delete=models.CASCADE, related_name="decryptions")
    text = models.CharField(max_length=1024)

class TrusteeSK(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="trustee_sk")
    trustee = models.ForeignKey(EmailUser, on_delete=models.CASCADE, related_name="trustee_sk")
    key = models.CharField(max_length=1024)

class EventSK(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="event_sk")
    key = models.CharField(max_length=1024)

class Ballot(models.Model):
    voter = models.ForeignKey(EmailUser, on_delete=models.CASCADE, related_name="ballots")
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="ballots")
    cast = models.BooleanField(default=False)

# Implements the new binary encoding scheme
class EncryptedVote(models.Model):
    ballot = models.ForeignKey(Ballot, on_delete=models.CASCADE, related_name="encrypted_vote")

class VoteFragment(models.Model):
    encrypted_vote = models.ForeignKey(EncryptedVote, on_delete=models.CASCADE, related_name="fragment")
    cipher_text_c1 = models.CharField(max_length=4096)
    cipher_text_c2 = models.CharField(max_length=4096)

class Organiser(models.Model):
    index = models.IntegerField(default=0)
    email = models.CharField(max_length=100, blank=False, null=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)


