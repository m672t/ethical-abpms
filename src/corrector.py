"""
عامل اصلاح‌کننده اخلاقی A-BPMS

وظیفه:
1. دریافت نتیجه Auditor
2. اعمال اصلاحات واقعی روی مدل فرآیند
3. اصلاح فرم‌ها
4. ساخت یک مدل اصلاح‌شده قابل استفاده توسط BPMN Generator
"""

import copy
from src.auditor import AuditorAgent


class CorrectedProcessModel:
    """
    یک مدل ساده و مستقل برای نگهداری فرآیند اصلاح‌شده.

    ساختار:
        start
        sequence
        xor
        and
        loop
    """

    def __init__(self, tree=None):
        self.tree = tree
        self.activities = []
        self.documentation = {}
        self.conditions = {}

    def get_activities(self):
        return self.activities

    def add_activity(self, name, documentation=None):
        if name not in self.activities:
            self.activities.append(name)

        if documentation:
            self.documentation[name] = documentation

    def remove_activity(self, name):
        if name in self.activities:
            self.activities.remove(name)

    def has_activity(self, name):
        return name in self.activities

    def get_documentation(self, name):
        return self.documentation.get(name)

    def set_condition(self, flow_name, condition):
        self.conditions[flow_name] = condition


class CorrectorAgent:
    """
    عامل اصلاح‌کننده اخلاقی فرآیند.

    اصلاحات واقعی:
    - عدالت
    - شفافیت
    - قابلیت اعتراض
    - حریم خصوصی
    """

    def __init__(self):

        self.auditor = AuditorAgent()
        self.corrections_applied = []

    # =========================================================
    # MAIN
    # =========================================================

    def correct(self, log_path, process_model, forms):

        audit_result = self.auditor.audit(
            log_path,
            process_model
        )

        corrections = {
            "audit_result": audit_result,
            "model_corrections": [],
            "form_corrections": [],
            "new_activities": [],
            "removed_activities": [],
            "modified_activities": [],
            "ethical_documentation": {}
        }

        # -----------------------------------------------------
        # ساخت کپی از مدل اولیه
        # -----------------------------------------------------

        corrected_model = self._copy_model(process_model)

        # -----------------------------------------------------
        # پردازش تخلفات
        # -----------------------------------------------------

        for violation in audit_result.get("violations", []):

            correction = self._apply_correction(
                violation,
                corrected_model,
                forms
            )

            corrections["model_corrections"].append(
                correction
            )

            if correction.get("new_activity"):
                corrections["new_activities"].append(
                    correction["new_activity"]
                )

            if correction.get("removed_activity"):
                corrections["removed_activities"].append(
                    correction["removed_activity"]
                )

            if correction.get("modified_activity"):
                corrections["modified_activities"].append(
                    correction["modified_activity"]
                )

            if correction.get("form_correction"):
                corrections["form_corrections"].append(
                    correction["form_correction"]
                )

            if correction.get("documentation"):
                corrections["ethical_documentation"].update(
                    correction["documentation"]
                )

        # -----------------------------------------------------
        # اصلاحات پایه حتی اگر Auditor آنها را گزارش نکرده باشد
        # -----------------------------------------------------

        corrected_model = self._ensure_ethical_structure(
            corrected_model,
            corrections
        )

        corrections["corrected_model"] = corrected_model

        self.corrections_applied = corrections

        return corrections

    # =========================================================
    # COPY
    # =========================================================

    def _copy_model(self, process_model):

        if process_model is None:
            return CorrectedProcessModel()

        # اگر مدل قبلی قابلیت deepcopy دارد
        try:
            copied = copy.deepcopy(process_model)
            return copied
        except Exception:
            pass

        # مدل ساده
        corrected = CorrectedProcessModel()

        try:
            corrected.activities = list(
                process_model.get_activities()
            )
        except Exception:
            corrected.activities = []

        return corrected

    # =========================================================
    # APPLY CORRECTION
    # =========================================================

    def _apply_correction(
        self,
        violation,
        process_model,
        forms
    ):

        rule = violation.get("rule", "")
        violation_type = violation.get("type", "")

        correction = {
            "rule": rule,
            "type": violation_type,
            "description": violation.get(
                "suggestion",
                ""
            ),
            "applied": False
        }

        # =====================================================
        # FAIRNESS
        # =====================================================

        if rule == "عدالت":

            if "تبعیض جنسیتی" in violation_type:

                activity_name = "بررسی تبعیض"

                self._add_activity(
                    process_model,
                    activity_name,
                    documentation=(
                        "⚖️ این فعالیت برای جلوگیری از "
                        "تأثیر متغیر جنسیت در تصمیم‌گیری "
                        "ایجاد شده است."
                    )
                )

                correction["new_activity"] = {
                    "name": activity_name,
                    "description": (
                        "کنترل عدم استفاده از جنسیت "
                        "در تصمیم‌گیری"
                    ),
                    "position": "قبل از تصمیم‌گیری"
                }

                correction["documentation"] = {
                    activity_name: (
                        "⚖️ کنترل عدالت: متغیرهای حساس "
                        "مانند جنسیت نباید معیار مستقیم "
                        "تصمیم‌گیری باشند."
                    )
                }

                correction["applied"] = True

        # =====================================================
        # TRANSPARENCY
        # =====================================================

        elif rule == "شفافیت":

            form_correction = {
                "add_field": "decision_explanation",
                "field_label": "توضیح دلیل تصمیم",
                "field_type": "textarea",
                "required": True
            }

            correction["form_correction"] = form_correction

            correction["modified_activity"] = {
                "name": "توضیح تصمیم",
                "description": (
                    "ثبت توضیح قابل فهم برای "
                    "تصمیم تأیید یا رد"
                )
            }

            correction["documentation"] = {
                "تأیید": (
                    "📝 دلیل تأیید باید به صورت "
                    "شفاف و قابل فهم ثبت شود."
                ),
                "رد": (
                    "📝 دلیل رد باید به صورت "
                    "شفاف و قابل فهم ثبت شود."
                )
            }

            correction["applied"] = True

        # =====================================================
        # APPEAL
        # =====================================================

        elif rule == "قابلیت اعتراض":

            activity_name = "درخواست بازبینی"

            self._add_activity(
                process_model,
                activity_name,
                documentation=(
                    "⚖️ این فعالیت مسیر رسمی اعتراض "
                    "و درخواست تجدیدنظر را فراهم می‌کند."
                )
            )

            review_activity = "بازبینی درخواست"

            self._add_activity(
                process_model,
                review_activity,
                documentation=(
                    "⚖️ درخواست تجدیدنظر توسط "
                    "عامل/کارشناس مسئول بررسی می‌شود."
                )
            )

            correction["new_activity"] = {
                "name": activity_name,
                "description": (
                    "کاربر می‌تواند پس از تصمیم "
                    "درخواست تجدیدنظر کند."
                ),
                "position": "بعد از تصمیم رد"
            }

            correction["additional_activity"] = {
                "name": review_activity,
                "description": (
                    "بررسی درخواست تجدیدنظر"
                )
            }

            correction["documentation"] = {
                activity_name: (
                    "⚖️ مسیر اعتراض برای تضمین "
                    "قابلیت پاسخ‌گویی فرآیند ایجاد شده است."
                ),
                review_activity: (
                    "⚖️ درخواست تجدیدنظر باید توسط "
                    "مسیر بازبینی مستقل بررسی شود."
                )
            }

            correction["applied"] = True

        # =====================================================
        # PRIVACY
        # =====================================================

        elif rule == "حریم خصوصی":

            sensitive_fields = [
                "gender",
                "ethnicity",
                "national_id"
            ]

            correction["form_correction"] = {
                "hide_fields": sensitive_fields,
                "field_label": (
                    "فیلدهای حساس در رابط کاربر "
                    "نمایش داده نمی‌شوند."
                )
            }

            correction["modified_activity"] = {
                "name": "حفاظت از حریم خصوصی",
                "description": (
                    "کنترل داده‌های حساس قبل از "
                    "نمایش یا استفاده در فرآیند"
                )
            }

            correction["documentation"] = {
                "ارزیابی نیاز مالی": (
                    "🔒 داده‌های حساس مانند جنسیت "
                    "نباید مستقیماً در معیار تصمیم‌گیری "
                    "استفاده شوند."
                )
            }

            correction["applied"] = True

        return correction

    # =========================================================
    # ADD ACTIVITY
    # =========================================================

    def _add_activity(
        self,
        process_model,
        name,
        documentation=None
    ):

        try:

            if hasattr(process_model, "add_activity"):

                process_model.add_activity(
                    name,
                    documentation
                )

                return

            if hasattr(
                process_model,
                "activities"
            ):

                if name not in process_model.activities:
                    process_model.activities.append(
                        name
                    )

        except Exception:
            pass

    # =========================================================
    # ENSURE ETHICAL STRUCTURE
    # =========================================================

    def _ensure_ethical_structure(
        self,
        process_model,
        corrections
    ):

        """
        اطمینان از اینکه فرآیند نهایی حداقل
        عناصر اخلاقی مورد انتظار را دارد.
        """

        activities = self._get_activities(
            process_model
        )

        # -----------------------------------------------------
        # Appeal
        # -----------------------------------------------------

        if any(
            "اعتراض" in str(x)
            or "بازبینی" in str(x)
            for x in activities
        ):
            pass

        # اگر بازبینی در مدل نیست، اضافه کن
        else:

            self._add_activity(
                process_model,
                "درخواست بازبینی",
                (
                    "⚖️ مسیر رسمی اعتراض "
                    "به تصمیم فراهم شده است."
                )
            )

            self._add_activity(
                process_model,
                "بازبینی درخواست",
                (
                    "⚖️ درخواست تجدیدنظر "
                    "به صورت مستقل بررسی می‌شود."
                )
            )

            corrections["new_activities"].extend([
                {
                    "name": "درخواست بازبینی",
                    "description": (
                        "مسیر اعتراض کاربر"
                    )
                },
                {
                    "name": "بازبینی درخواست",
                    "description": (
                        "بررسی درخواست تجدیدنظر"
                    )
                }
            ])

        return process_model

    # =========================================================
    # ACTIVITIES
    # =========================================================

    def _get_activities(self, process_model):

        try:

            if hasattr(
                process_model,
                "get_activities"
            ):
                return list(
                    process_model.get_activities()
                )

            if hasattr(
                process_model,
                "activities"
            ):
                return list(
                    process_model.activities
                )

        except Exception:
            pass

        return []

    # =========================================================
    # GENERATE CORRECTED MODEL INFO
    # =========================================================

    def generate_corrected_model(
        self,
        original_model,
        corrections
    ):

        original_activities = (
            self._get_activities(
                original_model
            )
        )

        corrected_model = corrections.get(
            "corrected_model"
        )

        corrected_activities = (
            self._get_activities(
                corrected_model
            )
        )

        added = [
            x for x in corrected_activities
            if x not in original_activities
        ]

        removed = [
            x for x in original_activities
            if x not in corrected_activities
        ]

        return {
            "original_activities":
                original_activities,

            "added_activities":
                added,

            "removed_activities":
                removed,

            "modified_activities":
                corrections.get(
                    "modified_activities",
                    []
                ),

            "ethical_documentation":
                corrections.get(
                    "ethical_documentation",
                    {}
                ),

            "model":
                corrected_model
        }

    # =========================================================
    # DEPLOY TO BPMS
    # =========================================================

    def deploy_to_bpms(self, bpmn_path):

        from src.bpms_integration import BPMSEngine

        engine = BPMSEngine()

        check = engine.check_installation()

        if not check["installed"]:

            return {
                "success": False,
                "message": check["message"],
                "suggestion": (
                    "لطفاً ProcessMaker را نصب کنید."
                )
            }

        import_result = engine.import_bpmn(
            bpmn_path
        )

        if not import_result["success"]:
            return import_result

        report = engine.generate_integration_report(
            bpmn_path
        )

        return {
            "success": True,
            "message": (
                "✅ فرآیند با موفقیت "
                "در BPMS مستقر شد."
            ),
            "report": report,
            "import_result": import_result
        }
