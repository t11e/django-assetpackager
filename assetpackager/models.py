from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

#For People who want to use the Sites application
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager

from sha import sha

class Asset(models.Model):
    name = models.TextField(blank=True)
    _hash = models.CharField(blank=True, null=True, max_length=128)
    asset_type = models.CharField(blank=True, max_length=3, choices=[('css','CSS'),('js', 'Javascript')])
    created_on = models.DateTimeField(auto_now=True)
    #Comment this out if you dont want to use sites
    site = models.ForeignKey(Site)
    
    #Site Manager
    on_site = CurrentSiteManager()
    
    class Meta:
        unique_together = (
            #Uncomment this and comment out the otherone if you are not using the Site Application
            #('name', 'asset_type'),
            ('name', 'asset_type', 'site'),
        )

class Javascript(models.Model):
    javascript = models.FileField(upload_to="js")
    order = models.IntegerField(default=0)
    #Comment this out if you dont want to use sites
    site = models.ForeignKey(Site)
    
    #Site Manager
    on_site = CurrentSiteManager()
   
    class Meta:
        ordering = ('order',)
        
    class Admin:
        fields = (
            (_("File"), {'fields': ('javascript','order')}),
            #Remove this if you are not using Sites Application
            (_("Site"), {'fields': ('site',)}),
        )

        list_display = ('javascript', 'order', 'site')
        
class CSS(models.Model):
    css = models.FileField(upload_to="css")
    order = models.IntegerField(default=0)
    #Comment this out if you dont want to use sites
    site = models.ForeignKey(Site)
    
    #Site Manager
    on_site = CurrentSiteManager()
   
    class Meta:
        ordering = ('order',)
        
    class Admin:
        fields = (
            (_("File"), {'fields': ('css','order')}),
            #Remove this if you are not using Sites Application
            (_("Site"), {'fields': ('site',)}),
        )

        list_display = ('css', 'order', 'site')