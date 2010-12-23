from django.contrib.auth.models import User
import subprocess

class UMSBackend:
    def authenticate(self, username=None, password=None):
        checkScript = "/home/sana/usic/ums_utils/bin/usiccheckpasswd"
        p = subprocess.Popen([checkScript, username], stdin=subprocess.PIPE)
        p.stdin.write(password + "\n")
        ret = p.wait()
        
        if ret == 0:
            userList = User.objects.filter(username=username)
            if len(userList) == 0:
                user = User(username=username)
                user.save()
            else:
                user = userList[0]
                    
            return user    
        return None
        
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
