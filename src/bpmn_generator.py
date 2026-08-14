"""
BPMN 2.0 Generator

تبدیل واقعی Process Tree حاصل از PM4Py
به BPMN 2.0 XML

پشتیبانی:
- SEQUENCE
- XOR
- AND
- LOOP
- Task
- Start Event
- End Event
- BPMN Documentation
- BPMN DI
"""

import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom


class BPMNGenerator:

    BPMN_NS = (
        "http://www.omg.org/spec/BPMN/20100524/MODEL"
    )

    BPMNDI_NS = (
        "http://www.omg.org/spec/BPMN/20100524/DI"
    )

    DC_NS = (
        "http://www.omg.org/spec/DD/20100524/DC"
    )

    DI_NS = (
        "http://www.omg.org/spec/DD/20100524/DI"
    )

    def __init__(
        self,
        process_name="EthicalProcess"
    ):

        self.process_name = self._clean_id(
            process_name
        )

        self.node_counter = 0
        self.flow_counter = 0

        self.root = None
        self.process = None

        self.elements = {}
        self.flows = []

        # موقعیت‌ها
        self.positions = {}

    # ============================================================
    # ID
    # ============================================================

    def _clean_id(self, text):

        text = re.sub(
            r"[^a-zA-Z0-9_]",
            "_",
            str(text)
        )

        if not text:
            text = "Process"

        if text[0].isdigit():
            text = "id_" + text

        return text

    def _new_id(self, prefix):

        self.node_counter += 1

        return (
            f"{prefix}_{self.node_counter:03d}"
        )

    # ============================================================
    # ELEMENTS
    # ============================================================

    def _add_element(
        self,
        tag,
        attrs
    ):

        if "id" not in attrs:
            attrs["id"] = self._new_id(
                tag.split(":")[-1]
            )

        element = ET.SubElement(
            self.process,
            tag,
            attrs
        )

        self.elements[
            attrs["id"]
        ] = element

        return attrs["id"]

    # ============================================================
    # DOCUMENTATION
    # ============================================================

    def _add_documentation(
        self,
        element_id,
        text
    ):

        if not text:
            return

        element = self.elements.get(
            element_id
        )

        if element is None:
            return

        documentation = ET.SubElement(
            element,
            "bpmn:documentation"
        )

        documentation.text = str(text)

    # ============================================================
    # FLOW
    # ============================================================

    def _add_flow(
        self,
        source,
        target,
        name=None
    ):

        self.flow_counter += 1

        flow_id = (
            f"Flow_{self.flow_counter:03d}"
        )

        attrs = {
            "id": flow_id,
            "sourceRef": source,
            "targetRef": target
        }

        if name:
            attrs["name"] = str(name)

        flow = ET.SubElement(
            self.process,
            "bpmn:sequenceFlow",
            attrs
        )

        self.flows.append(
            (
                flow_id,
                source,
                target
            )
        )

        return flow_id

    # ============================================================
    # PROCESS TREE TYPE
    # ============================================================

    def _operator_name(
        self,
        node
    ):

        operator = getattr(
            node,
            "operator",
            None
        )

        if operator is None:
            operator = getattr(
                node,
                "_operator",
                None
            )

        if operator is None:
            return None

        value = getattr(
            operator,
            "name",
            str(operator)
        )

        value = str(value).lower()

        if "sequence" in value:
            return "sequence"

        if "xor" in value:
            return "xor"

        if "parallel" in value:
            return "and"

        if value == "and":
            return "and"

        if "loop" in value:
            return "loop"

        return value

    def _children(
        self,
        node
    ):

        children = getattr(
            node,
            "children",
            None
        )

        if children is None:
            children = getattr(
                node,
                "_children",
                []
            )

        return list(children)

    def _label(
        self,
        node
    ):

        label = getattr(
            node,
            "label",
            None
        )

        if label is None:
            label = str(node)

        return str(label)

    # ============================================================
    # PROCESS TREE → BPMN
    # ============================================================

    def _convert_tree(
        self,
        node
    ):
        """
        تبدیل یک Node از Process Tree
        به یک fragment از BPMN.

        خروجی:
            (entry_node, exit_nodes)
        """

        operator = self._operator_name(
            node
        )

        children = self._children(
            node
        )

        # --------------------------------------------------------
        # LEAF = TASK
        # --------------------------------------------------------

        if operator is None:

            task_id = self._add_element(
                "bpmn:task",
                {
                    "id": self._new_id(
                        "Activity"
                    ),
                    "name": self._label(node)
                }
            )

            return task_id, [task_id]

        # --------------------------------------------------------
        # SEQUENCE
        # --------------------------------------------------------

        if operator == "sequence":

            if not children:
                return None, []

            fragments = [
                self._convert_tree(child)
                for child in children
            ]

            entry = fragments[0][0]

            previous_exits = fragments[0][1]

            for entry_child, exits_child in fragments[1:]:

                if entry_child is None:
                    continue

                for previous in previous_exits:

                    self._add_flow(
                        previous,
                        entry_child
                    )

                previous_exits = exits_child

            return (
                entry,
                previous_exits
            )

        # --------------------------------------------------------
        # XOR
        # --------------------------------------------------------

        if operator == "xor":

            gateway_id = self._add_element(
                "bpmn:exclusiveGateway",
                {
                    "id": self._new_id(
                        "ExclusiveGateway"
                    ),
                    "gatewayDirection":
                        "Diverging"
                }
            )

            exits = []

            for child in children:

                child_entry, child_exits = (
                    self._convert_tree(child)
                )

                if child_entry is None:
                    continue

                self._add_flow(
                    gateway_id,
                    child_entry
                )

                exits.extend(
                    child_exits
                )

            return gateway_id, exits

        # --------------------------------------------------------
        # AND / PARALLEL
        # --------------------------------------------------------

        if operator == "and":

            gateway_id = self._add_element(
                "bpmn:parallelGateway",
                {
                    "id": self._new_id(
                        "ParallelGateway"
                    ),
                    "gatewayDirection":
                        "Diverging"
                }
            )

            exits = []

            for child in children:

                child_entry, child_exits = (
                    self._convert_tree(child)
                )

                if child_entry is None:
                    continue

                self._add_flow(
                    gateway_id,
                    child_entry
                )

                exits.extend(
                    child_exits
                )

            return gateway_id, exits

        # --------------------------------------------------------
        # LOOP
        # --------------------------------------------------------

        if operator == "loop":

            if not children:
                return None, []

            body_entry, body_exits = (
                self._convert_tree(
                    children[0]
                )
            )

            if body_entry is None:
                return None, []

            gateway_id = self._add_element(
                "bpmn:exclusiveGateway",
                {
                    "id": self._new_id(
                        "LoopGateway"
                    ),
                    "gatewayDirection":
                        "Diverging"
                }
            )

            self._add_flow(
                gateway_id,
                body_entry,
                "ادامه حلقه"
            )

            # مسیر برگشت
            for exit_node in body_exits:

                self._add_flow(
                    exit_node,
                    gateway_id,
                    "تکرار"
                )

            return (
                gateway_id,
                [gateway_id]
            )

        # --------------------------------------------------------
        # UNKNOWN
        # --------------------------------------------------------

        if children:

            return self._convert_tree(
                children[0]
            )

        return None, []

    # ============================================================
    # ETHICAL GATEWAYS
    # ============================================================

    def _add_ethical_documentation(
        self,
        ethical_notes
    ):

        if not ethical_notes:
            return

        for element_id, element in self.elements.items():

            name = element.get(
                "name",
                ""
            )

            if name in ethical_notes:

                self._add_documentation(
                    element_id,
                    ethical_notes[name]
                )

    # ============================================================
    # BPMN DI
    # ============================================================

    def _create_diagram(self):

        diagram = ET.SubElement(
            self.root,
            "bpmndi:BPMNDiagram",
            {
                "id":
                    "BPMNDiagram_1"
            }
        )

        plane = ET.SubElement(
            diagram,
            "bpmndi:BPMNPlane",
            {
                "id":
                    "BPMNPlane_1",
                "bpmnElement":
                    self.process.get("id")
            }
        )

        # --------------------------------------------------------
        # Node positions
        # --------------------------------------------------------

        x = 100
        y = 200

        for element_id, element in (
            self.elements.items()
        ):

            tag = element.tag.split(
                "}"
            )[-1]

            if "Gateway" in element_id:
                width = 50
                height = 50

            elif tag in [
                "startEvent",
                "endEvent"
            ]:
                width = 36
                height = 36

            else:
                width = 120
                height = 80

            shape = ET.SubElement(
                plane,
                "bpmndi:BPMNShape",
                {
                    "id":
                        f"BPMNShape_{element_id}",
                    "bpmnElement":
                        element_id
                }
            )

            ET.SubElement(
                shape,
                "dc:Bounds",
                {
                    "x": str(x),
                    "y": str(y),
                    "width": str(width),
                    "height": str(height)
                }
            )

            x += 180

            if x > 1300:
                x = 100
                y += 150

        # --------------------------------------------------------
        # Flow DI
        # --------------------------------------------------------

        for flow_id, source, target in self.flows:

            edge = ET.SubElement(
                plane,
                "bpmndi:BPMNEdge",
                {
                    "id":
                        f"BPMNEdge_{flow_id}",
                    "bpmnElement":
                        flow_id
                }
            )

            # برای Import شدن BPMN
            # Waypointهای ساده ایجاد می‌کنیم.
            ET.SubElement(
                edge,
                "di:waypoint",
                {
                    "x": "100",
                    "y": "200"
                }
            )

            ET.SubElement(
                edge,
                "di:waypoint",
                {
                    "x": "200",
                    "y": "200"
                }
            )

    # ============================================================
    # GENERATE
    # ============================================================

    def generate(
        self,
        process_tree,
        ethical_notes=None,
        output_path=
            "output/process_model_ethical.bpmn"
    ):
        """
        تولید BPMN 2.0 XML واقعی از Process Tree.
        """

        if process_tree is None:

            raise ValueError(
                "Process Tree وجود ندارد."
            )

        ethical_notes = (
            ethical_notes or {}
        )

        # Namespace
        ET.register_namespace(
            "bpmn",
            self.BPMN_NS
        )

        ET.register_namespace(
            "bpmndi",
            self.BPMNDI_NS
        )

        ET.register_namespace(
            "dc",
            self.DC_NS
        )

        ET.register_namespace(
            "di",
            self.DI_NS
        )

        # --------------------------------------------------------
        # Definitions
        # --------------------------------------------------------

        self.root = ET.Element(
            "bpmn:definitions",
            {
                "id":
                    "Definitions_1",
                "targetNamespace":
                    "http://bpmn.io/schema/bpmn"
            }
        )

        # --------------------------------------------------------
        # Process
        # --------------------------------------------------------

        process_id = (
            f"Process_{self.process_name}"
        )

        self.process = ET.SubElement(
            self.root,
            "bpmn:process",
            {
                "id":
                    process_id,
                "name":
                    self.process_name,
                "isExecutable":
                    "true"
            }
        )

        # --------------------------------------------------------
        # Start
        # --------------------------------------------------------

        start_id = self._add_element(
            "bpmn:startEvent",
            {
                "id":
                    "StartEvent_1",
                "name":
                    "شروع"
            }
        )

        # --------------------------------------------------------
        # Process Tree
        # --------------------------------------------------------

        entry_id, exit_ids = (
            self._convert_tree(
                process_tree
            )
        )

        if entry_id is None:
            raise ValueError(
                "Process Tree به BPMN تبدیل نشد."
            )

        # Start → Process
        self._add_flow(
            start_id,
            entry_id
        )

        # --------------------------------------------------------
        # End
        # --------------------------------------------------------

        end_id = self._add_element(
            "bpmn:endEvent",
            {
                "id":
                    "EndEvent_1",
                "name":
                    "پایان"
            }
        )

        # Process → End
        for exit_id in exit_ids:

            self._add_flow(
                exit_id,
                end_id
            )

        # --------------------------------------------------------
        # Ethical Documentation
        # --------------------------------------------------------

        self._add_ethical_documentation(
            ethical_notes
        )

        # --------------------------------------------------------
        # BPMN DI
        # --------------------------------------------------------

        self._create_diagram()

        # --------------------------------------------------------
        # Save
        # --------------------------------------------------------

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
            encoding="utf-8"
        )

        dom = minidom.parseString(
            xml_bytes
        )

        pretty_xml = dom.toprettyxml(
            indent="  ",
            encoding="utf-8"
        )

        with open(
            output_path,
            "wb"
        ) as file:

            file.write(
                pretty_xml
            )

        return output_path
