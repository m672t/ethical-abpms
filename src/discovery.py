"""
Process Discovery
کشف فرآیند با Inductive Miner و نگه‌داری Process Tree واقعی
"""

import os
import pandas as pd

from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.objects.conversion.process_tree import converter as pt_converter
from pm4py.objects.log.util import dataframe_utils


class ProcessDiscovery:

    def __init__(self, csv_path):
        self.csv_path = csv_path

        self.log = None

        # مدل اصلی کشف‌شده
        self.process_tree = None

        # برای نمایش و تحلیل PM4Py
        self.petri_net = None
        self.initial_marking = None
        self.final_marking = None

    # ============================================================
    # LOAD LOG
    # ============================================================

    def load_log(self):
        """بارگذاری Event Log از CSV"""

        df = pd.read_csv(self.csv_path)

        required_columns = [
            "case_id",
            "activity",
            "timestamp"
        ]

        missing = [
            c for c in required_columns
            if c not in df.columns
        ]

        if missing:
            raise ValueError(
                f"ستون‌های ضروری در CSV وجود ندارند: {missing}"
            )

        # تبدیل timestamp
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        if df["timestamp"].isna().any():
            raise ValueError(
                "برخی timestampها قابل تبدیل به تاریخ نیستند."
            )

        # مرتب‌سازی صحیح Event Log
        df = df.sort_values(
            ["case_id", "timestamp"]
        ).reset_index(drop=True)

        # تبدیل نام ستون‌ها به استاندارد PM4Py
        df = df.rename(
            columns={
                "case_id": "case:concept:name",
                "activity": "concept:name",
                "timestamp": "time:timestamp"
            }
        )

        # تبدیل DataFrame به Event Log
        self.log = log_converter.apply(df)

        return self.log

    # ============================================================
    # DISCOVERY
    # ============================================================

    def discover_process(self):
        """
        کشف Process Tree واقعی با Inductive Miner.

        نکته مهم:
        Process Tree مدل اصلی سیستم است.
        اگر کشف شکست بخورد، دیگر مدل جعلی خطی تولید نمی‌کنیم.
        """

        if self.log is None:
            self.load_log()

        # --------------------------------------------------------
        # Inductive Miner
        # --------------------------------------------------------

        try:
            self.process_tree = inductive_miner.apply_tree(
                self.log
            )

        except Exception as e:
            # بعضی نسخه‌های PM4Py ممکن است apply_tree متفاوت داشته باشند
            try:
                self.process_tree = inductive_miner.apply(
                    self.log,
                    variant=inductive_miner.Variants.IM,
                    parameters={
                        "return_process_tree": True
                    }
                )

            except Exception as e2:
                raise RuntimeError(
                    "Inductive Miner نتوانست Process Tree تولید کند.\n"
                    f"خطای اول: {e}\n"
                    f"خطای دوم: {e2}"
                )

        # --------------------------------------------------------
        # تبدیل Process Tree به Petri Net
        # فقط برای Visualization / Analysis
        # --------------------------------------------------------

        try:
            (
                self.petri_net,
                self.initial_marking,
                self.final_marking
            ) = pt_converter.apply(
                self.process_tree
            )

        except Exception as e:
            # شکست Petri Net نباید باعث ساخت مدل جعلی شود.
            self.petri_net = None
            self.initial_marking = None
            self.final_marking = None

            print(
                "⚠️ Process Tree کشف شد ولی تبدیل به Petri Net "
                f"برای نمایش انجام نشد: {e}"
            )

        return self.process_tree

    # ============================================================
    # VISUALIZATION
    # ============================================================

    def visualize_process(
        self,
        output_path="output/process_model.png"
    ):
        """نمایش مدل کشف‌شده"""

        if self.process_tree is None:
            self.discover_process()

        os.makedirs(
            os.path.dirname(output_path) or ".",
            exist_ok=True
        )

        # اگر Petri Net داریم، همان را نمایش بده
        if self.petri_net is not None:

            try:
                gviz = pn_visualizer.apply(
                    self.petri_net,
                    self.initial_marking,
                    self.final_marking
                )

                pn_visualizer.save(
                    gviz,
                    output_path
                )

                return output_path

            except Exception as e:
                print(
                    f"⚠️ نمایش Petri Net انجام نشد: {e}"
                )

        # --------------------------------------------------------
        # fallback صرفاً برای Visualization
        # این fallback مدل فرآیند نیست.
        # --------------------------------------------------------

        import matplotlib.pyplot as plt

        activities = self.get_activities()

        fig, ax = plt.subplots(
            figsize=(12, 7)
        )

        ax.set_title(
            "فعالیت‌های فرآیند کشف‌شده",
            fontsize=16
        )

        ax.set_axis_off()

        for i, activity in enumerate(activities):

            ax.text(
                0.5,
                1 - (i + 1) / (len(activities) + 1),
                activity,
                ha="center",
                va="center",
                fontsize=12,
                bbox=dict(
                    boxstyle="round,pad=0.5",
                    facecolor="white",
                    edgecolor="black"
                )
            )

        plt.tight_layout()

        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight"
        )

        plt.close()

        return output_path

    # ============================================================
    # ACTIVITIES
    # ============================================================

    def get_activities(self):
        """دریافت فعالیت‌های موجود در Event Log"""

        if self.log is None:
            self.load_log()

        activities = set()

        for trace in self.log:
            for event in trace:
                activity = event.get(
                    "concept:name"
                )

                if activity:
                    activities.add(
                        str(activity)
                    )

        return sorted(activities)

    # ============================================================
    # PROCESS TREE INFO
    # ============================================================

    def get_process_tree(self):
        """
        دسترسی مستقیم به Process Tree.

        این متد برای BPMN Generator استفاده می‌شود.
        """

        if self.process_tree is None:
            self.discover_process()

        return self.process_tree

    def get_case_attributes(self):
        """دریافت ویژگی‌های موجود در Event Log"""

        if self.log is None:
            self.load_log()

        attributes = {}

        if len(self.log) == 0:
            return attributes

        sample_trace = self.log[0]

        # Case attributes
        for key, value in sample_trace.attributes.items():

            if key not in [
                "concept:name",
                "time:timestamp"
            ]:
                attributes[key] = type(value).__name__

        # Event attributes
        for event in sample_trace:

            for key, value in event.items():

                if key not in [
                    "concept:name",
                    "time:timestamp"
                ]:

                    if key not in attributes:
                        attributes[key] = (
                            type(value).__name__
                        )

        return attributes


# ================================================================
# Helper
# ================================================================

def discover_from_csv(csv_path):

    discoverer = ProcessDiscovery(
        csv_path
    )

    discoverer.load_log()
    discoverer.discover_process()

    return discoverer
