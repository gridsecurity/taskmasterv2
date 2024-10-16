from django.urls import re_path
from . import views

app_name='celerytasks'

urlpatterns = [
    re_path(r'^celery/process_emails/$', views.index, name='index'),
    re_path(r'^celery/send_emails/$', views.send_email, name="send_email"),
    re_path(r'^celery/request_tickets/$', views.process_requests, name="process_request_emails"),
    re_path(r'^celery/id_asset_dump/$', views.id_dump, name="id_dump"),
    re_path(r'^celery/ninja_one_dump/$', views.ninja_one_dumps, name="ninja_one_dump"),
    re_path(r'^celery/auvik_dump/$', views.auvik_dumps, name="auvik_dumps"),
    re_path(r'^celery/dump_assets/$', views.dump_assets, name="dump_assets"),
    re_path(r'^celery/global_software_creations', views.global_software_creations, name="global_software_creations"),
    re_path(r'^celery/pull_patches/$', views.pull_patches, name="pull_patches"),
    re_path(r'^celery/nri_email/$', views.nri_email_parse, name='nri_email'),
    re_path(r'^celery/pagerduty/$', views.alert_pagerduty, name='pagerduty'),
    re_path(r'^celery/run_daily_ticket_report/$', views.run_daily_ticket_report, name='run_daily_ticket_report'),
    re_path(r'^celery/assets_splunk_cloud/$', views.send_assets_to_splunk, name="splunk_cloud_assets"),
    re_path(r'^celery/repsol_splunk', views.repsol_splunk, name="repsol_splunk"),
    # re_path(r'^celery/provisions/$', views.provisions, name="provisions"),
    re_path(r'^celery/cisa_report', views.cisa_report, name="cisa_report"),
    re_path(r'^celery/clear_temp_folder_s3', views.clear_temp_folder_s3, name="clear_temp_folder_s3"),
    re_path(r'^celery/sync_okta_groups', views.sync_okta_groups, name="sync_okta_groups"),
    re_path(r'^celery/sync_db', views.sync_prod_to_preprod, name="sync_db"),
    
]