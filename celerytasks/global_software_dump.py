from .conn import db
from bson import ObjectId
from datetime import datetime

def get_nested_fields(document, selection, field_names):
    fields = selection.split('.')
    values = [document]
    for field in fields:
        temp = []
        for value in values:
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and field in item:
                        temp.append(item[field])
            elif isinstance(value, dict) and field in value:
                temp.append(value[field])
        values = temp
        if not values:
            return []
    flattened = []
    for value in values:
        if isinstance(value, list):
            flattened.extend(value)
        else:
            flattened.append(value)
    results = []
    for value in flattened:
        if not isinstance(value, dict):
            continue
        entry = {}
        for fname in field_names:
            if fname in value:
                entry[fname] = str(value[fname]).strip()
        if entry:
            results.append(entry)
    return results

def get_single_field(document, selection, field_name):
    fields = selection.split('.')
    values = [document]
    for field in fields:
        temp = []
        for value in values:
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and field in item:
                        temp.append(item[field])
            elif isinstance(value, dict) and field in value:
                temp.append(value[field])
        values = temp
        if not values:
            return []
    flattened = []
    for value in values:
        if isinstance(value, list):
            flattened.extend(value)
        else:
            flattened.append(value)
    result = [str(v).strip() for v in flattened if v]
    return result

def global_software_dump(collection, fields):
    projection = {}
    for field in fields:
        top_field = field['selection'].split('.')[0]
        projection[top_field] = 1
    projection['_id'] = 1
    result = db[collection].find({}, projection) 
    
    software_entries = []
    for doc in result:
        for field in fields:
            if 'field_names' in field:
                extracted_fields = get_nested_fields(doc, field['selection'], field['field_names'])
                if not extracted_fields:
                    continue
                for extracted in extracted_fields:
                    if 'name' not in extracted or not extracted['name']:
                        continue
                    software_entry = {
                        "name": extracted["name"],
                        "source": collection,
                        "assets": [str(doc['_id'])],
                        "last_seen": datetime.timestamp(datetime.today()),
                        "dateCreated": datetime.timestamp(datetime.today())
                    }
                    for key, value in extracted.items():
                        if key != "name":
                            software_entry[key] = value
                    software_entries.append(software_entry)
            elif 'field' in field:
                extracted_values = get_single_field(doc, field['selection'], field['field'])
                if not extracted_values:
                    continue
                for value in extracted_values:
                    if not value:
                        continue
                    software_entry = {
                        "name": value,
                        "source": collection,
                        "assets": [str(doc['_id'])],
                        "last_seen": datetime.timestamp(datetime.today()),
                        "dateCreated": datetime.timestamp(datetime.today())
                    }
                    software_entries.append(software_entry)
    return software_entries
