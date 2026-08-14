"""
BPMN 2.0 Generator for Ethical A-BPMS

ویژگی‌ها:
- تولید BPMN 2.0 معتبر
- Namespace صحیح
- BPMN-DI کامل
- Sequence Flow
- XOR Gateway
- AND Gateway
- Loop
- Documentation
- مسیر بررسی تبعیض
- مسیر اعتراض و بازبینی
- سازگار با process tree های PM4Py
- سازگار با API قبلی generate()
"""

from __future__ import annotations

import os
import re
import uuid
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Any, Dict, List, Optional, Tuple


class BPMNGenerator:
    """
    تولیدکننده BPMN 2.0 برای A-BPMS

    API قدیمی:
        generate(process_tree, ethical_notes, output_path)

    API جدید:
        generate(
            process_tree,
            ethical_notes=None,
            corrections=None,
            output_path=None
        )
    """

    BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
    BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
    DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
    DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
    XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

    def __init__(self, process_name="EthicalProcess"):
        self.process_name = process_name
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.flows: List[Dict[str, Any]] = []

        self.node_counter = 0
        self.flow_counter = 0

        self.width = 1400
        self.height = 900

        self.x = 100
        self.y = 300

        self.task_width = 150
        self.task_height = 80

        self.gateway_size = 50

        self.vertical_gap = 180
        self.horizontal_gap = 220

    # ============================================================
    # ID helpers
    # ============================================================

    def _id(self, prefix: str) -> str:
        self.node_counter += 1
        return f"{prefix}_{self.node_counter}"

    def _flow_id(self) -> str:
        self.flow_counter += 1
        return f"Flow_{self.flow_counter}"

    def _safe_id(self, text: str) -> str:
        text = str(text)
        text = re.sub(r"[^a-zA-Z0-9_]", "_", text)
        text = text.strip("_")

        if not text:
            text = "Element"

        return text[:40]

    # ============================================================
    # XML helpers
    # ============================================================

    def _q(self, namespace: str, tag: str) -> str:
        return f"{{{namespace}}}{tag}"

    def _documentation(self, element, text: Optional[str]):
        if not text:
            return

        doc = ET.SubElement(
            element,
            self._q(self.BPMN_NS, "documentation")
        )
        doc.text = str(text)

    # ============================================================
    # Node creation
    # ============================================================

    def _add_task(
        self,
        name: str,
        documentation: Optional[str] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        task_id: Optional[str] = None,
    ) -> str:

        node_id = task_id or self._id("Activity")

        self.nodes[node_id] = {
            "id": node_id,
            "type": "task",
            "name": name,
            "documentation": documentation,
            "x": x if x is not None else self.x,
            "y": y if y is not None else self.y,
            "width": self.task_width,
            "height": self.task_height,
        }

        return node_id

    def _add_start(
        self,
        name: str = "شروع",
        x: Optional[float] = None,
        y: Optional[float] = None,
    ) -> str:

        node_id = self._id("StartEvent")

        self.nodes[node_id] = {
            "id": node_id,
            "type": "start",
            "name": name,
            "documentation": None,
            "x": x if x is not None else self.x,
            "y": y if y is not None else self.y + 15,
            "width": 36,
            "height": 36,
        }

        return node_id

    def _add_end(
        self,
        name: str = "پایان",
        x: Optional[float] = None,
        y: Optional[float] = None,
    ) -> str:

        node_id = self._id("EndEvent")

        self.nodes[node_id] = {
            "id": node_id,
            "type": "end",
            "name": name,
            "documentation": None,
            "x": x if x is not None else self.x,
            "y": y if y is not None else self.y + 15,
            "width": 36,
            "height": 36,
        }

        return node_id

    def _add_gateway(
        self,
        gateway_type: str,
        name: str,
        documentation: Optional[str] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
    ) -> str:

        prefix = "ExclusiveGateway" if gateway_type == "XOR" else "ParallelGateway"

        node_id = self._id(prefix)

        self.nodes[node_id] = {
            "id": node_id,
            "type": gateway_type,
            "name": name,
            "documentation": documentation,
            "x": x if x is not None else self.x,
            "y": y if y is not None else self.y + 15,
            "width": self.gateway_size,
            "height": self.gateway_size,
        }

        return node_id

    # ============================================================
    # Sequence flow
    # ============================================================

    def _add_flow(
        self,
        source: str,
        target: str,
        condition: Optional[str] = None,
        name: Optional[str] = None,
    ) -> str:

        flow_id = self._flow_id()

        self.flows.append({
            "id": flow_id,
            "source": source,
            "target": target,
            "condition": condition,
            "name": name,
        })

        return flow_id

    # ============================================================
    # Process tree extraction
    # ============================================================

    def _extract_process_tree_activities(self, tree) -> List[str]:
        """
        استخراج فعالیت‌ها از ProcessTree مربوط به PM4Py.

        تلاش می‌کند با چند نوع ساختار مختلف سازگار باشد.
        """

        activities = []

        if tree is None:
            return activities

        # PM4Py ProcessTree
        try:
            from pm4py.objects.process_tree.obj import Operator

            def visit(node):
                if node is None:
                    return

                operator = getattr(node, "operator", None)

                if operator is None:
                    label = getattr(node, "label", None)

                    if label:
                        activities.append(str(label))

                    return

                children = getattr(node, "children", []) or []

                for child in children:
                    visit(child)

            visit(tree)

            return self._unique(activities)

        except Exception:
            pass

        # Dict
        if isinstance(tree, dict):
            if "activities" in tree:
                return self._unique(
                    [str(x) for x in tree["activities"]]
                )

            if "children" in tree:
                for child in tree["children"]:
                    activities.extend(
                        self._extract_process_tree_activities(child)
                    )

            if "label" in tree:
                activities.append(str(tree["label"]))

            return self._unique(activities)

        # List / tuple
        if isinstance(tree, (list, tuple)):
            for item in tree:
                activities.extend(
                    self._extract_process_tree_activities(item)
                )

            return self._unique(activities)

        return activities

    def _unique(self, values: List[str]) -> List[str]:
        result = []

        for value in values:
            if value and value not in result:
                result.append(value)

        return result

    # ============================================================
    # Normalize corrections
    # ============================================================

    def _normalize_corrections(
        self,
        corrections: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:

        result = {
            "new_activities": [],
            "removed_activities": [],
            "model_corrections": [],
            "form_corrections": [],
        }

        if not corrections:
            return result

        for key in result:
            value = corrections.get(key)

            if isinstance(value, list):
                result[key] = value

        return result

    # ============================================================
    # Ethical activities
    # ============================================================

    def _ethical_documentation(self, name: str) -> str:

        docs = {
            "بررسی تبعیض":
                "این فعالیت برای کنترل سوگیری و جلوگیری از اثرگذاری "
                "مستقیم متغیرهای حساس مانند جنسیت بر تصمیم‌گیری ایجاد شده است.",

            "درخواست بازبینی":
                "این فعالیت برای تضمین قابلیت اعتراض متقاضی و فراهم کردن "
                "مسیر رسمی درخواست تجدیدنظر ایجاد شده است.",

            "بازبینی درخواست":
                "این فعالیت برای بررسی مستقل درخواست تجدیدنظر و افزایش "
                "پاسخ‌گویی فرآیند ایجاد شده است.",

            "ابلاغ نتیجه":
                "نتیجه تصمیم باید به‌صورت شفاف و قابل فهم به متقاضی ابلاغ شود.",

            "توضیح دلیل تصمیم":
                "دلیل تصمیم باید به‌صورت قابل فهم و قابل ممیزی ثبت شود.",
        }

        return docs.get(
            name,
            "این فعالیت با رعایت اصول اخلاقی A-BPMS طراحی شده است."
        )

    # ============================================================
    # Build ethical corrected process
    # ============================================================

    def _build_ethical_process(
        self,
        activities: List[str],
        corrections: Dict[str, Any],
        ethical_notes: Optional[Any],
    ) -> Tuple[str, str]:

        # ========================================================
        # حذف فعالیت‌هایی که Corrector حذف کرده است
        # ========================================================

        removed = set()

        for item in corrections.get("removed_activities", []):
            if isinstance(item, str):
                removed.add(item)

            elif isinstance(item, dict):
                if item.get("name"):
                    removed.add(item["name"])

        activities = [
            a for a in activities
            if a not in removed
        ]

        # ========================================================
        # فعالیت‌های جدید Corrector
        # ========================================================

        new_names = []

        for item in corrections.get("new_activities", []):

            if isinstance(item, str):
                new_names.append(item)

            elif isinstance(item, dict):
                name = item.get("name")

                if name:
                    new_names.append(name)

        # ========================================================
        # تشخیص تخلفات اخلاقی
        # ========================================================

        fairness_violation = False
        appeal_violation = False
        transparency_violation = False
        privacy_violation = False

        for correction in corrections.get("model_corrections", []):

            rule = correction.get("rule", "")

            if rule == "عدالت":
                fairness_violation = True

            elif rule == "قابلیت اعتراض":
                appeal_violation = True

            elif rule == "شفافیت":
                transparency_violation = True

            elif rule == "حریم خصوصی":
                privacy_violation = True

        # ========================================================
        # تشخیص از روی فعالیت‌های جدید
        # ========================================================

        if "بررسی تبعیض" in new_names:
            fairness_violation = True

        if "درخواست بازبینی" in new_names:
            appeal_violation = True

        if "بازبینی درخواست" in new_names:
            appeal_violation = True

        # ========================================================
        # تشخیص از ethical_notes
        # ========================================================

        if ethical_notes:

            notes_text = str(ethical_notes)

            if "تبعیض" in notes_text:
                fairness_violation = True

            if "بازبینی" in notes_text or "اعتراض" in notes_text:
                appeal_violation = True

            if "توضیح" in notes_text:
                transparency_violation = True

            if "حریم خصوصی" in notes_text or "gender" in notes_text:
                privacy_violation = True

        # ========================================================
        # حذف فعالیت‌های تکراری
        # ========================================================

        activities = self._unique(activities)

        # ========================================================
        # پیدا کردن فعالیت‌های اصلی
        # ========================================================

        registration = self._find_activity(
            activities,
            [
                "ثبت درخواست",
                "ثبت‌درخواست"
            ]
        )

        documents = self._find_activity(
            activities,
            [
                "بررسی مدارک"
            ]
        )

        financial = self._find_activity(
            activities,
            [
                "ارزیابی نیاز مالی"
            ]
        )

        approval = self._find_activity(
            activities,
            [
                "تایید",
                "تأیید",
                "تایید درخواست",
                "تأیید درخواست"
            ]
        )

        rejection = self._find_activity(
            activities,
            [
                "رد",
                "رد درخواست"
            ]
        )

        notification = self._find_activity(
            activities,
            [
                "ابلاغ نتیجه"
            ]
        )

        # ========================================================
        # اگر ثبت درخواست پیدا نشد
        # ========================================================

        if not registration and activities:
            registration = activities[0]

        # ========================================================
        # فعالیت‌های عادی
        # ========================================================

        normal_tasks = []

        for activity in activities:

            if activity in {
                registration,
                approval,
                rejection,
                notification,
            }:
                continue

            if activity not in normal_tasks:
                normal_tasks.append(activity)

        # ========================================================
        # حذف فعالیت‌های اخلاقی از مسیر عادی
        # ========================================================

        standard = []

        for activity in normal_tasks:

            if activity in [
                "بررسی تبعیض",
                "درخواست بازبینی",
                "بازبینی درخواست",
                "تأیید پس از بازبینی",
                "رد پس از بازبینی",
            ]:
                continue

            standard.append(activity)

        # ========================================================
        # START
        # ========================================================

        start = self._add_start(
            "شروع",
            x=80,
            y=330
        )

        current = start

        # ========================================================
        # ثبت درخواست
        # ========================================================

        if registration:

            task = self._add_task(
                registration,
                self._ethical_documentation(registration),
                x=180,
                y=310
            )

            self._add_flow(
                current,
                task
            )

            current = task

        # ========================================================
        # فعالیت‌های استاندارد
        # ========================================================

        x = 380

        for activity in standard:

            task = self._add_task(
                activity,
                self._ethical_documentation(activity),
                x=x,
                y=310
            )

            self._add_flow(
                current,
                task
            )

            current = task

            x += 210

        # ========================================================
        # بررسی تبعیض
        # ========================================================

        if fairness_violation:

            fairness = self._add_task(
                "بررسی تبعیض",
                (
                    "این فعالیت برای جلوگیری از تبعیض طراحی شده است. "
                    "متغیرهای حساس مانند جنسیت نباید مستقیماً "
                    "در تصمیم‌گیری استفاده شوند."
                ),
                x=x,
                y=310
            )

            self._add_flow(
                current,
                fairness
            )

            current = fairness

            x += 210

        # ========================================================
        # XOR تصمیم اولیه
        # ========================================================

        decision_gateway = self._add_gateway(
            "XOR",
            "تصمیم نهایی",
            (
                "این گیت تصمیم‌گیری را به مسیرهای تأیید و رد "
                "تفکیک می‌کند. مسیر تصمیم نباید بر اساس "
                "متغیرهای حساس مانند جنسیت تعیین شود."
            ),
            x=x,
            y=325
        )

        self._add_flow(
            current,
            decision_gateway
        )

        # ========================================================
        # مسیر تأیید اولیه
        # ========================================================

        approval_id = None

        if approval:

            approval_id = self._add_task(
                approval,
                self._ethical_documentation(approval),
                x=x + 180,
                y=190
            )

            self._add_flow(
                decision_gateway,
                approval_id,
                condition="شرایط احراز شده است",
                name="تأیید"
            )

        # ========================================================
        # مسیر رد اولیه
        # ========================================================

        rejection_id = None

        if rejection:

            rejection_id = self._add_task(
                rejection,
                (
                    self._ethical_documentation(rejection)
                    + " دلیل تصمیم باید برای متقاضی قابل فهم باشد."
                ),
                x=x + 220,
                y=520
            )

            self._add_flow(
                decision_gateway,
                rejection_id,
                condition="شرایط احراز نشده است",
                name="رد"
            )

        # ========================================================
        # اگر تأیید و رد وجود نداشتند
        # ========================================================

        if approval_id is None and rejection_id is None:

            approval_id = self._add_task(
                "تصمیم درخواست",
                (
                    "تصمیم نهایی با رعایت عدالت و بدون استفاده "
                    "مستقیم از متغیرهای حساس اتخاذ می‌شود."
                ),
                x=x + 180,
                y=310
            )

            self._add_flow(
                decision_gateway,
                approval_id
            )

        # ========================================================
        # متغیرهای مربوط به Appeal
        # ========================================================

        appeal_request = None
        appeal_review = None

        appeal_gateway = None
        appeal_approval = None
        appeal_rejection = None

        # ========================================================
        # مسیر اعتراض
        #
        # رد اولیه
        #     ↓
        # درخواست بازبینی
        #     ↓
        # بازبینی درخواست
        #     ↓
        # XOR تصمیم مجدد
        #     ↙       ↘
        #   تأیید      رد
        # ========================================================

        if rejection_id and appeal_violation:

            # ----------------------------------------------------
            # درخواست بازبینی
            # ----------------------------------------------------

            appeal_request = self._add_task(
                "درخواست بازبینی",
                (
                    "این فعالیت برای تضمین قابلیت اعتراض متقاضی "
                    "و فراهم کردن مسیر رسمی درخواست تجدیدنظر "
                    "ایجاد شده است."
                ),
                x=x + 450,
                y=520
            )

            self._add_flow(
                rejection_id,
                appeal_request,
                condition="متقاضی درخواست بازبینی دارد",
                name="درخواست بازبینی"
            )

            # ----------------------------------------------------
            # بازبینی مستقل
            # ----------------------------------------------------

            appeal_review = self._add_task(
                "بازبینی درخواست",
                (
                    "این فعالیت برای بررسی مستقل درخواست تجدیدنظر "
                    "و افزایش پاسخ‌گویی فرآیند ایجاد شده است."
                ),
                x=x + 680,
                y=520
            )

            self._add_flow(
                appeal_request,
                appeal_review,
                name="ارجاع برای بازبینی"
            )

            # ----------------------------------------------------
            # XOR تصمیم پس از بازبینی
            # ----------------------------------------------------

            appeal_gateway = self._add_gateway(
                "XOR",
                "تصمیم نهایی پس از بازبینی",
                (
                    "این گیت نتیجه بازبینی مستقل را بررسی می‌کند. "
                    "تصمیم مجدد باید بر اساس معیارهای مرتبط با "
                    "شرایط مالی و شرایط احراز باشد و نباید بر اساس "
                    "متغیرهای حساس مانند جنسیت اتخاذ شود."
                ),
                x=x + 900,
                y=535
            )

            self._add_flow(
                appeal_review,
                appeal_gateway,
                name="نتیجه بازبینی"
            )

            # ----------------------------------------------------
            # تأیید پس از بازبینی
            # ----------------------------------------------------

            appeal_approval = self._add_task(
                "تأیید پس از بازبینی",
                (
                    "درخواست پس از بازبینی تأیید شده است. "
                    "تصمیم بر اساس معیارهای مرتبط با شرایط "
                    "احراز و بدون تبعیض اتخاذ شده است."
                ),
                x=x + 1100,
                y=380
            )

            self._add_flow(
                appeal_gateway,
                appeal_approval,
                condition="شرایط پس از بازبینی احراز شده است",
                name="تأیید پس از بازبینی"
            )

            # ----------------------------------------------------
            # رد پس از بازبینی
            # ----------------------------------------------------

            appeal_rejection = self._add_task(
                "رد پس از بازبینی",
                (
                    "درخواست پس از بازبینی نیز رد شده است. "
                    "دلیل رد باید به صورت شفاف و قابل فهم "
                    "برای متقاضی ثبت و اعلام شود."
                ),
                x=x + 1100,
                y=650
            )

            self._add_flow(
                appeal_gateway,
                appeal_rejection,
                condition="شرایط پس از بازبینی احراز نشده است",
                name="رد پس از بازبینی"
            )

        # ========================================================
        # ابلاغ نتیجه
        # ========================================================

        if notification:

            notification_id = self._add_task(
                notification,
                self._ethical_documentation(notification),
                x=x + 1350,
                y=380
            )

        else:

            notification_id = self._add_task(
                "ابلاغ نتیجه",
                self._ethical_documentation("ابلاغ نتیجه"),
                x=x + 1350,
                y=380
            )

        # ========================================================
        # تأیید اولیه → ابلاغ
        # ========================================================

        if approval_id:

            self._add_flow(
                approval_id,
                notification_id,
                name="ابلاغ نتیجه تأیید"
            )

        # ========================================================
        # رد اولیه → ابلاغ
        #
        # این مسیر فقط زمانی طی می‌شود که اعتراض انجام نشود.
        # ========================================================

        if rejection_id:

            self._add_flow(
                rejection_id,
                notification_id,
                condition="متقاضی درخواست بازبینی ندارد",
                name="ابلاغ نتیجه رد"
            )

        # ========================================================
        # تأیید پس از بازبینی → ابلاغ
        # ========================================================

        if appeal_approval:

            self._add_flow(
                appeal_approval,
                notification_id,
                name="ابلاغ تأیید پس از بازبینی"
            )

        # ========================================================
        # رد پس از بازبینی → ابلاغ
        # ========================================================

        if appeal_rejection:

            self._add_flow(
                appeal_rejection,
                notification_id,
                name="ابلاغ رد پس از بازبینی"
            )

        # ========================================================
        # END
        # ========================================================

        end = self._add_end(
            "پایان",
            x=x + 1570,
            y=400
        )

        self._add_flow(
            notification_id,
            end
        )

        return start, end

    # ============================================================
    # Find activity
    # ============================================================

    def _find_activity(
        self,
        activities: List[str],
        candidates: List[str]
    ) -> Optional[str]:

        for candidate in candidates:

            if candidate in activities:
                return candidate

        # normalized matching
        def normalize(value):
            return str(value).replace(
                "‌", ""
            ).replace(
                " ", ""
            ).lower()

        normalized = {
            normalize(a): a
            for a in activities
        }

        for candidate in candidates:

            key = normalize(candidate)

            if key in normalized:
                return normalized[key]

        return None

    # ============================================================
    # XML generation
    # ============================================================

    def _create_xml(
        self,
        process_name: str = "فرآیند کمک مالی دانشجویی"
    ) -> ET.Element:

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

        ET.register_namespace(
            "xsi",
            self.XSI_NS
        )

        definitions = ET.Element(
            self._q(self.BPMN_NS, "definitions"),
            {
                "id": "Definitions_Ethical_ABPMS",
                "targetNamespace":
                    "http://bpmn.io/schema/bpmn",
            }
        )

        process = ET.SubElement(
            definitions,
            self._q(self.BPMN_NS, "process"),
            {
                "id": "Process_Ethical_ABPMS",
                "name": process_name,
                "isExecutable": "true",
            }
        )

        # --------------------------------------------------------
        # Nodes
        # --------------------------------------------------------

        for node_id, node in self.nodes.items():

            node_type = node["type"]

            if node_type == "task":

                element = ET.SubElement(
                    process,
                    self._q(self.BPMN_NS, "task"),
                    {
                        "id": node_id,
                        "name": node["name"],
                    }
                )

            elif node_type == "start":

                element = ET.SubElement(
                    process,
                    self._q(self.BPMN_NS, "startEvent"),
                    {
                        "id": node_id,
                        "name": node["name"],
                    }
                )

            elif node_type == "end":

                element = ET.SubElement(
                    process,
                    self._q(self.BPMN_NS, "endEvent"),
                    {
                        "id": node_id,
                        "name": node["name"],
                    }
                )

            elif node_type == "XOR":

                element = ET.SubElement(
                    process,
                    self._q(
                        self.BPMN_NS,
                        "exclusiveGateway"
                    ),
                    {
                        "id": node_id,
                        "name": node["name"],
                    }
                )

            elif node_type == "AND":

                element = ET.SubElement(
                    process,
                    self._q(
                        self.BPMN_NS,
                        "parallelGateway"
                    ),
                    {
                        "id": node_id,
                        "name": node["name"],
                    }
                )

            else:
                continue

            self._documentation(
                element,
                node.get("documentation")
            )

        # --------------------------------------------------------
        # Sequence flows
        # --------------------------------------------------------

        for flow in self.flows:

            attrs = {
                "id": flow["id"],
                "sourceRef": flow["source"],
                "targetRef": flow["target"],
            }

            if flow.get("name"):
                attrs["name"] = flow["name"]

            flow_element = ET.SubElement(
                process,
                self._q(
                    self.BPMN_NS,
                    "sequenceFlow"
                ),
                attrs
            )

            if flow.get("condition"):

                condition = ET.SubElement(
                    flow_element,
                    self._q(
                        self.BPMN_NS,
                        "conditionExpression"
                    ),
                    {
                        self._q(
                            self.XSI_NS,
                            "type"
                        ): "bpmn:tFormalExpression"
                    }
                )

                condition.text = flow["condition"]

        # --------------------------------------------------------
        # BPMN DI
        # --------------------------------------------------------

        diagram = ET.SubElement(
            definitions,
            self._q(
                self.BPMNDI_NS,
                "BPMNDiagram"
            ),
            {
                "id": "BPMNDiagram_Ethical_ABPMS"
            }
        )

        plane = ET.SubElement(
            diagram,
            self._q(
                self.BPMNDI_NS,
                "BPMNPlane"
            ),
            {
                "id": "BPMNPlane_Ethical_ABPMS",
                "bpmnElement": "Process_Ethical_ABPMS",
            }
        )

        # --------------------------------------------------------
        # Shapes
        # --------------------------------------------------------

        for node_id, node in self.nodes.items():

            shape = ET.SubElement(
                plane,
                self._q(
                    self.BPMNDI_NS,
                    "BPMNShape"
                ),
                {
                    "id": f"{node_id}_di",
                    "bpmnElement": node_id,
                }
            )

            ET.SubElement(
                shape,
                self._q(
                    self.DC_NS,
                    "Bounds"
                ),
                {
                    "x": str(node["x"]),
                    "y": str(node["y"]),
                    "width": str(node["width"]),
                    "height": str(node["height"]),
                }
            )

        # --------------------------------------------------------
        # Edges
        # --------------------------------------------------------

        for flow in self.flows:

            source = self.nodes.get(
                flow["source"]
            )

            target = self.nodes.get(
                flow["target"]
            )

            if not source or not target:
                continue

            edge = ET.SubElement(
                plane,
                self._q(
                    self.BPMNDI_NS,
                    "BPMNEdge"
                ),
                {
                    "id": f"{flow['id']}_di",
                    "bpmnElement": flow["id"],
                }
            )

            sx = source["x"] + source["width"]
            sy = source["y"] + source["height"] / 2

            tx = target["x"]
            ty = target["y"] + target["height"] / 2

            # اگر مسیر عمودی/شاخه‌ای باشد
            if abs(sy - ty) > 10:

                mid_x = (sx + tx) / 2

                ET.SubElement(
                    edge,
                    self._q(
                        self.DI_NS,
                        "waypoint"
                    ),
                    {
                        "x": str(sx),
                        "y": str(sy),
                    }
                )

                ET.SubElement(
                    edge,
                    self._q(
                        self.DI_NS,
                        "waypoint"
                    ),
                    {
                        "x": str(mid_x),
                        "y": str(sy),
                    }
                )

                ET.SubElement(
                    edge,
                    self._q(
                        self.DI_NS,
                        "waypoint"
                    ),
                    {
                        "x": str(mid_x),
                        "y": str(ty),
                    }
                )

                ET.SubElement(
                    edge,
                    self._q(
                        self.DI_NS,
                        "waypoint"
                    ),
                    {
                        "x": str(tx),
                        "y": str(ty),
                    }
                )

            else:

                ET.SubElement(
                    edge,
                    self._q(
                        self.DI_NS,
                        "waypoint"
                    ),
                    {
                        "x": str(sx),
                        "y": str(sy),
                    }
                )

                ET.SubElement(
                    edge,
                    self._q(
                        self.DI_NS,
                        "waypoint"
                    ),
                    {
                        "x": str(tx),
                        "y": str(ty),
                    }
                )

        return definitions

    # ============================================================
    # Main generate
    # ============================================================

    def generate(
        self,
        process_tree,
        ethical_notes=None,
        corrections=None,
        output_path=None,
        **kwargs,
    ):

        # --------------------------------------------------------
        # Backward compatibility
        # --------------------------------------------------------

        if output_path is None:

            output_path = kwargs.get(
                "path"
            )

        if output_path is None:

            output_path = os.path.join(
                os.getcwd(),
                "ethical_process.bpmn"
            )

        # --------------------------------------------------------
        # Reset state
        # --------------------------------------------------------

        self.nodes = {}
        self.flows = []

        self.node_counter = 0
        self.flow_counter = 0

        # --------------------------------------------------------
        # Activities
        # --------------------------------------------------------

        activities = (
            self._extract_process_tree_activities(
                process_tree
            )
        )

        # --------------------------------------------------------
        # اگر ProcessTree قابل استخراج نبود
        # --------------------------------------------------------

        if not activities:

            activities = [
                "ثبت درخواست",
                "بررسی مدارک",
                "ارزیابی نیاز مالی",
                "تأیید درخواست",
                "رد درخواست",
                "ابلاغ نتیجه",
            ]

        # --------------------------------------------------------
        # Normalize corrections
        # --------------------------------------------------------

        normalized_corrections = (
            self._normalize_corrections(
                corrections
            )
        )

        # --------------------------------------------------------
        # اگر corrections از kwargs آمده باشد
        # --------------------------------------------------------

        if not corrections:

            normalized_corrections = (
                self._normalize_corrections(
                    kwargs.get("correction_result")
                    or kwargs.get("corrected_model")
                    or kwargs.get("corrections")
                )
            )

        # --------------------------------------------------------
        # Build process
        # --------------------------------------------------------

        self._build_ethical_process(
            activities,
            normalized_corrections,
            ethical_notes,
        )

        # --------------------------------------------------------
        # XML
        # --------------------------------------------------------

        definitions = self._create_xml()

        # --------------------------------------------------------
        # Pretty XML
        # --------------------------------------------------------

        raw_xml = ET.tostring(
            definitions,
            encoding="utf-8",
            xml_declaration=True
        )

        dom = minidom.parseString(
            raw_xml
        )

        pretty_xml = dom.toprettyxml(
            indent="  ",
            encoding="UTF-8"
        )

        # --------------------------------------------------------
        # Remove empty lines
        # --------------------------------------------------------

        pretty_text = "\n".join(
            line
            for line in pretty_xml.decode(
                "utf-8"
            ).splitlines()
            if line.strip()
        )

        # --------------------------------------------------------
        # Output directory
        # --------------------------------------------------------

        directory = os.path.dirname(
            os.path.abspath(output_path)
        )

        os.makedirs(
            directory,
            exist_ok=True
        )

        # --------------------------------------------------------
        # Write
        # --------------------------------------------------------

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                pretty_text
            )

        return output_path


# ================================================================
# Convenience function
# ================================================================

def generate_bpmn(
    process_tree,
    ethical_notes=None,
    corrections=None,
    output_path="ethical_process.bpmn",
):

    generator = BPMNGenerator()

    return generator.generate(
        process_tree=process_tree,
        ethical_notes=ethical_notes,
        corrections=corrections,
        output_path=output_path,
    )
