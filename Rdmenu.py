import subprocess
import socket
import time

prefs = {'dmenu':'dmenu',\
        'Rcmd':'/usr/bin/R',\
        'menu_arguments':[ "-i", "-nf", "#888888", "-nb", "#1D1F21", "-sf",\
        "#ffffff", "-sb", "#1D1F21", "-fn", "Inconsolata", "-l", "20" ],\
        'encoding':'UTF-8'}

RscriptOpen = '''
con  <- socketConnection( host="localhost", port= 6011, blocking=TRUE, server=TRUE, open="r+")
while(TRUE) {
   data  <- readLines(con,1)
   response  <- eval(parse(text=data))
   writeLines(format(response),con)
   }
}'''

RscriptClose = '''
close(con)
quit()
'''

class dmenu(object):

    def menu(self, items, prompt=""):
        """Display a menu in dmenu and return chosen item"""

        user = subprocess.Popen([prefs['dmenu']] + prefs['menu_arguments'] + ['-p', prompt], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE)

        response = user.communicate(items.encode(prefs['encoding']))[0]

        response = response.decode(prefs['encoding'])
        response = response.strip('\n')
        response = response.strip()

        return response

class Rserver(object):
    Rprocess = None
    socket = None

    def __init__(self):
        
        # Remove leading and trailing newlines,
        # replace the others with ; strip whitespace
        # and quotes to send to R
        self.RscriptOpen = RscriptOpen.strip()
        self.RscriptOpen = self.RscriptOpen.replace(' ', '')
        self.RscriptOpen = self.RscriptOpen.replace('\n', ';')
        self.RscriptOpen = "'" + self.RscriptOpen + "'"

        self.RscriptClose = RscriptClose.strip()
        self.RscriptClose = self.RscriptClose.replace(' ', '')
        self.RscriptClose = self.RscriptClose.replace('\n', ';')

    def open(self):
        """Start R instance and open socket"""

        self.Rprocess = subprocess.Popen(prefs['Rcmd'] + ' --slave --vanilla -e ' + self.RscriptOpen,
                shell=True)
        time.sleep(1) # Wait to allow R to get the socket ready
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("localhost", 6011))

    def close(self):
        """Close socket and quit R instance"""

        self.socket.close()
        self.socket=None

        self.Rprocess.terminate()
        self.Rprocess = None

    def compute(self, expression):
        """Evaluate a string in R"""

        expression.strip('\n')
        expression = expression + '\n'

        self.socket.send(expression.encode())

        response = self.socket.recv(4096)
        response = response.decode()
        response = response.strip('\n')

        return response

def main():

    D = dmenu()

    R = Rserver()
    R.open()

    history = []

    while True:
        
        displayHistory = ''.join(e + '\n' for e in history)
        expression = D.menu(displayHistory,">>>")
        if expression == "Q":
            break
        history.append(R.compute(expression) + '# ' + expression)

    R.close()

if __name__=="__main__":
    main()
