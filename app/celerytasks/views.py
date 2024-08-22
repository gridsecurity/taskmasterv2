from django.shortcuts import HttpResponse
from .tasks import *

# Create your views here.
def index(request):
    process_ticket_emails()
    return HttpResponse('response done')

def send_email(request):
    send_emails()
    return HttpResponse(200)

def process_requests(request):
    process_request_emails()

def nri_email_parse(request):
    nri_email()
    return HttpResponse('response done')

def alert_pagerduty(request):
    pagerduty()
    return HttpResponse('response done')

def id_dump(request):
    id_asset_dump()
    return HttpResponse('Finished dump')

def run_daily_ticket_report(request):
    daily_tickets_report()
    return HttpResponse('done')

def pull_patches(request):
    sync_patches()
    return HttpResponse("Patches Synced")

def send_assets_to_splunk(request):
    splunk_cloud_assets()
    return HttpResponse("Splunk Cloud")

# def provisions(request):
#     access_ticket_provisions()
#     return HttpResponse()

def cisa_report(request):
    process_csa_report()
    return HttpResponse()

def clear_temp_folder_s3(request):
    clear_temp_s3()
    return HttpResponse()

def dump_assets(request):
    asset_dump()
    return HttpResponse("Finished")

def ninja_one_dumps(request):
    ninja_one_dump()
    return HttpResponse("Finished")

def auvik_dumps(request):
    auvik_dump()
    return HttpResponse("Finished")

def sync_okta_groups(request):
    syncOktaGroups()
    return HttpResponse('Finished')

def sync_prod_to_preprod(request):
    sync_db()
    return HttpResponse("Finished")