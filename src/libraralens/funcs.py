import xml.etree.ElementTree as ET

def remove_namespaces(root: ET.Element) -> ET.Element:

    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    return root