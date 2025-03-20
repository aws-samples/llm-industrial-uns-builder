import untangle

def tia_db_export_to_entries(tia_db_xml_export: str) -> [[]]:
    rows = []
    tia_export = untangle.parse(tia_db_xml_export)
    print(tia_export)
    dbs = [db for db in tia_export.Document.children if db._name == 'SW_Blocks_GlobalDB']
    for db in dbs:
        db_name = db.AttributeList.Name.cdata
        db_number = db.AttributeList.Number.cdata
        print(f"DB Name: {db_name}")
        print(f"DB Number: {db_number}")
        for section in db.AttributeList.Interface.Sections.children:
            print(f"Section Name: {section['Name']}")
            for member in section.children:
                for child in member.children:
                    if child._name == "AttributeList":
                        # offset_integer_attributes = [attr for attr in member.AttributeList.children if
                        #                              attr._name == 'IntegerAttribute' and attr['Name'] == 'Offset']
                        # offset: int = int(offset_integer_attributes[0].cdata.strip()) if len(offset_integer_attributes) > 0 else -1
                        # print("attr?")
                        # print(child)
                        offset: int = int(child.children[0].cdata.strip())
                        comments = []
                        comment_outer_elements = [comment for comment in member.children if comment._name == 'Comment']
                        for comment_element in comment_outer_elements:
                            for language_text in member.Comment.MultiLanguageText:
                                comments.append({
                                    "text": language_text.cdata.strip(),
                                    "lang": language_text['Lang']
                                })
                        start_values = [start_value for start_value in member.children if start_value._name == 'StartValue']
                        start_value = start_values[0].cdata if len(start_values) > 0 else None
                        print(f"entry: Name: {member['Name']} Datatype: {member['Datatype']} Offset: {offset} " +
                              f"StartValue: {start_value} Comments: {comments}")
                        rows.append({
                            "name": member['Name'],
                            "db_number": db_number,
                            "offset": offset,
                            "datatype": member['Datatype']
                        })
                    else:
                        print("no attribute")
                        print(member["AttributeList"])
                        print(member)
    return rows