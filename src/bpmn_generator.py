"""
ماژول تولید BPMN 2.0 - خروجی استاندارد XML
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re

class BPMNGenerator:
    """تولید فایل BPMN 2.0 از مدل فرآیند"""
    
    def __init__(self, process_name="EthicalProcess"):
        # استفاده از نام انگلیسی بدون فاصله
        self.process_name = re.sub(r'[^a-zA-Z0-9_]', '_', process_name)
        self.ns = {
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
            'dc': 'http://www.omg.org/spec/DD/20100524/DC',
            'di': 'http://www.omg.org/spec/DD/20100524/DI'
        }
        
    def _clean_id(self, text):
        """تبدیل نام به ID معتبر BPMN (فقط حروف انگلیسی، اعداد و خط تیره)"""
        # حذف کاراکترهای غیرمجاز
        clean = re.sub(r'[^a-zA-Z0-9_]', '_', text)
        # اگه با عدد شروع شد، یه حرف اول بذار
        if clean and clean[0].isdigit():
            clean = 'id_' + clean
        return clean
    
    def generate(self, activities, ethical_notes, output_path="output/process_model.bpmn"):
        """
        تولید فایل BPMN 2.0 معتبر
        """
        
        root = ET.Element('bpmn:definitions', {
            'xmlns:bpmn': self.ns['bpmn'],
            'xmlns:bpmndi': self.ns['bpmndi'],
            'xmlns:dc': self.ns['dc'],
            'xmlns:di': self.ns['di'],
            'targetNamespace': 'http://bpmn.io/schema/bpmn',
            'id': 'Definitions_1'
        })
        
        # ایجاد Process با ID معتبر
        process_id = f'Process_{self.process_name}'
        process = ET.SubElement(root, 'bpmn:process', {
            'id': process_id,
            'isExecutable': 'true',
            'name': self.process_name
        })
        
        # المان‌ها و اتصالات
        elements = []
        
        # Start Event
        start_id = 'StartEvent_1'
        start = ET.SubElement(process, 'bpmn:startEvent', {
            'id': start_id,
            'name': 'شروع'
        })
        elements.append((start_id, 'شروع'))
        
        # فعالیت‌ها
        for i, activity in enumerate(activities, 1):
            node_id = f'Activity_{i:02d}'
            # استفاده از نام انگلیسی برای فعالیت
            activity_name = self._clean_id(activity)
            
            task = ET.SubElement(process, 'bpmn:task', {
                'id': node_id,
                'name': activity
            })
            
            # افزودن Documentation (برچسب اخلاقی)
            if activity in ethical_notes:
                doc = ET.SubElement(task, 'bpmn:documentation')
                doc.text = ethical_notes[activity]
            
            elements.append((node_id, activity))
            
            # اتصال از قبلی به این
            if len(elements) > 1:
                prev_id = elements[-2][0]
                flow = ET.SubElement(process, 'bpmn:sequenceFlow', {
                    'id': f'Flow_{i-1}_{i}',
                    'sourceRef': prev_id,
                    'targetRef': node_id
                })
        
        # End Event
        end_id = 'EndEvent_1'
        end = ET.SubElement(process, 'bpmn:endEvent', {
            'id': end_id,
            'name': 'پایان'
        })
        
        # اتصال آخرین فعالیت به End
        if elements:
            flow = ET.SubElement(process, 'bpmn:sequenceFlow', {
                'id': f'Flow_{len(elements)}_end',
                'sourceRef': elements[-1][0],
                'targetRef': end_id
            })
        
        # ============================================================
        # BPMNDI (برای نمایش بصری) - با ارجاعات صحیح
        # ============================================================
        bpmndi = ET.SubElement(root, 'bpmndi:BPMNDiagram', {
            'id': 'BPMNDiagram_1'
        })
        
        bpmn_plane = ET.SubElement(bpmndi, 'bpmndi:BPMNPlane', {
            'id': 'BPMNPlane_1',
            'bpmnElement': process_id
        })
        
        # موقعیت‌های المان‌ها
        positions = [
            (start_id, 100, 200),
        ]
        
        for i, (node_id, name) in enumerate(elements, 1):
            positions.append((node_id, 100 + i * 120, 200))
        
        positions.append((end_id, 100 + (len(elements) + 1) * 120, 200))
        
        for node_id, x, y in positions:
            shape = ET.SubElement(bpmn_plane, 'bpmndi:BPMNShape', {
                'id': f'BPMNShape_{node_id}',
                'bpmnElement': node_id
            })
            bounds = ET.SubElement(shape, 'dc:Bounds', {
                'x': str(x),
                'y': str(y),
                'width': '100',
                'height': '80'
            })
        
        # ذخیره فایل
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # تبدیل به string با فرمت زیبا
        xml_str = ET.tostring(root, encoding='utf-8')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        # حذف خط اول اضافی (<?xml version="1.0" ?>)
        lines = pretty_xml.split('\n')
        if lines and lines[0].strip().startswith('<?xml'):
            pretty_xml = '\n'.join(lines[1:])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        return output_path
    
    def generate_from_corrections(self, discoverer, corrections, output_path="output/process_model_ethical.bpmn"):
        """تولید BPMN از مدل اصلاح‌شده"""
        
        if discoverer:
            activities = discoverer.get_activities()
        else:
            activities = []
        
        # برچسب‌های اخلاقی
        ethical_notes = {}
        for act in activities:
            notes = []
            
            if 'ارزیابی' in act:
                notes.append("This activity has been made fair by removing sensitive attributes (gender).")
            elif 'بررسی' in act:
                notes.append("The review process is conducted with full transparency.")
            elif 'تأیید' in act or 'رد' in act:
                notes.append("Decision reasons are recorded transparently.")
            elif 'بازبینی' in act:
                notes.append("This activity allows users to appeal decisions.")
            elif 'تبعیض' in act:
                notes.append("This gateway prevents gender discrimination.")
            else:
                notes.append("This activity is designed with ethical principles.")
            
            ethical_notes[act] = "\n".join(notes)
        
        # اضافه کردن فعالیت‌های جدید از اصلاحات
        if corrections and 'new_activities' in corrections:
            for new_act in corrections['new_activities']:
                act_name = new_act.get('name', '')
                if act_name and act_name not in activities:
                    activities.append(act_name)
                    ethical_notes[act_name] = f"Ethical correction: {new_act.get('description', '')}"
        
        return self.generate(activities, ethical_notes, output_path)