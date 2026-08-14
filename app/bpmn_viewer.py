import streamlit as st
import os
import base64

def render_bpmn_viewer(bpmn_path):
    """
    نمایش فایل BPMN با استفاده از کتابخانه bpmn-js در Streamlit
    """
    
    if not os.path.exists(bpmn_path):
        st.error(f"❌ فایل BPMN در مسیر {bpmn_path} یافت نشد!")
        return
    
    with open(bpmn_path, 'r', encoding='utf-8') as f:
        bpmn_xml = f.read()
    
    # کد HTML برای نمایش BPMN با bpmn-js
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>نمایش BPMN</title>
        <script src="https://unpkg.com/bpmn-js@8.7.2/dist/bpmn-viewer.development.js"></script>
        <style>
            body {{ 
                margin: 0; 
                padding: 0; 
                direction: ltr; 
            }}
            #canvas {{
                height: 500px;
                border: 1px solid #ccc;
                border-radius: 8px;
                background: #fafafa;
            }}
            .bpmn-error {{
                color: red;
                padding: 20px;
                text-align: center;
                background: #ffe6e6;
                border-radius: 8px;
                margin: 10px 0;
            }}
            .bpmn-info {{
                color: #155724;
                padding: 10px;
                text-align: center;
                background: #d4edda;
                border-radius: 8px;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div id="canvas"></div>
        <div id="status"></div>
        <script>
            const xml = `{bpmn_xml}`;
            
            try {{
                const viewer = new BpmnViewer({{
                    container: '#canvas',
                    width: '100%',
                    height: '100%'
                }});
                
                viewer.importXML(xml, function(err) {{
                    if (err) {{
                        console.error('خطا در بارگذاری BPMN:', err);
                        document.getElementById('canvas').innerHTML = `
                            <div class="bpmn-error">
                                ❌ خطا در بارگذاری فایل BPMN:<br>
                                ${{err.message || 'خطای ناشناخته'}}
                            </div>
                        `;
                        return;
                    }}
                    
                    // بزرگنمایی خودکار برای نمایش کامل
                    const canvas = viewer.get('canvas');
                    canvas.zoom('fit-viewport');
                    
                    document.getElementById('status').innerHTML = `
                        <div class="bpmn-info">
                            ✅ فرآیند با موفقیت بارگذاری شد! 
                            تعداد فعالیت‌ها: ${{canvas.getRootElement().children.length || 'نامشخص'}}
                        </div>
                    `;
                }});
            }} catch(e) {{
                console.error('خطا:', e);
                document.getElementById('canvas').innerHTML = `
                    <div class="bpmn-error">
                        ❌ خطا در نمایش BPMN:<br>
                        ${{e.message || 'خطای ناشناخته'}}
                    </div>
                `;
            }}
        </script>
    </body>
    </html>
    """
    
    # نمایش در Streamlit
    st.components.v1.html(html_code, height=550, scrolling=True)