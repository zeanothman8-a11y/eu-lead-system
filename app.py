import streamlit as st
import re
import requests
from bs4 import BeautifulSoup
from google import genai

# إعدادات الصفحة
st.set_page_config(page_title="EU Lead Generator AI", page_icon="🎯", layout="wide")

st.title("🎯 نظام استخراج الإيميلات والتخصيص الذكي (للسوق الأوروبي)")
st.write("أدخل رابط موقع الشركة المستهدفة، وسيقوم النظام بفحص الصفحة، استخراج البريد الرسمي، وصياغة رسالة احترافية عبر Gemini.")

# إعداد مفتاح Gemini
client = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
    else:
        st.warning("⚠️ يرجى إعداد مفتاح Gemini API في إعدادات Secrets الخاصة بـ Streamlit.")
except Exception as e:
    st.warning("⚠️ تعذر تهيئة عميل Gemini.")

# مدخلات المستخدم
website_url = st.text_input("رابط موقع الشركة (مثال: https://example-company.de)", "")
company_description = st.text_area("وصف قصير عن نشاط الشركة أو الخدمة التي يقدمونها:", "")
user_service = st.text_area("خدمتك أو منتجك الذي تريد عرضه عليهم:", "خدمة تحسين العمليات البرمجية واللوجستية...")

if st.button("بدء الاستخراج والتوليد 🚀"):
    if not website_url:
        st.error("الرجاء إدخال رابط الموقع أولاً.")
    else:
        with st.spinner("جاري زحف الموقع وفحص صفحات الاتصال..."):
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            try:
                # 1. جلب بيانات الموقع الرئيسي
                response = requests.get(website_url, headers=headers, timeout=10)
                if response.status_code != 200:
                    st.error(f"تعذر الوصول للموقع. رمز الخطأ: {response.status_code}")
                else:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # البحث عن صفحة الاتصال أو من نحن أو Impressum
                    contact_urls = []
                    for a in soup.find_all('a', href=True):
                        text = a.get_text().lower()
                        href = a['href'].lower()
                        if any(term in text or term in href for term in ['contact', 'imprint', 'impressum', 'about', 'kontakt']):
                            link = a['href']
                            if link.startswith('http'):
                                contact_urls.append(link)
                            elif link.startswith('/'):
                                contact_urls.append(website_url.rstrip('/') + link)
                    
                    full_text = response.text
                    # زيارة أول رابطين للتواصل للتأكد من جمع البيانات
                    for c_url in list(set(contact_urls))[:2]:
                        try:
                            contact_resp = requests.get(c_url, headers=headers, timeout=10)
                            if contact_resp.status_code == 200:
                                full_text += " " + contact_resp.text
                        except:
                            pass
                    
                    # 2. استخراج وتصفية الإيميلات
                    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
                    raw_emails = set(re.findall(email_pattern, full_text))
                    
                    free_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com', 'example.com', 'wixpress.com']
                    clean_emails = []
                    
                    for email in raw_emails:
                        email_lower = email.lower()
                        domain = email_lower.split('@')[1]
                        if domain not in free_domains:
                            if not any(email_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.pdf', '.svg', '.webp']):
                                clean_emails.append(email_lower)
                    
                    clean_emails = list(set(clean_emails))
                    
                    # 3. عرض النتائج
                    st.success("تمت عملية الفحص بنجاح!")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📧 الإيميلات الرسمية المستخرجة:")
                        if clean_emails:
                            for em in clean_emails:
                                st.code(em)
                        else:
                            st.info("لم يتم العثور على بريد رسمي مباشر، يُرجى مراجعة صفحة 'Impressum' في الموقع يدوياً.")
                            
                    with col2:
                        st.subheader("🤖 مسودة الرسالة المقترحة (Gemini AI):")
                        if client:
                            prompt = f"""
                            أنت خبير تطوير أعمال موجه للشركات الصغيرة والمتوسطة في أوروبا.
                            صغ رسالة بريد إلكتروني أولية (Cold Email) باللغة الإنجليزية موجهة لشركة تعمل في هذا المجال: {company_description}
                            لعرض هذه الخدمة: {user_service}
                            الشروط: قصيرة جداً (4 أسطر كحد أقصى)، مهنية، بدون حماس مبالغ فيه أو كلمات سبام.
                            """
                            try:
                                # استخدام اسم الموديل المستقر المعتمد
                                ai_response = client.models.generate_content(
                                    model='gemini-3.5-flash-lite',
                                    contents=prompt,
                                )
                                st.text_area("الرسالة الجاهزة للإرسال:", ai_response.text, height=180)
                            except Exception as e:
                                st.error(f"حدث خطأ أثناء توليد الرسالة بالذكاء الاصطناعي: {e}")
                        else:
                            st.warning("أدخل مفتاح الـ API لتفعيل توليد الرسائل.")
                            
            except Exception as e:
                st.error(f"حدث خطأ أثناء فحص الموقع: {e}")
