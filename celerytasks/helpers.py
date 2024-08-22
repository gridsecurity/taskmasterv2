import io
import pandas as pd
from .conn import *
from datetime import date
from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext


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