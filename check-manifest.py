#!/usr/bin/env python

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

from dataclasses import dataclass, field
import xml.etree.ElementTree as ET
from typing import Any, Dict


@dataclass
class HalRecord:
    """
    Represents a HAL record with its parsed dictionary form and raw XML.
    """
    name: str
    raw_xml: str
    element: ET.Element
    parsed_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_element(cls, element: ET.Element):
        """
        Create a HalRecord from an XML element.
        """
        name = element.findtext("name")
        raw_xml = ET.tostring(element, encoding="unicode")
        parsed_data = cls._parse_element_recursively(element)
        return cls(name=name, raw_xml=raw_xml, element=element, parsed_data=parsed_data)

    @staticmethod
    def _parse_element_recursively(element: ET.Element) -> Dict[str, Any]:
        """
        Recursively parse an XML element into a dictionary.
        """
        parsed = {element.tag: {} if element.attrib else None}
        children = list(element)
        
        if children:
            # If the element has children, process them recursively
            child_data = {}
            for child in children:
                child_parsed = HalRecord._parse_element_recursively(child)
                child_tag = child.tag
                if child_tag not in child_data:
                    child_data[child_tag] = []
                child_data[child_tag].append(child_parsed[child_tag])
            parsed[element.tag] = child_data
        elif element.text:
            # If the element has text, include it
            parsed[element.tag] = element.text.strip()
        else:
            # Otherwise, keep it as None (empty element)
            parsed[element.tag] = None

        # Add attributes, if any
        if element.attrib:
            parsed[element.tag]["@attributes"] = element.attrib

        return parsed

    def __eq__(self, other):
        """
        Compare two HalRecord objects for semantic equality.
        Ignores formatting differences.
        """
        if not isinstance(other, HalRecord):
            return NotImplemented
        return self.parsed_data == other.parsed_data

    def __repr__(self):
        """
        String representation for debugging.
        """
        return f"HalRecord(name={self.name}, parsed_data={self.parsed_data})"



def parse_manifest(manifest_path):
    """
    Parse a manifest file and extract its type, version, target-level, and HAL records.
    """
    tree = ET.parse(manifest_path)
    root = tree.getroot()

    # Extract manifest properties
    manifest_type = root.attrib.get("type")
    manifest_version = root.attrib.get("version")
    target_level = root.attrib.get("target-level")

    # Extract HAL records
    hal_records = []
    for hal in root.findall("hal"):
        record = HalRecord.from_element(hal)
        hal_records.append(record)

    return manifest_type, manifest_version, target_level, hal_records


def preload_stock_manifests(stock_tree_path, type_to_load):
    """
    Load all stock manifests into memory, grouped by type.
    """
    stock_manifests = []
    stock_tree_path = Path(stock_tree_path)

    for manifest_file in stock_tree_path.rglob("*.xml"):
        try:
            tree = ET.parse(manifest_file)
            root = tree.getroot()
            manifest_type = root.attrib.get("type")

            if manifest_type != type_to_load:
                continue

            print(f"Loading {manifest_file}")

            m = [HalRecord.from_element(hal) for hal in root.findall("hal")]
            stock_manifests.append(dict(file=manifest_file, hal_records=m))
        except: # ET.ParseError:
            print(f"Warning: Failed to parse {manifest_file}")
            continue

    return stock_manifests


def find_matching_hal(stock_manifests, hal_name):
    """
    Find a matching HAL record in the preloaded stock manifests.
    """
    for manifest in stock_manifests:
        for srec in manifest["hal_records"]:
            if hal_name == srec.name:
                return srec, manifest["file"]

    return None, None


def combine_elements(my_manifest_path, elements_to_combine, output_path):
    """
    Combine a list of elements into a new XML using the root from my_manifest.

    Args:
        my_manifest_path (str): Path to the source manifest file.
        elements_to_combine (list of ET.Element): List of elements to include in the output.
        output_path (str): Path to the output XML file.
    """
    # Parse my_manifest to get the root
    my_manifest_tree = ET.parse(my_manifest_path)
    root = my_manifest_tree.getroot()

    # Remove all existing children from the root
    for child in list(root):
        root.remove(child)

    # Append new elements from the provided list
    for element in elements_to_combine:
        root.append(element)

    # Write the updated tree to the output file
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"Combined XML written to {output_path}")


def main(my_manifest, stock_tree, output):
    my_manifest_path = Path(my_manifest)
    if not my_manifest_path.exists():
        print(f"Error: {my_manifest} does not exist.")
        return

    stock_tree_path = Path(stock_tree)
    if not stock_tree_path.exists():
        print(f"Error: {stock_tree} does not exist.")
        return

    # Parse my manifest
    my_type, my_version, my_target_level, my_hal_records = parse_manifest(my_manifest_path)
    print(f"My manifest type: {my_type}, version: {my_version}, target-level: {my_target_level}")

    # Preload all stock manifests
    print("Preloading stock manifests...")
    stock_manifests = preload_stock_manifests(stock_tree_path, my_type)

    print()

    matched = 0
    elements = []
    for hal in my_hal_records:
        srec, stock_fname = find_matching_hal(stock_manifests, hal.name)
        if srec is None:
            print(f"HAL: {hal.name} - Not found on stock")
            elements.append(hal.element)
        elif srec != hal:
            print(f"HAL: {hal.name} - Mismatch")
            print(f"Found in: {stock_fname}")
            # print('My manifest:\n', hal.raw_xml)
            # print()
            # print('Stock:\n', srec.raw_xml)
            print()
            elements.append(srec.element)
        else:
            matched += 1
            elements.append(hal.element)

    print()
    print(f'Total chacked records: {len(my_hal_records)}')
    print(f"Matching records: {matched}")
    print(f"Mismatched records: {len(my_hal_records) - matched}")

    combine_elements(my_manifest_path, elements, output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare HAL records between two manifests.")
    parser.add_argument("my_manifest", type=str, help="Path to the manifest.xml file.")
    parser.add_argument("stock_tree", type=str, help="Path to the stock ROM tree.")
    parser.add_argument("output", type=str, help="Path to the combined manifest.xml file.")
    args = parser.parse_args()
    main(args.my_manifest, args.stock_tree, args.output)
