import os
import urllib2
import urlparse
from bencode import *
from hashlib import sha1

class Download:

    def __init__(self, url):
        self.url = url

    def GetHashstring(self):
        pass

    def GetURI(self):
        pass


class Torrent(Download):
    def __init__(self, url, fileName = None):  
        
        if fileName is None:
            handle = urllib2.urlopen(url) 

            # download the torrent into a temp dir
            self.tempFileName = "/tmp" + "/" + os.path.basename(url)
                
            tempFileHandle = file(self.tempFileName, 'w')
            tempFileHandle.write(handle.read())            
            tempFileHandle.close()
            
        else:
            self.tempFileName = fileName

        tempFileHandle = file(self.tempFileName, 'r')
                        
        torrentInfo = bdecode(tempFileHandle.read())
        self.torrentHashString = sha1(bencode(torrentInfo['info'])).hexdigest()
   
    def GetHashstring(self):
        return self.torrentHashString
        
    def GetURI(self):
        return self.tempFileName
        
    def DeleteFile(self):
        pass
        # delete the temp torrent file
        #os.remove(tempFileName)

class Magnet(Download):
    def __init__(self, url):
        queryString = url.split("?")[1]
        parsedQueryString = urlparse.parse_qs(queryString)
        self.hashString = parsedQueryString['xt'][0].split(":")[2]
        
    def GetHashstring(self):
        return self.hashString

class File(Download):
    pass

