from PyPDF2 import PdfReader


def get_embedded_files(fileName):
    attachments = {}
    reader = PdfReader(fileName)
    if reader.is_encrypted:
        reader.decrypt("j2Pao0yGNkeosUmYBt!")
        for pagenum in range(0, len(reader.pages)):
            page_object = reader.pages[pagenum]
            if "/Annots" in page_object:
                for annot in page_object['/Annots']:
                        annotobj = annot.get_object()
                        if annotobj['/Subtype'] == '/FileAttachment':
                            fileobj = annotobj["/FS"]
                            attachments[fileobj["/F"]] = fileobj["/EF"]["/F"].get_data()

    for filename, data in attachments.items():
        if ".csv" in filename:
            with open(filename, "wb") as outfile:
                outfile.write(data)
    return attachments