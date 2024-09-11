import io
import pandas as pd
from .conn import *
from datetime import date
from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext
from s3 import S3_DB
import os

def convert_tickets_to_excel(tickets):
    df = pd.DataFrame.from_records(list(tickets))
    df["updated"] = pd.to_datetime(df["updated"], unit="s")
    df["submitdate"] = pd.to_datetime(df["submitdate"], unit="s")
    if "startDate" in df:
        df["startDate"] = pd.to_datetime(df["startDate"], unit="s")
    if "endDate" in df:
        df["endDate"] = pd.to_datetime(df["endDate"], unit="s")
    excelFile = io.BytesIO()
    writer = pd.ExcelWriter(excelFile, engine="xlsxwriter")
    df.to_excel(writer, sheet_name="Tickets")
    workbook = writer.book
    workbook.close()
    excelFile.seek(0)
    return excelFile

def upload_to_sharepoint(excel_file, path):
    site_url = 'https://gridsec.sharepoint.com/sites/Portal.Grid.Security'
    client_credentials = UserCredential('reports@gridsec.com', '2KxCbsxMTueVXy')
    ctx = ClientContext(site_url).with_credentials(client_credentials)
    target_folder = ctx.web.get_folder_by_server_relative_url(path)
    target_folder.upload_file('{}.xlsx'.format(date.today()), excel_file).execute_query()


def rename_images_to_be_unique(file_name, path):
    original_filename = file_name
    base_name, file_extension = os.path.splitext(original_filename)
    
    # Get bucket items
    s3 = S3_DB()
    items = s3.list_bucket_items(s3.ticket_bucket, path)
    
    # Extract existing filenames in the bucket
    existing_files = []
    for item in items:
        existing_files.append(os.path.basename(item.key))
    
    # Start with the original filename
    new_filename = original_filename
    counter = 0
    
    # Check if the filename already exists
    while new_filename in existing_files:
        counter += 1
        new_filename = f"{base_name}({counter}){file_extension}"
    
    return new_filename