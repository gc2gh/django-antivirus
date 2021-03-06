import os

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from django.utils.translation import ugettext_lazy as _

import app_settings
from utils import path_to_object

FILE_STANDING = 0
FILE_VIRUS_NOT_FOUND = 1
FILE_VIRUS_FOUND = -1
FILE_NOT_EXISTS = -2

FILE_STATUS_CHOICES = (
    (FILE_STANDING,        _('Standing')),
    (FILE_VIRUS_NOT_FOUND, _('Virus not found')),
    (FILE_VIRUS_FOUND,     _('Virus found')),
    (FILE_NOT_EXISTS,      _('Not exists')),
)

class FileManager(models.Manager):
    """Default manager for File model class"""
    def get_or_create_for_object(self, obj, file_path, url=None):
        """Create an file reference for an specific object and file field"""
        ctype = ContentType.objects.get_for_model(obj)
        file, new = self.get_or_create(
                path = file_path,
                defaults = {
                    'content_type': ctype,
                    'object_id': obj.id,
                    'url': url,
                    }
                )

        return file

class File(models.Model):
    """Model class to storage file checked (or to be checked) by antivirus"""
    path = models.CharField(max_length=250, unique=True)
    status = models.SmallIntegerField(default=0, blank=True, choices=FILE_STATUS_CHOICES)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object = GenericForeignKey()
    viruses_found = models.TextField(blank=True)
    url = models.URLField(blank=True, null=True)

    objects = FileManager()

    def __unicode__(self):
        return self.path

    class Meta:
        pass

    def scanfile(self, backend_path=app_settings.ANTIVIRUS_BACKEND):
        """Uses the antivirus backend to scan the file for virus"""
        if not self.check_file_exists():
            return False

        backend_class = path_to_object(backend_path)
        backend = backend_class()

        found, virus = backend.scanfile(self.path)

        if found:
            self.viruses_found = virus
            self.status = FILE_VIRUS_FOUND
            self.save()
        else:
            self.viruses_found = ''
            self.status = FILE_VIRUS_NOT_FOUND
            self.save()

        return found

    def check_file_exists(self):
        """Checks if a file exists, save this information and returns it"""
        if self.status != FILE_NOT_EXISTS and not os.path.isfile(self.path):
            self.status = FILE_NOT_EXISTS
            self.save()
            return False

        elif self.status == FILE_NOT_EXISTS and os.path.isfile(self.path):
            self.status = FILE_STANDING
            self.save()

        return True

