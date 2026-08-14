import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom


# ============================================================
# BPMN 2.0 NAMESPACES
# ============================================================

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"

ET.register_namespace("bpmn", BPMN_NS)
ET.register_namespace("bpmndi", BPMNDI_NS)
ET.register_namespace("dc", DC_NS)
ET.register_namespace("di", DI_NS)


def q(ns, tag):
    """Qualified XML tag."""
    return f"{{{ns}}}{tag}"


# ============================================================
# BPMN GENERATOR
# ============================================================

class BPMNGenerator:

    def __init__(self, process_name="EthicalProcess"):

        self.process_name = self.clean_id(process_name)

        self.node_counter = 0
        self.flow_counter = 0

        self.root = None
        self.process = None

        self.elements = {}
        self.flows = []

        # Layout
        self.positions = {}
        self.next_x = 150
        self.next_y = 150

    # ========================================================
    # HELPERS
    # ========================================================

    def clean_id(self, value):

        value = re.sub(r"[^A-Za-z0-9_]", "_", str(value))

        if not value:
            value = "Process"

        if value[0].isdigit():
            value = "id_" + value

        return value

    def new_id(self, prefix):

        self.node_counter += 1

        return f"{prefix}_{self.node_counter}"

    # ========================================================
    # BPMN ELEMENT
    # ========================================================

    def add_element(self, tag, name=None):

        element_id = self.new_id(tag)

        attrs = {"id": element_id}

        if name is not None:
            attrs["name"] = str(name)

        element = ET.SubElement(
            self.process,
            q(BPMN_NS, tag),
            attrs
        )

        self.elements[element_id] = element

        # simple layout
        self.positions[element_id] = (
            self.next_x,
            self.next_y
        )

        self.next_x += 180

        if self.next_x > 1400:
            self.next_x = 150
            self.next_y += 180

        return element_id

    # ========================================================
    # FLOW
    # ========================================================

    def add_flow(self, source, target, name=None):

        self.flow_counter += 1

        flow_id = f"Flow_{self.flow_counter}"

        attrs = {
            "id": flow_id,
            "sourceRef": source,
            "targetRef": target
        }

        if name:
            attrs["name"] = str(name)

        ET.SubElement(
            self.process,
            q(BPMN_NS, "sequenceFlow"),
            attrs
        )

        self.flows.append(
            (flow_id, source, target)
        )

        return flow_id

    # ========================================================
    # DOCUMENTATION
    # ========================================================

    def add_documentation(self, element_id, text):

        if not text:
            return

        element = self.elements[element_id]

        doc = ET.SubElement(
            element,
            q(BPMN_NS, "documentation")
        )

        doc.text = str(text)

    # ========================================================
    # PROCESS TREE HELPERS
    # ========================================================

    def operator_name(self, node):

        op = getattr(node, "operator", None)

        if op is None:
            return None

        name = getattr(op, "name", str(op)).lower()

        if "sequence" in name:
            return "sequence"

        if "xor" in name:
            return "xor"

        if "parallel" in name or name == "and":
            return "and"

        if "loop" in name:
            return "loop"

        return name

    def children(self, node):

        return list(
            getattr(node, "children", [])
        )

    # ========================================================
    # PROCESS TREE -> BPMN
    # ========================================================

    def convert_node(self, node):

        op = self.operator_name(node)
        children = self.children(node)

        # ----------------------------------------------------
        # LEAF
        # ----------------------------------------------------

        if op is None:

            task = self.add_element(
                "task",
                getattr(node, "label", str(node))
            )

            return task, [task]

        # ----------------------------------------------------
        # SEQUENCE
        # ----------------------------------------------------

        if op == "sequence":

            fragments = [
                self.convert_node(child)
                for child in children
            ]

            entry = fragments[0][0]
            exits = fragments[0][1]

            for child_entry, child_exits in fragments[1:]:

                for exit_node in exits:
                    self.add_flow(
                        exit_node,
                        child_entry
                    )

                exits = child_exits

            return entry, exits

        # ----------------------------------------------------
        # XOR
        # ----------------------------------------------------

        if op == "xor":

            split = self.add_element(
                "exclusiveGateway"
            )

            join = self.add_element(
                "exclusiveGateway"
            )

            for child in children:

                child_entry, child_exits = (
                    self.convert_node(child)
                )

                self.add_flow(
                    split,
                    child_entry
                )

                for exit_node in child_exits:

                    self.add_flow(
                        exit_node,
                        join
                    )

            return split, [join]

        # ----------------------------------------------------
        # AND
        # ----------------------------------------------------

        if op == "and":

            split = self.add_element(
                "parallelGateway"
            )

            join = self.add_element(
                "parallelGateway"
            )

            for child in children:

                child_entry, child_exits = (
                    self.convert_node(child)
                )

                self.add_flow(
                    split,
                    child_entry
                )

                for exit_node in child_exits:

                    self.add_flow(
                        exit_node,
                        join
                    )

            return split, [join]

        # ----------------------------------------------------
        # LOOP
        # ----------------------------------------------------

        if op == "loop":

            body_entry, body_exits = (
                self.convert_node(children[0])
            )

            gateway = self.add_element(
                "exclusiveGateway"
            )

            for exit_node in body_exits:

                self.add_flow(
                    exit_node,
                    gateway
                )

            self.add_flow(
                gateway,
                body_entry,
                "تکرار"
            )

            return body_entry, [gateway]

        # fallback
        return self.convert_node(children[0])

    # ========================================================
    # BPMN DIAGRAM INTERCHANGE
    # ========================================================

    def create_diagram(self, process_id):

        diagram = ET.SubElement(
            self.root,
            q(BPMNDI_NS, "BPMNDiagram"),
            {"id": "BPMNDiagram_1"}
        )

        plane = ET.SubElement(
            diagram,
            q(BPMNDI_NS, "BPMNPlane"),
            {
                "id": "BPMNPlane_1",
                "bpmnElement": process_id
            }
        )

        # Shapes
        for element_id, element in self.elements.items():

            x, y = self.positions[element_id]

            tag = element.tag.split("}")[-1]

            if "Gateway" in tag:
                width = height = 50

            elif tag in ("startEvent", "endEvent"):
                width = height = 36

            else:
                width = 120
                height = 80

            shape = ET.SubElement(
                plane,
                q(BPMNDI_NS, "BPMNShape"),
                {
                    "id": f"{element_id}_di",
                    "bpmnElement": element_id
                }
            )

            ET.SubElement(
                shape,
                q(DC_NS, "Bounds"),
                {
                    "x": str(x),
                    "y": str(y),
                    "width": str(width),
                    "height": str(height)
                }
            )

        # Edges
        for flow_id, source, target in self.flows:

            sx, sy = self.positions[source]
            tx, ty = self.positions[target]

            edge = ET.SubElement(
                plane,
                q(BPMNDI_NS, "BPMNEdge"),
                {
                    "id": f"{flow_id}_di",
                    "bpmnElement": flow_id
                }
            )

            ET.SubElement(
                edge,
                q(DI_NS, "waypoint"),
                {
                    "x": str(sx + 120),
                    "y": str(sy + 40)
                }
            )

            ET.SubElement(
                edge,
                q(DI_NS, "waypoint"),
                {
                    "x": str(tx),
                    "y": str(ty + 40)
                }
            )

    # ========================================================
    # GENERATE
    # ========================================================

    def generate(
        self,
        process_tree,
        ethical_notes=None,
        output_path="output/process_model_ethical.bpmn"
    ):

        ethical_notes = ethical_notes or {}

        # Root
        self.root = ET.Element(
            q(BPMN_NS, "definitions"),
            {
                "id": "Definitions_1",
                "targetNamespace": "http://ethical-abpms"
            }
        )

        process_id = (
            f"Process_{self.process_name}"
        )

        self.process = ET.SubElement(
            self.root,
            q(BPMN_NS, "process"),
            {
                "id": process_id,
                "name": self.process_name,
                "isExecutable": "true"
            }
        )

        # Start
        start = self.add_element(
            "startEvent",
            "شروع"
        )

        # Tree
        entry, exits = self.convert_node(
            process_tree
        )

        self.add_flow(
            start,
            entry
        )

        # End
        end = self.add_element(
            "endEvent",
            "پایان"
        )

        for exit_node in exits:

            self.add_flow(
                exit_node,
                end
            )

        # Ethical documentation
        for element_id, element in self.elements.items():

            name = element.get("name")

            if name in ethical_notes:

                self.add_documentation(
                    element_id,
                    ethical_notes[name]
                )

        # Diagram
        self.create_diagram(
            process_id
        )

        # Save
        directory = os.path.dirname(
            output_path
        )

        if directory:

            os.makedirs(
                directory,
                exist_ok=True
            )

        xml_bytes = ET.tostring(
            self.root,
            encoding="utf-8",
            xml_declaration=True
        )

        pretty = minidom.parseString(
            xml_bytes
        ).toprettyxml(
            indent="  ",
            encoding="utf-8"
        )

        with open(
            output_path,
            "wb"
        ) as f:

            f.write(pretty)

        return output_path
