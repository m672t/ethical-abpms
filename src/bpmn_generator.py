"""
ماژول تولید BPMN 2.0 از Process Tree واقعی
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re

class BPMNGenerator:
    """تولید فایل BPMN 2.0 از Process Tree کشف‌شده توسط pm4py"""
    
    def __init__(self, process_name="EthicalProcess"):
        self.process_name = re.sub(r'[^a-zA-Z0-9_]', '_', process_name)
        self.ns = {
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
            'dc': 'http://www.omg.org/spec/DD/20100524/DC',
            'di': 'http://www.omg.org/spec/DD/20100524/DI'
        }
        self.node_counter = 0
        self.flow_counter = 0
        self.process = None
        self.elements = {}
        self.connections = []
        
    def _clean_id(self, text):
        """تبدیل نام به ID معتبر BPMN"""
        clean = re.sub(r'[^a-zA-Z0-9_]', '_', text)
        if clean and clean[0].isdigit():
            clean = 'id_' + clean
        return clean
    
    def _new_id(self, prefix):
        """تولید ID یکتا"""
        self.node_counter += 1
        return f"{prefix}_{self.node_counter:03d}"
    
    def _add_element(self, parent, tag, attrs=None):
        """افزودن المان به فرآیند با ID خودکار"""
        if attrs is None:
            attrs = {}
        if 'id' not in attrs:
            attrs['id'] = self._new_id(tag.split(':')[-1])
        elem = ET.SubElement(parent, tag, attrs)
        return elem
    
    def _add_flow(self, source, target):
        """افزودن sequenceFlow بین دو المان"""
        flow_id = f"Flow_{self.flow_counter:03d}"
        self.flow_counter += 1
        flow = ET.SubElement(self.process, 'bpmn:sequenceFlow', {
            'id': flow_id,
            'sourceRef': source,
            'targetRef': target
        })
        return flow
    
    def _convert_process_tree(self, parent_element, tree_node):
        """
        تبدیل recursive Process Tree به عناصر BPMN
        """
        # تشخیص نوع گره
        node_type = tree_node._operator if hasattr(tree_node, '_operator') else None
        
        if node_type is None:  # فعالیت (Leaf)
            # ایجاد Task
            task = ET.SubElement(self.process, 'bpmn:task', {
                'id': self._new_id('Activity'),
                'name': tree_node.label if hasattr(tree_node, 'label') else str(tree_node)
            })
            self.elements[task.get('id')] = task
            return task.get('id')
        
        elif node_type == 'sequence':  # توالی
            # XOR Gateway (محلی) برای کنترل توالی
            gateway = ET.SubElement(self.process, 'bpmn:exclusiveGateway', {
                'id': self._new_id('Gateway'),
                'gatewayDirection': 'Converging'
            })
            self.elements[gateway.get('id')] = gateway
            
            last_id = gateway.get('id')
            for child in tree_node._children:
                child_id = self._convert_process_tree(parent_element, child)
                # اتصال از گیت‌وی به اولین child
                self._add_flow(last_id, child_id)
                last_id = child_id
            
            return gateway.get('id')
        
        elif node_type == 'xor':  # XOR (انتخاب)
            # Exclusive Gateway (شاخه‌ها)
            gateway = ET.SubElement(self.process, 'bpmn:exclusiveGateway', {
                'id': self._new_id('Gateway'),
                'gatewayDirection': 'Diverging'
            })
            self.elements[gateway.get('id')] = gateway
            
            for child in tree_node._children:
                child_id = self._convert_process_tree(parent_element, child)
                # اتصال از گیت‌وی به هر child (با شرط)
                self._add_flow(gateway.get('id'), child_id)
            
            return gateway.get('id')
        
        elif node_type == 'and':  # AND (همزمان)
            # Parallel Gateway
            gateway = ET.SubElement(self.process, 'bpmn:parallelGateway', {
                'id': self._new_id('Gateway'),
                'gatewayDirection': 'Diverging'
            })
            self.elements[gateway.get('id')] = gateway
            
            for child in tree_node._children:
                child_id = self._convert_process_tree(parent_element, child)
                self._add_flow(gateway.get('id'), child_id)
            
            return gateway.get('id')
        
        elif node_type == 'loop':  # حلقه
            # XOR Gateway با مسیر برگشتی
            start_gateway = ET.SubElement(self.process, 'bpmn:exclusiveGateway', {
                'id': self._new_id('Gateway'),
                'gatewayDirection': 'Diverging'
            })
            self.elements[start_gateway.get('id')] = start_gateway
            
            # بدن حلقه
            body_id = self._convert_process_tree(parent_element, tree_node._children[0])
            
            # گیت‌وی خاتمه
            end_gateway = ET.SubElement(self.process, 'bpmn:exclusiveGateway', {
                'id': self._new_id('Gateway'),
                'gatewayDirection': 'Converging'
            })
            self.elements[end_gateway.get('id')] = end_gateway
            
            # اتصال start → body → end
            self._add_flow(start_gateway.get('id'), body_id)
            self._add_flow(body_id, end_gateway.get('id'))
            
            # مسیر بازگشت (حلقه)
            self._add_flow(end_gateway.get('id'), start_gateway.get('id'))
            
            return start_gateway.get('id')
        
        else:
            # Fallback: فقط child اول رو برگردون
            if hasattr(tree_node, '_children') and tree_node._children:
                return self._convert_process_tree(parent_element, tree_node._children[0])
            return None
    
    def generate(self, process_tree, ethical_notes=None, output_path="output/process_model.bpmn"):
        """
        تولید فایل BPMN 2.0 از Process Tree
        """
        if ethical_notes is None:
            ethical_notes = {}
        
        # ریشه BPMN
        root = ET.Element('bpmn:definitions', {
            'xmlns:bpmn': self.ns['bpmn'],
            'xmlns:bpmndi': self.ns['bpmndi'],
            'xmlns:dc': self.ns['dc'],
            'xmlns:di': self.ns['di'],
            'targetNamespace': 'http://bpmn.io/schema/bpmn',
            'id': 'Definitions_1'
        })
        
        # Process
        process_id = f'Process_{self.process_name}'
        self.process = ET.SubElement(root, 'bpmn:process', {
            'id': process_id,
            'isExecutable': 'true',
            'name': self.process_name
        })
        
        # Start Event
        start_id = self._new_id('StartEvent')
        start = ET.SubElement(self.process, 'bpmn:startEvent', {
            'id': start_id,
            'name': 'شروع'
        })
        self.elements[start_id] = start
        
        # تبدیل Process Tree
        last_id = start_id
        if process_tree is not None:
            tree_id = self._convert_process_tree(self.process, process_tree)
            if tree_id:
                self._add_flow(last_id, tree_id)
                last_id = tree_id
        
        # End Event
        end_id = self._new_id('EndEvent')
        end = ET.SubElement(self.process, 'bpmn:endEvent', {
            'id': end_id,
            'name': 'پایان'
        })
        self.elements[end_id] = end
        self._add_flow(last_id, end_id)
        
        # اضافه کردن برچسب‌های اخلاقی (Documentation)
        for elem_id, elem in self.elements.items():
            if elem.tag == 'bpmn:task' and elem.get('name') in ethical_notes:
                doc = ET.SubElement(elem, 'bpmn:documentation')
                doc.text = ethical_notes[elem.get('name')]
        
        # BPMN DI (موقعیت‌ها)
        bpmndi = ET.SubElement(root, 'bpmndi:BPMNDiagram', {'id': 'BPMNDiagram_1'})
        plane = ET.SubElement(bpmndi, 'bpmndi:BPMNPlane', {
            'id': 'BPMNPlane_1',
            'bpmnElement': process_id
        })
        
        # موقعیت‌دهی ساده (می‌توانید بهینه کنید)
        for i, (elem_id, elem) in enumerate(self.elements.items()):
            shape = ET.SubElement(plane, 'bpmndi:BPMNShape', {
                'id': f'BPMNShape_{elem_id}',
                'bpmnElement': elem_id
            })
            bounds = ET.SubElement(shape, 'dc:Bounds', {
                'x': str(100 + i * 120),
                'y': '200',
                'width': '100',
                'height': '80'
            })
        
        # ذخیره فایل
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        xml_str = ET.tostring(root, encoding='utf-8')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        # حذف خط اول اضافی
        lines = pretty_xml.split('\n')
        if lines and lines[0].strip().startswith('<?xml'):
            pretty_xml = '\n'.join(lines[1:])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        return output_path
