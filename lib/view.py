from config.config import *
config = getConfig()
extensions = config['extensions'][1:-1]
http_method = config['http_method']
thread_count = config['thread_count']


def view(msg_class, msg=[]):
    if msg_class == "init":
        ext = "\033[1;31m%s\033[0m" % "Extensions: " + "\033[1;33m%s\033[0m" % extensions
        httpm = "\033[1;31m%s\033[0m" % "HTTP method: " + "\033[1;33m%s\033[0m" % http_method
        wordsz = "\033[1;31m%s\033[0m" % "Wordlist size: " + "\033[1;33m%s\033[0m" % msg[0]
        threadcount = "\033[1;31m%s\033[0m" % "Threads: " + "\033[1;33m%s\033[0m" % thread_count
        ban = "\033[1;31m%s\033[0m" % BANNER
        m = ban + "\n" + " | ".join([ext, httpm, threadcount, wordsz]) + "\n"
    if msg_class == "target":
        m = "\033[1;31m%s\033[0m" % "Target: " + "\033[1;33m%s\033[0m" % msg[0]
    if msg_class == "start":
        current_time = time.strftime("%H:%M:%S")
        m = "\033[1;33m%s\033[0m" % (f"[{current_time}] Starting: {msg[0]}")
    if msg_class == "scanning":
        response = msg[0]
        status = response.status
        target = "/" + response.full_path
        current_time = time.strftime("%H:%M:%S")
        mm = f"[{current_time}] {status} - {target}"        
        if status in (200, 201, 204):
            m = "\033[1;32m%s\033[0m" % mm
        elif status == 401:
            m = "\033[1;33m%s\033[0m" % mm
        elif status == 403:
            m = "\033[1;34m%s\033[0m" % mm
        elif status in range(500, 600):
            m = "\033[1;31m%s\033[0m" % mm
        else:
            m = mm
        if response.redirect:
            m += f"  ->  {response.redirect}"
        for redirect in response.history:
            m += f"\n-->  {redirect}"               
    print(m)
