# global_software_dump.py

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
        entry = {}
        if isinstance(value, dict):
            for fname in field_names:
                if fname in value:
                    entry[fname] = str(value[fname]).strip()
        else:
            if len(field_names) == 1:
                entry[field_names[0]] = str(value).strip()
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
    
    return [str(v).strip() for v in flattened if v]

def get_value_by_selection(document, selection):

    fields = selection.split('.')
    value = document
    for field in fields:
        if isinstance(value, dict) and field in value:
            value = value[field]
        else:
            return None
    return value
def search_asset_list(doc, config, asset_list):
    for item in asset_list:
        if config["db_link"]["assets_collection_selector"] in item:
            asset_selector_value = item[config["db_link"]["assets_collection_selector"]]
            doc_selector_value = doc[config["db_link"]["selector"]]
            # print(f"Asset: {asset_selector_value} ---> Item: {doc_selector_value}")
            if asset_selector_value == doc_selector_value:
                return [str(item["_id"])]
    return []

        
        
def extract_fields_from_doc(doc, config, asset_list, collection):
    assets=[str(doc['_id'])]
    if config["db_link"]:
        result = search_asset_list(doc, config, asset_list)
        if result:
            assets = result
    software_entries = []
    software_entry = {
        "source": collection,
        "assets": assets,
        "last_seen": datetime.timestamp(datetime.now()),
        "dateCreated": datetime.timestamp(datetime.now())
    }
    for field in config["fields"]:
        extracted_values = get_single_field(doc, field['selection'], field['field'])
        if extracted_values:
            software_entry[field['field']] = extracted_values[0]  # Assuming one value per field
    if 'name' in software_entry and software_entry['name']:
        if validate_software_entry(software_entry):
            software_entries.append(software_entry)
    return software_entries

def validate_software_entry(entry):
    return all(isinstance(key, str) for key in entry.keys())

def process_function_single_call(func, config, asset_list, collection):

    api_call =  func['apiCall']
    fields =  func['fields']

    api_response = api_call()
    if not api_response:
        return []


    if isinstance(api_response, dict):
        api_items = api_response.get('results', [])
    elif isinstance(api_response, list):
        api_items = api_response
    else:
        return []

    total_api_items = len(api_items)
    processed_api_items = 0
    software_entries = []
    for item in api_items:
        assets = []  
        # Extract all specified fields for this item
        extracted = {}
        if config["db_link"]:
            result = search_asset_list(item, config, asset_list)
            if result:
                assets = result
        for field in fields:
            field_value = get_value_by_selection(item, field['selection'])
            if field_value is not None:
                extracted[field['field']] = str(field_value).strip()
        # Include all extracted fields in the software entry
        software_entry = {
            "source": collection,
            "assets": assets,
            "last_seen": datetime.timestamp(datetime.now()),
            "dateCreated": datetime.timestamp(datetime.now()),
            **extracted  # Merge all extracted fields
        }
        # if validate_software_entry(software_entry):
        #     if func['response_comparison'] in response_map:
        #         response_map[func['response_comparison']].append(software_entry)
        #     else:
        #         response_map[func['response_comparison']] = [software_entry]
        if len(assets)>0:
            software_entries.append(software_entry)
        processed_api_items += 1
        print(f"Processed {processed_api_items}/{total_api_items} items from API response.")
    return software_entries
    # Associate software entries with matching documents
    # assets_list = list(db.assets.find({}))
    # total_docs = len(assets_list)
    # processed_docs = 0

    # for doc in assets_list:
    #     matching_software = response_map.get(func['collection_comparison'])
    #     if matching_software:
    #         for software_entry in matching_software:
    #             software_entry_copy = software_entry.copy()
    #             software_entry_copy["assets"] = [str(doc['_id'])]
    #             software_entries.append(software_entry_copy)
    #     processed_docs += 1
    #     print(f"Matched {processed_docs}/{total_docs} documents with API data.")

    # return software_entries


def global_software_dump(collection, config):

    software_entries = []

    total_docs = db[collection].count_documents({})
    processed_docs = 0
    fields = config.get("fields", [])
    functions = config.get("functions", [])
    asset_list = list(db.assets.find({},{"_id":1, "indDefId":1, "ninjaId":1}))
    if fields:
        # projection_fields = {field['selection'].split('.')[0]: 1 for field in config["fields"] if 'selection' in field}
        # projection_fields['_id'] = 1
        results = db[collection].find({})
        
        for doc in results:
            entries = extract_fields_from_doc(doc, config, asset_list, collection)
            software_entries.extend(entries)
            processed_docs += 1
            print(f"Processed {processed_docs}/{total_docs} documents for field-based extraction.")

    if functions:
        for func in functions:
            if func.get("forEach", True):
                entries = process_function_per_document_wrapper(collection, func)
                software_entries.extend(entries)
            else:
                entries = process_function_single_call(func, config, asset_list, collection)
                software_entries.extend(entries)

    return software_entries

def process_function_per_document_wrapper(collection, func):

    param = func.get('param')
    api_call = func.get('apiCall')

    total_func_docs = db[collection].count_documents({})
    processed_func_docs = 0
    software_entries = []

    docs_cursor = db[collection].find({}, {param: 1, '_id': 1})
    for doc in docs_cursor:
        entries = process_function_per_document(doc, func, collection)
        software_entries.extend(entries)
        processed_func_docs += 1
        print(f"Processed {processed_func_docs}/{total_func_docs} documents for function '{api_call.__name__}'.")
    return software_entries

def process_function_per_document(doc, func_config, collection):

    param = func_config['param']
    api_call = func_config['apiCall']
    fields = func_config['fields']

    param_value = doc.get(param)
    if param_value is None:
        return []

    api_response = api_call(param_value)
    if not api_response:
        return []

    software_entries = []
    # Assuming api_response is a list of items
    api_items = api_response if isinstance(api_response, list) else [api_response]
    total_api_items = len(api_items)
    processed_api_items = 0

    for item in api_items:
        # Extract all specified fields for this item
        extracted = {}
        for field in fields:
            field_value = get_value_by_selection(item, field['selection'])
            if field_value is not None:
                extracted[field['field']] = str(field_value).strip()
        if 'name' not in extracted or not extracted['name']:
            continue
        # Include all extracted fields in the software entry
        software_entry = {
            "source": collection,
            "assets": [str(doc['_id'])],
            "last_seen": datetime.timestamp(datetime.now()),
            "dateCreated": datetime.timestamp(datetime.now()),
            **extracted  # Merge all extracted fields
        }
        if validate_software_entry(software_entry):
            software_entries.append(software_entry)
        processed_api_items += 1
        print(f"Processed {processed_api_items}/{total_api_items} items from API response for document '{doc['_id']}'.")

    return software_entries

