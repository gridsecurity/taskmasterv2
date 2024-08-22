import base64
import cryptocode
import time
from django.template.loader import render_to_string


def request_email_processor(m):
    epoch = int(time.time())
    dict = {
        "tca_approval": base64.b64encode(cryptocode.encrypt("{}|tca_rm|{}".format(m.sender.address, epoch), "Mega Puffin 5000").encode('ascii')).decode("ascii"),
        "access_approval":  base64.b64encode(cryptocode.encrypt("{}|access|{}".format(m.sender.address, epoch), "Mega Puffin 5000").encode('ascii')).decode("ascii"),
        "change_approval":  base64.b64encode(cryptocode.encrypt("{}|change|{}".format(m.sender.address, epoch), "Mega Puffin 5000").encode('ascii')).decode("ascii"),
    }
    template = render_to_string('emailadmin/public_request_email.html', dict)
    print("sending reply message")
    reply_msg = m.reply()
    reply_msg.body = template
    try:
        reply_msg.send()
    except:
        pass
    m.mark_as_read()