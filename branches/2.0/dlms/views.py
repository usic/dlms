# coding: UTF-8
# Create your views here.

from __future__ import division

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from dlms.models import Torrent
from django.conf import settings

import transmissionrpc
from transmissionrpc import TransmissionError

import os
import shutil
import urllib2
from bencode import *
from hashlib import sha1

import download

from django import forms

class UploadFileForm(forms.Form):
    file  = forms.FileField("Файл:")


def format_data(value):
    """Utility function to present user-friendly bytes"""
    units = ("Байт", "КіБайт", "МіБайт", "ГіБайт")
    
    for unit in units:
        if value >= 1024.0:
            value /= 1024.0
        else:
            return "%(value).2f %(unit)s" % {'value': value,
                                             'unit': unit }

def doLogin(request):
    
    if request.method == 'GET':
        return render_to_response('dlms/login.html', { 'errorFlag': False })
        
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('dlms.views.index'))
            
        else:
            return render_to_response('dlms/login.html', { 'errorFlag': True })
        

@login_required
def index(request):
    
    errorFlag = False
    user = request.user
    username = user.username
    
    # the transmission client object, used for torrent management
    tc = transmissionrpc.Client(settings.TRANSMISSION_SETTINGS['host'],
                                port=settings.TRANSMISSION_SETTINGS['port'],
                                user=settings.TRANSMISSION_SETTINGS['user'],
                                password=settings.TRANSMISSION_SETTINGS['password'])
    
    url = ''
    magicString = ''
    
    adminFlag = False
    
    if user.is_staff:
            adminFlag = True
            
    uriToAdd = None
    torrent = None
    
    fileName = 'phony'
    fileSize = -999
    
    if request.method == 'POST':
        
        
        form = UploadFileForm(request.POST, request.FILES)
        
        if form.is_valid():
            # process the uploaded torrent file
            uploadedFile = request.FILES['file']
            
            
            tempFileName = '/tmp/' + uploadedFile.name
            destination = open(tempFileName, 'wb+')
            
            for chunk in uploadedFile.chunks():
                destination.write(chunk)
                if len(chunk) > 11:
                    magicString = chunk[0:11]
                    
                    if magicString == "d8:announce":
                        fileName = uploadedFile.name
                        fileSize = uploadedFile.size
                        
            destination.close()
            
            if fileSize != -999:
                torrent = download.Torrent('', fileName=tempFileName)
            
                torrentHashString = torrent.GetHashstring()
                uriToAdd = torrent.GetURI()

        
        else:
            url = request.POST['url']
            
        
            # if the url starts with "magnet:", it is a magnet link, so add it to
            # transmission by URL
            if url.startswith("magnet:"):
                magnet = download.Magnet(url)
                torrentHashString = magnet.GetHashstring()
                uriToAdd = url
            else:    
                try:
                    # read the first 11 bytes to determine whether this is a torrent fileList
                    handle = urllib2.urlopen(url) 
                    magicString = handle.read(11)
                except ValueError, e:
                    errorFlag = True
                
                if magicString == "d8:announce":
                    torrent = download.Torrent(url)
            
                    torrentHashString = torrent.GetHashstring()
                    uriToAdd = torrent.GetURI()
                
        if not uriToAdd is None:
            
            #torrentListForHash = Torrent.objects.filter(transmission_hash_string=torrentHashString, user=user)
            
            torrentCountForHash = Torrent.objects.filter(transmission_hash_string=torrentHashString).count()
            torrentCountForHashUser = Torrent.objects.filter(transmission_hash_string=torrentHashString, user=user).count()
            
            # if the hashstring of the torrent is already in the db, but not for this user, 
            # just add it to the db without adding to transmission
            #if len(torrentListForHash) == 0:
            if torrentCountForHash == 0:
        
                # add the torrent to transmission
                globalDownloadDir = settings.GLOBAL_DOWNLOAD_DIR
                userDir = globalDownloadDir + torrentHashString
        
                try:
                    addedTorrent = tc.add_uri(uriToAdd, download_dir = userDir)
                except TransmissionError, e:
                    errorFlag = True
    
            if torrentCountForHashUser == 0:
                # save the record to the db
                torrentDB = Torrent(url=url, user=user, transmission_hash_string=torrentHashString)
                torrentDB.save()
    
            if not torrent is None:
                torrent.DeleteFile()
                
        else:
            errorFlag = True
            
    userTorrents = []    
    
    if user.is_staff:
        userTorrents = Torrent.objects.all()
    else:
        userTorrents = user.torrent_set.all()
    

    userHashstrings = {}
    
    for userTorrent in userTorrents:
        hashString = userTorrent.transmission_hash_string
        
        if not hashString in userHashstrings:
            userHashstrings[hashString] = []

        userHashstrings[hashString].append(userTorrent.user.username)
            
    torrentList = {}
    
    if userHashstrings:
        hashStrings = userHashstrings.keys()
        
        torrentList = tc.info(hashStrings)
    
    presList = [] 
    
    fileLists = []

    for torrent in torrentList.values():
        files = []
        
        totalSizeBytes = 0
        
        for item_number, item_description in torrent.files().items():
            
            sizeBytes = format_data(item_description['size'])
            
            completedBytes = format_data(item_description['completed'])
                
            completedPercent = "%.2f" % (item_description['completed'] / item_description['size'] * 100) 
            
            files.append({
                'name': item_description['name'],
                'name_short': os.path.basename(item_description['name']),
                'size_bytes': sizeBytes,
                'completed_bytes': completedBytes,
                'completed_percent': completedPercent,
                'finished': item_description['completed'] == item_description['size']})
            
            totalSizeBytes += item_description['size']
        
       
        presTorrent = {
            'name': torrent.name,
            'usernames': userHashstrings[torrent.hashString],
            'hashString': torrent.hashString,
            'progress': torrent.progress,
            'status': torrent.status,
            'date_added': torrent.date_added,
            'date_done': torrent.date_done,
            'eta': torrent.eta,
            'total_size': format_data(totalSizeBytes),
            'finished': torrent.progress == 100.0,
            
            }
            
        if len(files) > 0:
            presTorrent['files'] = files
            presTorrent['first_file'] = files[0]
            presTorrent['files_count'] = len(torrent.files().items())
            
            
        presList.append(presTorrent)

       


    
    # if GET, just show the list and the add form
    if request.method == 'GET':
        
        form = UploadFileForm()

        
        
        if 'list_only' in request.GET:
            return render_to_response('dlms/item_list.html', {'torrent_list': presList, 'adminFlag': adminFlag})
     
    return render_to_response('dlms/index.html', {'torrent_list': presList,
                                                          'user': username,
                                                          'errorFlag': errorFlag,
                                                          'adminFlag': adminFlag,
                                                          'torrentURL': url,
                                                          'uploadForm': form,
                                                          'fileName': fileName,
                                                          'fileSize': fileSize})
           
def delItem(request, hash_string):

    user = request.user

    torrentsToDelete = Torrent.objects.filter(transmission_hash_string=hash_string)

    torrentByUser = user.torrent_set.filter(transmission_hash_string=hash_string)
    
    # if this is the last reference to the torrent, delete it from transmission
    if len(torrentByUser) > 0:
  
        if len(torrentsToDelete) == 1:
            tc = transmissionrpc.Client(settings.TRANSMISSION_SETTINGS['host'],
                                port=settings.TRANSMISSION_SETTINGS['port'],
                                user=settings.TRANSMISSION_SETTINGS['user'],
                                password=settings.TRANSMISSION_SETTINGS['password'])
            tc.remove(hash_string, delete_data=True)
        
            #globalDownloadDir = "/var/www/dlms_downloads/"
            globalDownloadDir = settings.GLOBAL_DOWNLOAD_DIR
            userDir = globalDownloadDir + hash_string
        
            #if os.path.exists(userDir):
                #shutil.rmtree(userDir)
                

        # delete from db
        torrentToDelete = user.torrent_set.filter(transmission_hash_string=hash_string)[0]
        torrentToDelete.delete()
    
    return HttpResponseRedirect(reverse('dlms.views.index'))



