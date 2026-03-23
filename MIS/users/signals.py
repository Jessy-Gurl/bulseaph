# users/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import HomepageContent

@receiver(post_migrate)
def create_default_homepage_content(sender, **kwargs):
    """Automatically create default homepage content after migration"""
    
    sections_data = [
        {
            'section_name': 'mensahe_ng_pinuno',
            'title': 'Mensahe ng Pinuno ng PSWDO',
            'content': '''
            <p><strong>Magandang araw sa inyong lahat!</strong></p>
            <p>Ang Provincial Social Welfare and Development Office (PSWDO) ay patuloy na nagtataguyod ng mga programang nakatuon sa pagpapalakas ng mga pamilya at pagtutulungan sa mga mahihirap. Ang aming misyon ay magbigay ng serbisyong may pagmamahal at pag-unawa sa bawat mamamayan.</p>
            <p>Salamat sa inyong suporta at pagtitiwala sa aming serbisyo.</p>
            <p><strong>- Pinuno ng PSWDO</strong></p>
            ''',
            'order': 1
        },
        {
            'section_name': 'department_head',
            'title': 'Department Heads',
            'content': '''
            <div class="department-card">
                <h3>Director</h3>
                <p>Dr. Juan Dela Cruz</p>
                <p>Director, PSWDO</p>
            </div>
            <div class="department-card">
                <h3>Assistant Director</h3>
                <p>Ms. Maria Santos</p>
                <p>Assistant Director</p>
            </div>
            <div class="department-card">
                <h3>Chief Social Worker</h3>
                <p>Mr. Pedro Reyes</p>
                <p>Chief Social Worker</p>
            </div>
            ''',
            'order': 2
        },
        {
            'section_name': 'vision',
            'title': 'Vision',
            'content': '<p>"Isang lipunang masaganang, mapayapa, at may pag-asa kung saan ang bawat pamilya ay may sapat na suporta at oportunidad para umunlad."</p>',
            'order': 3
        },
        {
            'section_name': 'mission',
            'title': 'Mission',
            'content': '<p>"Magbigay ng komprehensibong serbisyo sa panlipunan na nakatuon sa pagpapalakas ng mga pamilya, pagprotekta sa mga vulnerable na sektor, at pagpromote ng masustansyang buhay para sa lahat."</p>',
            'order': 4
        },
        {
            'section_name': 'mandates',
            'title': 'Mandates',
            'content': '''
            <div class="mf-box">
                <h3>Primary Mandates</h3>
                <ul>
                    <li>Pagpapatupad ng mga batas at patakaran sa panlipunan</li>
                    <li>Pagbibigay ng proteksyon sa mga vulnerable na sektor</li>
                    <li>Pagpapaunlad ng mga programa sa pagpapalakas ng pamilya</li>
                </ul>
            </div>
            <div class="mf-box">
                <h3>Secondary Mandates</h3>
                <ul>
                    <li>Pagsasagawa ng mga training at capacity building</li>
                    <li>Pagbuo ng mga partnership sa iba\'t ibang sektor</li>
                    <li>Pag-monitor at pag-evaluate ng mga programa</li>
                </ul>
            </div>
            ''',
            'order': 5
        },
        {
            'section_name': 'functions',
            'title': 'Functions',
            'content': '''
            <div class="mf-box">
                <h3>Planning & Development</h3>
                <ul>
                    <li>Pagsasagawa ng needs assessment</li>
                    <li>Pagpaplano ng mga programa at proyekto</li>
                    <li>Pag-aalok ng mga rekomendasyon</li>
                </ul>
            </div>
            <div class="mf-box">
                <h3>Implementation</h3>
                <ul>
                    <li>Pagtataguyod ng mga social welfare programs</li>
                    <li>Pagbibigay ng direct services</li>
                    <li>Pagpapatupad ng relief operations</li>
                </ul>
            </div>
            ''',
            'order': 6
        },
        {
            'section_name': 'programs_and_services',
            'title': 'Programs and Services',
            'content': '''
            <div class="program-card">
                <h4>4Ps Program</h4>
                <p>Pantawid Pamilyang Pilipino Program para sa mga pamilyang nasa kahirapan.</p>
            </div>
            <div class="program-card">
                <h4>Senior Citizen Benefits</h4>
                <p>Mga benepisyo at serbisyo para sa mga matatanda.</p>
            </div>
            <div class="program-card">
                <h4>Child Protection</h4>
                <p>Proteksyon at serbisyo para sa mga bata na nasa panganib.</p>
            </div>
            <div class="program-card">
                <h4>Women Empowerment</h4>
                <p>Mga programa para sa pagpapalakas ng mga kababaihan.</p>
            </div>
            <div class="program-card">
                <h4>Disaster Response</h4>
                <p>Relief operations at rehabilitation sa mga baha at kalamidad.</p>
            </div>
            <div class="program-card">
                <h4>Income Generation</h4>
                <p>Training at pondo para sa livelihood programs.</p>
            </div>
            ''',
            'order': 7
        },
        {
            'section_name': 'achievements',
            'title': 'Achievements',
            'content': '''
            <li><strong>2023:</strong> Pinakamagandang Social Welfare Office Award</li>
            <li><strong>2023:</strong> 500+ Families Benefited from 4Ps Program</li>
            <li><strong>2022:</strong> Successful Implementation of Senior Citizen Card</li>
            <li><strong>2022:</strong> Disaster Response Excellence Award</li>
            <li><strong>2021:</strong> Community-Based Rehabilitation Program Launch</li>
            ''',
            'order': 8
        },
        {
            'section_name': 'contact_information',
            'title': 'Contact Information',
            'content': '''
            <div class="contact-item">
                <h4>Address</h4>
                <p>Provincial Capitol Compound<br>City, Province, Philippines</p>
            </div>
            <div class="contact-item">
                <h4>Phone</h4>
                <p>(02) 123-4567<br>(02) 765-4321</p>
            </div>
            <div class="contact-item">
                <h4>Email</h4>
                <p>pswdo@province.gov.ph<br>info@pswdo.gov.ph</p>
            </div>
            <div class="contact-item">
                <h4>Office Hours</h4>
                <p>Monday - Friday<br>8:00 AM - 5:00 PM</p>
            </div>
            ''',
            'order': 9
        }
    ]
    
    created_count = 0
    for data in sections_data:
        if not HomepageContent.objects.filter(section_name=data['section_name']).exists():
            HomepageContent.objects.create(**data)
            created_count += 1
    
    if created_count > 0:
        print(f"✅ Created {created_count} default homepage sections!")