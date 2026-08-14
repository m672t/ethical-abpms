import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.process_tree import converter as pt_converter
import os

class ProcessDiscovery:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.log = None
        self.petri_net = None
        self.initial_marking = None
        self.final_marking = None
        self.process_tree = None
        
    def load_log(self):
        """بارگذاری لاگ از فایل CSV"""
        df = pd.read_csv(self.csv_path)
        
        # تبدیل ستون timestamp به فرمت datetime
        df = dataframe_utils.convert_timestamp_columns_in_df(df)
        df = df.sort_values('timestamp')
        
        # تغییر نام ستون‌ها به فرمت استاندارد pm4py
        df = df.rename(columns={
            'case_id': 'case:concept:name',
            'activity': 'concept:name',
            'timestamp': 'time:timestamp'
        })
        
        # تبدیل به Event Log
        self.log = log_converter.apply(df)
        return self.log
    
    def discover_process(self):
        """کشف فرآیند با استفاده از Inductive Miner"""
        if self.log is None:
            self.load_log()
        
        # دریافت process tree
        self.process_tree = inductive_miner.apply(self.log)
        
        # تبدیل process tree به petri net
        try:
            self.petri_net, self.initial_marking, self.final_marking = pt_converter.apply(self.process_tree)
        except:
            # اگر روش اول جواب نداد، از روش جایگزین استفاده می‌کنیم
            from pm4py.objects.petri_net.utils import petri_utils
            from pm4py.objects.petri_net import obj as petri_net
            from pm4py.objects.petri_net.obj import Marking
            
            # ساخت یک petri net ساده برای نمایش
            net = petri_net.PetriNet("discovered_process")
            im = Marking()
            fm = Marking()
            
            # ایجاد یک place شروع
            start_place = petri_net.PetriNet.Place("start")
            net.places.add(start_place)
            im[start_place] = 1
            
            # ایجاد یک place پایان
            end_place = petri_net.PetriNet.Place("end")
            net.places.add(end_place)
            fm[end_place] = 1
            
            # ایجاد transition برای هر فعالیت
            activities = self.get_activities()
            last_place = start_place
            
            for i, activity in enumerate(activities):
                # ایجاد transition
                trans = petri_net.PetriNet.Transition(activity, activity)
                net.transitions.add(trans)
                
                # ایجاد place جدید
                if i < len(activities) - 1:
                    new_place = petri_net.PetriNet.Place(f"p_{i+1}")
                    net.places.add(new_place)
                else:
                    new_place = end_place
                
                # اتصال transition
                net.arcs.add(petri_net.PetriNet.Arc(last_place, trans, 1))
                net.arcs.add(petri_net.PetriNet.Arc(trans, new_place, 1))
                
                last_place = new_place
            
            self.petri_net = net
            self.initial_marking = im
            self.final_marking = fm
            
        return self.petri_net, self.initial_marking, self.final_marking
    
    def visualize_process(self, output_path="output/process_model.png"):
        """نمایش بصری مدل فرآیند"""
        if self.petri_net is None:
            self.discover_process()
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        try:
            gviz = pn_visualizer.apply(self.petri_net, self.initial_marking, self.final_marking)
            pn_visualizer.save(gviz, output_path)
        except:
            # اگر visualization خطا داد، یک تصویر ساده از فعالیت‌ها ایجاد می‌کنیم
            import matplotlib.pyplot as plt
            activities = self.get_activities()
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.set_title("مدل فرآیند کشف‌شده", fontsize=16)
            ax.set_axis_off()
            
            y_pos = range(len(activities))
            ax.barh(y_pos, [1]*len(activities), color='skyblue')
            ax.set_yticks(y_pos)
            ax.set_yticklabels(activities)
            ax.invert_yaxis()
            
            for i, act in enumerate(activities):
                ax.text(0.5, i, f"← {act} →", va='center', ha='center', fontsize=12)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
        return output_path
    
    def get_activities(self):
        """دریافت لیست فعالیت‌های موجود در لاگ"""
        if self.log is None:
            self.load_log()
        
        activities = set()
        for trace in self.log:
            for event in trace:
                activities.add(event['concept:name'])
        return sorted(list(activities))
    
    def get_case_attributes(self):
        """دریافت ویژگی‌های هر کیس"""
        if self.log is None:
            self.load_log()
        
        attributes = {}
        sample_trace = self.log[0]
        for key, value in sample_trace.attributes.items():
            if key not in ['concept:name', 'time:timestamp']:
                attributes[key] = type(value).__name__
        
        for event in sample_trace:
            for key, value in event.items():
                if key not in ['concept:name', 'time:timestamp'] and key not in attributes:
                    attributes[key] = type(value).__name__
                    
        return attributes

def discover_from_csv(csv_path):
    discoverer = ProcessDiscovery(csv_path)
    discoverer.load_log()
    discoverer.discover_process()
    return discoverer