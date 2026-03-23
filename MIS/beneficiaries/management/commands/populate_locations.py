# beneficiaries/populate_districts.py
from beneficiaries.models import District, Municipality, Barangay
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Populate Bulacan districts, municipalities, and barangays'

    def handle(self, *args, **options):
        self.stdout.write('Populating Bulacan locations...')

districts_munis = {
    "1st DISTRICT": ["Bulakan", "Calumpit", "Hagonoy", "City of Malolos", "Paombong", "Pulilan"],
    "2nd DISTRICT": ["City of Baliwag", "Bustos", "Plaridel"],
    "3rd DISTRICT": ["Doña Remedios Trinidad", "San Ildefonso", "San Miguel", "San Rafael"],
    "4th DISTRICT": ["Marilao", "City of Meycauayan", "Obando"],
    "5th DISTRICT": ["Balagtas", "Bocaue", "Guiguinto", "Pandi"],
    "6th DISTRICT": ["Angat", "Norzagaray", "Santa Maria"],
    "LONE DISTRICT OF SAN JOSE DEL MONTE": ["San Jose del Monte"],
}

municipality_barangays = {
    #1st DISTRICT
     "Bulakan": [
        "Bagumbayan", "Balubad", "Bambang", "Matungao", "Maysantol", "Perez",
        "Pitpitan", "San Francisco", "San Jose (Poblacion)", "San Nicolas", "Santa Ana",
        "Santa Ines", "Taliptip", "Tibig"
    ],
    "Calumpit": [
        "Balite", "Balungao", "Buguion", "Bulusan", "Calizon", "Calumpang", "Caniogan",
        "Meysulao", "Meyto", "Palimbang", "Panducot", "Pio Cruzcosa", "Poblacion",
        "Pungo", "San Jose", "San Marcos", "San Miguel", "Santa Lucia", "Santo Niño",
        "Sapang Bayan", "Sergio Bayan", "Sucol"
    ],
    "Hagonoy": [
        "Abulalas", "Carillo", "Iba", "Iba-Ibayo", "Mercado", "Palapat", "Pugad",
        "Sagrada Familia", "San Agustin", "San Isidro", "San Jose", "San Juan",
        "San Miguel", "San Nicolas", "San Pablo", "San Pascual", "San Pedro",
        "San Roque", "San Sebastian", "Santa Cruz", "Santa Elena", "Santa Monica",
        "Santo Niño", "Santo Rosario", "Tampok", "Tibaguin"
    ],
    "City of Malolos": [
        "Anilao", "Atlag", "Babatnin", "Bagna", "Bagong Bayan", "Balayong", "Balite",
        "Bangkal", "Barihan", "Bulihan", "Bungahan", "Caingin", "Calero", "Caliligawan",
        "Canalate", "Caniogan", "Catmon", "Cofradia", "Dakila", "Guinhawa", "Liang",
        "Ligas", "Longos", "Look 1st", "Look 2nd", "Lugam", "Mabolo", "Mambog",
        "Masile", "Matimbo", "Mojon", "Namayan", "Niugan", "Pamarawan", "Panasahan",
        "Pinagbakahan", "San Agustin", "San Gabriel", "San Juan", "San Pablo",
        "San Vicente (formerly Poblacion)", "Santiago", "Santisima Trinidad",
        "Santo Cristo", "Santo Niño (formerly Poblacion)", "Santo Rosario (formerly Poblacion)",
        "Santor", "Sumapang Bata", "Sumapang Matanda", "Taal", "Tikay"
    ],
    "Paombong": [
        "Binakod", "Kapitangan", "Malumot", "Masukol", "Pinalagdan", "Poblacion",
        "San Isidro I", "San Isidro II", "San Jose", "San Roque", "San Vicente",
        "Santa Cruz", "Santo Niño", "Santo Rosario"
    ],
    "Pulilan": [
        "Balatobg A", "Balatong B", "Cutcot", "Dampol 1st", "Dampol 2nd A", "Dampol 2nd B",
        "Dulong Malabon", "Inaon", "Longos", "Lumbac", "Paltao", "Peñabatan", "Poblacion",
        "Sta. Peregrina", "Sto. Cristo", "Taal", "Tabon", "Tibag", "Tinejero"
    ],

    #2st DISTRICT
    "City of Baliwag": [
        "Bagong Nayon", "Bangkong Malapad", "Barangca", "Calantipay", "Catulinan",
        "Concepcion", "Hinukay", "Makinabang", "Matangtubig", "Pagala", "Paitan",
        "Panginay", "Parian", "Piel", "Pinagbarilan", "Poblacion", "San Jose", "San Roque",
        "Santa Barbara", "Santo Cristo", "Santo Niño", "Subic", "Sulivan", "Tangos",
        "Tarcan", "Tibag", "Tilapayong"
    ],
    "Bustos": [
        "Bonga Mayor", "Bonga Menor", "Buisan", "Camachilihan", "Cambaog",
        "Dalig", "Liciada", "Malamig", "Malawak", "Perez", "Poblacion",
        "San Pedro", "Tanawan", "Tindahan"
    ],
    "Plaridel": [
        "Agnaya", "Bagong Silang", "Banga I", "Banga II", "Bintog", "Bulihan", "Culianin",
        "Dampol", "Lagundi", "Lalangan", "Lumang Bayan", "Parulan", "Poblacion",
        "Rueda", "San Jose", "Santa Ines", "Santo Niño", "Sipat", "Tabang"
    ],

    #3st DISTRICT
    "Doña Remedios Trinidad": [
        "Bayabas", "Camachin", "Camachile", "Camada", "Kabayunan", "Kalawakan",
        "Pulong Sampalok", "Sapang Bulak", "Talbak"
    ],
    "San Ildefonso": [
        "Akle", "Alagao", "Anyatam", "Asper", "Basuit", "Bularit", "Bungad",
        "Cabugao", "Calasag", "Calawitan", "Garlang", "Gabihan", "Lapnit", "Malipampang",
        "Malolos", "Matimbubong", "Nabaong Garlang", "Pala-pala", "Pampangin", "Pasong Bangkal",
        "Pasong Intsik", "Pinaod", "Poblacion", "Pulong Tamo", "Sapang Dayap", "Sapang Putik",
        "Sapang Putol", "Santa Catalina Bata", "Santa Catalina Matanda", "Santo Cristo",
        "Santo Niño", "Sapa", "Telepatio", "Tibag", "Umpucan", "Upig"
    ],
    "San Miguel": [
        "Bagong Bayan", "Bagong Pag-asa", "Balaong", "Balite", "Baluarte",
        "Bantog", "Baritan", "Baybay", "Biak-na-Bato", "Bigo", "Bantog Norte",
        "Bantog Sur", "Buliran", "Camias", "Ibayong Ilog", "Lambakin", "Malibay",
        "Mandile", "Maliwalo", "Masalipit", "Malipampang", "Magmarale", "Paliwas",
        "Partida", "Poblacion", "Pulo", "Pacalcal", "Paitan", "Salacot", "San Agustin",
        "San Jose", "San Juan", "San Vicente", "Santa Inez", "Santa Lucia", 
        "Santa Rita Bata", "Santa Rita Matanda", "Santo Niño", "Sapang", "Sibul",
        "Sacdalan", "San Pablo", "Sapang Putol", "Santo Rosario", "Sta. Monica",
        "Tigpalas", "Tuzon", "Tartaro", "Umiray"
    ],
    "San Rafael": [
        "Balagtas", "Caingin", "Coral na Bato", "Cruz na Daan", "Dagat-Dagatan", "Capihan",
        "Diliman I", "Diliman II", "Gabihan", "Kagongkong", "Karla", "Licub", "Ligang",
        "Maronquillo", "Masantol", "Maasim", "Pantubig", "Pasong Bangkal", "Pasong Callos",
        "Pasong Intsik", "Poblacion", "Punta Norte", "Punta Sur", "Pantubig Poblacion",
        "Pasong Bangkal Poblacion", "Sapang Putik", "Sampaloc", "San Agustin", "San Roque",
        "Tambubong", "Talacsan", "Tambubong Poblacion", "Tibagan", "Ulingao"
    ],

    #4th DISTRICT
    "Marilao": [
        "Abangan Norte", "Abangan Sur", "Ibayo", "Lambakin", "Lias", "Loma de Gato",
        "Nagbalon", "Patubig", "Poblacion I", "Poblacion II", "Prenza I", "Prenza II",
        "Saog", "Sta. Rosa I", "Sta. Rosa II", "Tabing Ilog"
    ],
    "City of Meycauayan": [
        "Bagbaguin", "Bahay Pare", "Bancal", "Bayugo", "Bangcal", "Caingin", "Calvario",
        "Camalig", "Dulong Bayan", "Hulo", "Iba", "Langka", "Lawa", "Liputan", "Longos",
        "Malhacan", "Pandayan", "Pantoc", "Perez", "Poblacion", "Paso de Blas", "Pantalan",
        "Saluysoy", "Tugatog", "Ubihan", "Zamora"
    ],
    "Obando": [
        "Binuangan", "Catanghalan", "Hulo", "Lawa", "Paco", "Pag-asa (formerly Poblacion)",
        "Paliwas", "Panghulo", "Salambao", "San Pascual", "Tawiran"
    ],

    #5th DISTRICT
    "Balagtas": [
        "Borol 1st", "Borol 2nd", "Dalig", "Longos", "Panginay", "Pulong Gubat",
        "San Juan", "Santol", "Wawa"
    ],
    "Bocaue": [
        "Antipona", "Bagumbayan", "Bambang", "Batia", "Biñang 1st", "Biñang 2nd",
        "Bolacan", "Bundukan", "Bunlo", "Caingin", "Duhat", "Igulot", "Lolomboy",
        "Poblacion", "Sulucan", "Taal", "Tambobong", "Turo", "Wakas"
    ],
    "Guiguinto": [
        "Cutcut", "Daungan", "Ilang-Ilang", "Malis", "Panginay", "Poblacion",
        "Pritil", "Pulong Gubat", "Santa Cruz", "Santa Rita", "Tabang", "Tabe",
        "Tiaong", "Tuktukan"
    ],
    "Pandi": [
        "Bagbaguin", "Bagong Barrio", "Baka-Bakahan", "Bunsuran I", "Bunsuran II",
        "Bunsuran III", "Cacarong Bata", "Cacarong Matanda", "Cupang", "Malibong Bata",
        "Malibong Matanda", "Manatal", "Mapulang Lupa", "Masagana", "Masuso",
        "Pinagkuartelan", "Poblacion", "Real de Cacarong", "San Roque", "Santo Niño",
        "Siling Bata", "Siling Matanda"
    ],

    #6th DISTRICT
     "Angat": [
        "Banaban", "Baybay", "Binagbag", "Donacion", "Encanto", "Laog",
        "Marungko", "Niugan", "Paltok", "Pulong", "San Roque (Poblacion)",
        "Santa Cruz (Poblacion) -Santa Lucia", "Santo Cristo (Poblacion) -Sulucan",
        "Taboc", "Yantok"
    ],
    "Norzagaray": [
        "Bigte", "Bitungol", "Friendship Village Resources (FVR)", "Matictic",
        "Minuyan", "North Hills Village", "Paradise III", "Partida", "Pinagtulayan",
        "Poblacion", "San Lorenzo", "San Mateo", "Tigbe"
    ],
    "Santa Maria": [
        "Bagbaguin", "Balasing", "Buenavista", "Bulac", "Camangyanan", "Catmon",
        "Caypombo", "Caysio", "Dulong Bayan", "Guyong", "Lalakhan", "Mag-asawang Sapa",
        "Mahabang Parang", "Manggahan", "Parada", "Poblacion", "Pulong Buhangin",
        "San Gabriel", "San Jose Patag", "San Vicente", "Santa Clara", "Santa Cruz",
        "Silangan", "Tumana"
    ],

    #LONE DISTRICT OF SAN JOSE DEL MONTE
    "San Jose del Monte": [
        "Assumption", "Bagong Buhay I", "Bagong Buhay II", "Bagong Buhay III",
        "Citrus", "Ciudad Real", "Dulong Bayan", "Fatima", "Fatima II", "Fatima III",
        "Fatima IV", "Fatima V", "Francisco Homes - Guijo", "Francisco Homes - Mulawin",
        "Francisco Homes - Narra", "Francisco Homes - Yakal", "Gaya-Gaya", "Graceville",
        "Gumaoc Central", "Gumaoc East", "Gumaoc West", "Kaybanban", "Kaypian", "Lawang Pari",
        "Maharlika", "Minuyan", "Minuyan II", "Minuyan III", "Minuyan IV", "Minuyan Proper",
        "Minuyan V", "Muzon East", "Muzon Proper", "Muzon South", "Muzon West", "Paradise III",
        "Poblacion", "Poblacion I", "Saint Martin de Porres", "San Isidro", "San Manuel",
        "San Martin I", "San Martin II", "San Martin III", "San Martin IV", "San Pedro",
        "San Rafael I", "San Rafael II", "San Rafael III", "San Rafael IV", "San Rafael V",
        "San Roque", "Santa Cruz I", "Santa Cruz II", "Santa Cruz III", "Santa Cruz IV",
        "Santa Cruz V", "Santo Cristo", "Santo Niño I", "Santo Niño II", "Sapang Palay",
        "Tungkong Mangga"
    ]
}

for district_name, municipalities in districts_munis.items():
    district_obj, created = District.objects.get_or_create(name=district_name)
    for muni in municipalities:
        Municipality.objects.get_or_create(name=muni, district=district_obj)

print("Districts and municipalities added!")

for muni_name, barangays in municipality_barangays.items():
    municipality_obj = Municipality.objects.get(name=muni_name)
    for barangay_name in barangays:
        Barangay.objects.get_or_create(name=barangay_name, municipality=municipality_obj)
    print(f"Barangays for {muni_name} added!")
