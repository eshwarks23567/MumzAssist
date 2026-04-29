"""
Generates synthetic but realistic Mumzworld product + order data.
Products span all 15 navigation categories seen on mumzworld.com.
Run: python scripts/generate_data.py
"""

import json
import random
from pathlib import Path

random.seed(42)

# ── 1. PRODUCTS ────────────────────────────────────────────────────────────────

RAW_PRODUCTS = [
    # ── GEAR: Strollers ──────────────────────────────────────────────────────
    ("P-STR-001","Cybex Gazelle S Stroller","عربة أطفال سايبكس غازيل إس","gear",2199,True,30,24,"0–4y"),
    ("P-STR-002","Bugaboo Fox 5 Stroller","عربة أطفال بوغابو فوكس 5","gear",3850,True,30,24,"0–4y"),
    ("P-STR-003","UPPAbaby Vista V2 Stroller","عربة أطفال أبابيبي فيستا في2","gear",3299,True,30,24,"0–5y"),
    ("P-STR-004","Silver Cross Wave 2 Stroller","عربة أطفال سيلفر كروس ويف 2","gear",3650,True,30,24,"0–4y"),
    ("P-STR-005","Joie Versatrax Stroller","عربة أطفال جوي فيرساتراكس","gear",1399,True,30,24,"0–4y"),
    ("P-STR-006","Chicco Urban Plus Stroller","عربة أطفال شيكو أوربان بلس","gear",1199,True,30,24,"0–3y"),
    ("P-STR-007","Graco Modes Element Stroller","عربة أطفال غراكو موودز إليمنت","gear",849,True,30,24,"0–4y"),
    ("P-STR-008","Maxi-Cosi Leona² Pushchair","عربة أطفال ماكسي كوسي ليونا2","gear",1750,True,30,24,"0–4y"),
    # ── GEAR: Car Seats ──────────────────────────────────────────────────────
    ("P-CAR-001","Maxi-Cosi Pebble 360 Pro Car Seat","كرسي سيارة ماكسي كوسي بيبل 360 برو","gear",1650,True,30,24,"0–12m"),
    ("P-CAR-002","Joie i-Spin 360 Car Seat","كرسي سيارة جوي آي-سبين 360","gear",1299,True,30,24,"0–4y"),
    ("P-CAR-003","Cybex Cloud G i-Size Car Seat","كرسي سيارة سايبكس كلاود جي","gear",1850,True,30,24,"0–24m"),
    ("P-CAR-004","BeSafe iZi Go Modular i-Size","كرسي سيارة بيسيف آيزي جو","gear",1499,True,30,24,"0–18m"),
    ("P-CAR-005","Graco 4Ever DLX 4-in-1 Car Seat","كرسي سيارة غراكو 4 في 1","gear",999,True,30,12,"0–10y"),
    # ── GEAR: Carriers ───────────────────────────────────────────────────────
    ("P-CAR-006","BabyBjörn Harmony Baby Carrier","حامل أطفال بيبي بيورن هارموني","gear",699,True,30,12,"0–3y"),
    ("P-CAR-007","Ergobaby Omni 360 Cool Air Carrier","حامل أطفال إرغوبيبي أومني 360","gear",549,True,30,12,"0–4y"),
    # ── BEDROOM ──────────────────────────────────────────────────────────────
    ("P-BED-001","Chicco Next2Me Magic Bedside Crib","سرير شيكو نكست 2 مي ماجيك","bedroom",1499,True,30,24,"0–6m"),
    ("P-BED-002","Stokke Sleepi Crib + Mattress","سرير ستوكي سليبي مع مرتبة","bedroom",3299,True,30,24,"0–10y"),
    ("P-BED-003","Maxi-Cosi Iora Bedside Crib","سرير ماكسي كوسي آيورا","bedroom",1099,True,30,24,"0–6m"),
    ("P-BED-004","IKEA SNIGLAR Crib","سرير IKEA سنيغلار","bedroom",299,True,30,12,"0–5y"),
    ("P-BED-005","aden+anais Organic Muslin Swaddle 4-Pack","ملفّات موسلين ادن+أناييس عضوية (4 قطع)","bedroom",189,True,30,0,"0–6m"),
    ("P-BED-006","Tommee Tippee Sleeptime Lite Night Light","مصباح ليلي توميه تيبي","bedroom",149,True,30,12,"0+"),
    ("P-BED-007","Aerosleep Evolution Pack (mattress+cover)","مرتبة أيروسليب مع غطاء","bedroom",899,True,30,12,"0–2y"),
    ("P-BED-008","Gravity Baby Sleep Sack 0–6M","كيس نوم غرافيتي 0–6 أشهر","bedroom",149,True,30,0,"0–6m"),
    # ── FEEDING ──────────────────────────────────────────────────────────────
    ("P-FED-001","Philips Avent Natural Bottle 260ml 3-pack","زجاجة فيليبس أفنت 260 مل (3 قطع)","feeding",89,True,30,0,"0+"),
    ("P-FED-002","Dr. Brown's Natural Flow Bottle Set 4-pack","طقم زجاجات دكتور براون (4 قطع)","feeding",149,True,30,0,"0+"),
    ("P-FED-003","Tommee Tippee Closer to Nature Bottle","زجاجة توميه تيبي الطبيعية","feeding",69,True,30,0,"0+"),
    ("P-FED-004","Medela Pump In Style Advanced","شفاطة ميديلا بامب إن ستايل","feeding",1149,False,0,12,"Nursing"),
    ("P-FED-005","Spectra S1 Plus Double Breast Pump","شفاطة سبيكترا S1 مزدوجة","feeding",899,False,0,12,"Nursing"),
    ("P-FED-006","Haakaa Silicone Breast Pump 150ml","شفاطة هاكا سيليكون 150 مل","feeding",79,True,30,0,"Nursing"),
    ("P-FED-007","Aptamil Profutura Stage 1 800g","حليب أبتاميل بروفيوتورا مرحلة 1 800 جم","feeding",189,False,0,0,"0–6m"),
    ("P-FED-008","NAN Supreme Stage 1 900g","حليب نان سوبريم مرحلة 1 900 جم","feeding",175,False,0,0,"0–6m"),
    ("P-FED-009","Stokke Tripp Trapp High Chair","كرسي مرتفع ستوكي تريب تراب","feeding",1299,True,30,36,"6m–adult"),
    ("P-FED-010","Chicco Polly 2-in-1 Highchair","كرسي مرتفع شيكو بولي 2 في 1","feeding",549,True,30,12,"6m–3y"),
    ("P-FED-011","Summer Infant Pop n Sit Booster","كرسي تعزيز محمول سامر إنفانت","feeding",249,True,30,12,"6m–3y"),
    ("P-FED-012","Munchkin LATCH Bottle Warmer","سخان زجاجات مانشكين","feeding",149,True,30,12,"0+"),
    # ── TOYS ─────────────────────────────────────────────────────────────────
    ("P-TOY-001","Fisher-Price Rainforest Jumperoo","جهاز قفز فيشر برايس رين فورست","toys",399,False,30,12,"4–12m"),
    ("P-TOY-002","LEGO DUPLO Classic Brick Box 85pcs","مكعبات ليغو دوبلو كلاسيك (85 قطعة)","toys",199,True,30,0,"1.5–5y"),
    ("P-TOY-003","VTech Sit-to-Stand Learning Walker","مشاية VTech للتعلم","toys",289,True,30,12,"9m–3y"),
    ("P-TOY-004","Hape Pound & Tap Bench","طاولة الطرق هاب","toys",129,True,30,0,"12m+"),
    ("P-TOY-005","Skip Hop Activity Gym","سجادة نشاط سكيب هوب","toys",349,True,30,0,"0–12m"),
    ("P-TOY-006","Melissa & Doug Deluxe Wooden A-Z Puzzle","لغز الأبجدية الخشبي ميليسا ودوغ","toys",119,True,30,0,"3–6y"),
    ("P-TOY-007","Infantino Flip 4-in-1 Carrier + Gym","حامل وسجادة إنفانتينو 4 في 1","toys",249,True,30,0,"0–12m"),
    ("P-TOY-008","Bright Starts Bounce Bouncer","أرجوحة برايت ستارتس","toys",299,True,30,12,"0–6m"),
    # ── DIAPERS ──────────────────────────────────────────────────────────────
    ("P-DIA-001","Pampers Premium Care Diapers NB 80pcs","حفاضات بامبرز بريميوم NB 80 قطعة","diapers",89,True,30,0,"NB"),
    ("P-DIA-002","Pampers Premium Care Diapers Size 3 120pcs","حفاضات بامبرز بريميوم مقاس 3","diapers",99,True,30,0,"4–9kg"),
    ("P-DIA-003","Huggies Platinum Diapers Size 4 84pcs","حفاضات هاغيز بلاتينيوم مقاس 4","diapers",95,True,30,0,"7–18kg"),
    ("P-DIA-004","Mamypoko Pants Size M 62pcs","حفاضات مامي بوكو إم 62 قطعة","diapers",79,True,30,0,"7–10kg"),
    ("P-DIA-005","WaterWipes Fragrance-Free Baby Wipes 9-pack","مناديل ويتر وايبز بدون عطر (9 علب)","diapers",149,True,30,0,"0+"),
    ("P-DIA-006","Mustela Diaper Rash Cream 123","كريم الطفح الجلدي موستيلا 123","diapers",79,True,30,0,"0+"),
    # ── OUTDOOR ──────────────────────────────────────────────────────────────
    ("P-OUT-001","Phil & Teds Explorer Inline Stroller","عربة فيل آند تيدز اكسبلورر","outdoor",2199,True,30,24,"0–5y"),
    ("P-OUT-002","Ergobaby Metro+ Compact Stroller","عربة إرغوبيبي مترو+ المدمجة","outdoor",1549,True,30,24,"0–4y"),
    ("P-OUT-003","Sunstyle UV Protection Swimsuit Baby","بدلة سباحة للأطفال بحماية UV","outdoor",119,True,30,0,"0–4y"),
    ("P-OUT-004","Babymoov Freshness Lunch Bag","حقيبة طعام بيبيموف فريشنيس","outdoor",149,True,30,0,"all"),
    # ── BATH ─────────────────────────────────────────────────────────────────
    ("P-BAT-001","Stokke Flexi Bath Foldable Tub","حوض استحمام ستوكي فليكسي قابل للطي","bath",219,True,30,0,"0–4y"),
    ("P-BAT-002","Fisher-Price 4-in-1 Sling n Seat Tub","حوض استحمام فيشر برايس 4 في 1","bath",179,True,30,0,"0–3y"),
    ("P-BAT-003","Mustela Gentle Cleansing Gel 500ml","جل تنظيف موستيلا اللطيف 500 مل","bath",69,True,30,0,"0+"),
    ("P-BAT-004","Bioderma ABCDerm Cleansing Gel 200ml","جل تنظيف بيوديرما ABCDerm","bath",55,True,30,0,"0+"),
    ("P-BAT-005","Safety 1st Tub","حوض استحمام سيفتي فيرست","bath",99,True,30,0,"0–1y"),
    ("P-BAT-006","Chicco Baby Hug Bath & Relax","استحمام ومرخ شيكو بيبي هاغ","bath",149,True,30,0,"0–6m"),
    # ── SAFETY ───────────────────────────────────────────────────────────────
    ("P-SAF-001","Motorola VM65 Baby Monitor","جهاز مراقبة أطفال موتورولا VM65","safety",549,True,30,12,"0–3y"),
    ("P-SAF-002","Nanit Pro Smart Baby Monitor","جهاز مراقبة أطفال ذكي نانيت برو","safety",1299,True,30,12,"0–5y"),
    ("P-SAF-003","Safety 1st Extra Tall Walk-Thru Gate","بوابة أمان سيفتي فيرست","safety",299,True,30,12,"6m–2y"),
    ("P-SAF-004","BabyDan Multidan Safety Gate","بوابة سلامة بيبي دان","safety",349,True,30,12,"6m–2y"),
    ("P-SAF-005","Braun ThermoScan 7 Ear Thermometer","مقياس حرارة براون للأذن","safety",279,True,30,24,"0+"),
    # ── FASHION / CLOTHING ───────────────────────────────────────────────────
    ("P-CLO-001","Mamas & Papas Sleepsuit 3-Pack (0–3M)","بدلة نوم ماماز آند باباز (0–3 أشهر)","fashion",125,True,30,0,"0–3m"),
    ("P-CLO-002","Carter's 5-Pack Bodysuits (6M)","بدلات كارترز (5 قطع) 6 أشهر","fashion",139,True,30,0,"6m"),
    ("P-CLO-003","Purebaby Organic Onesie 6-Pack","بدلات بيورباي العضوية (6 قطع)","fashion",215,True,30,0,"0–12m"),
    ("P-CLO-004","H&M Baby Cotton Set (top+pants)","طقم قطن H&M للأطفال","fashion",89,True,30,0,"3–24m"),
    ("P-CLO-005","Mothercare All Stars Socks 7-Pack","جوارب ماذركير أولستار (7 قطع)","fashion",45,True,30,0,"0–24m"),
    # ── MUMZ (Maternity) ─────────────────────────────────────────────────────
    ("P-MUM-001","Belabumbum Maternity Nightgown","قميص نوم للحوامل بيلابمبوم","mumz",249,True,30,0,"Maternity"),
    ("P-MUM-002","Lansinoh Nipple Cream 40ml","كريم الحلمة لانسينو 40 مل","mumz",69,True,30,0,"Nursing"),
    ("P-MUM-003","Carriwell Seamless Drop-Cup Nursing Bra","حمالة صدر للرضاعة كارييويل","mumz",159,True,30,0,"Nursing"),
    # ── PHARMACY ─────────────────────────────────────────────────────────────
    ("P-PHA-001","Calpol Infant Suspension 100ml","معلق كالبول للرضع 100 مل","pharmacy",25,True,14,0,"3m+"),
    ("P-PHA-002","Nelsons Teetha Granules 24 sachets","حبيبات نيلسونز تيثا للتسنين","pharmacy",49,True,14,0,"3m+"),
    ("P-PHA-003","FridaBaby NoseFrida Snot Sucker","شافطة أنف فريدا بيبي","pharmacy",89,True,30,0,"0+"),
    ("P-PHA-004","Gripe Water 150ml","ماء الريح 150 مل","pharmacy",35,True,14,0,"4w+"),
    ("P-PHA-005","Mama's Choice Vitamin D Drops","قطرات فيتامين D ماما تشويس","pharmacy",79,True,30,0,"0+"),
    # ── HOME ─────────────────────────────────────────────────────────────────
    ("P-HOM-001","Storksak Alyssa Leather Changing Bag","حقيبة التغيير الجلدية ستوركساك","home",895,True,30,12,"all"),
    ("P-HOM-002","Summer Infant Deluxe SuperSeat","مقعد سوبر سيت سامر إنفانت","home",299,True,30,12,"6–18m"),
    ("P-HOM-003","Diono Ultra Dry Seat Waterproof Liner","بطانة مقعد مضادة للماء دايونو","home",149,True,30,0,"all"),
    # ── BOOKS ────────────────────────────────────────────────────────────────
    ("P-BOK-001","The Very Hungry Caterpillar (Board Book)","دودة الجوع الشديدة (كتاب مقوى)","books",35,True,30,0,"0–5y"),
    ("P-BOK-002","Goodnight Moon (Board Book)","تصبح على خير يا قمر","books",39,True,30,0,"0–3y"),
    ("P-BOK-003","Arabic Alphabet Flash Cards","بطاقات تعليمية الحروف العربية","books",65,True,30,0,"2–6y"),
    # ── PARTY ────────────────────────────────────────────────────────────────
    ("P-PAR-001","My 1st Birthday Party Kit (Pink)","طقم عيد الميلاد الأول (وردي)","party",129,True,30,0,"all"),
    ("P-PAR-002","Gender Reveal Confetti Cannon Set","طقم مدفع الكونفيتي للكشف عن الجنس","party",79,True,30,0,"all"),
]

def make_product(row):
    pid, name, name_ar, cat, price, returnable, ret_days, warranty, age = row
    return {
        "product_id": pid,
        "name": name,
        "name_ar": name_ar,
        "category": cat,
        "price_aed": float(price),
        "in_stock": random.random() > 0.08,  # 8% chance out-of-stock
        "age_range": age,
        "returnable": returnable,
        "return_window_days": ret_days,
        "warranty_months": warranty,
    }

products = {r[0]: make_product(r) for r in RAW_PRODUCTS}

# ── 2. ORDERS ─────────────────────────────────────────────────────────────────

GCC_CUSTOMERS = [
    # UAE
    ("Sara Al Mansouri","sara.m"),("Fatima Al Zaabi","fatima.z"),("Nora Hassan","nora.h"),
    ("Layla Qasim","layla.q"),("Hana Al Khatri","hana.k"),("Maryam Saleh","maryam.s"),
    ("Aisha Mohammed","aisha.m"),("Reem Al Falasi","reem.f"),("Dana Al Suwaidi","dana.s"),
    ("Shaikha Al Muhairi","shaikha.m"),("Manal Al Khaja","manal.k"),("Hessa Al Blooshi","hessa.b"),
    ("Alia Al Marri","alia.m"),("Salama Al Neyadi","salama.n"),("Wadha Al Ketbi","wadha.k"),
    ("Khulood Al Dhaheri","khulood.d"),("Mouza Al Hameli","mouza.h"),("Hind Al Mazrouei","hind.m"),
    ("Afra Al Shamsi","afra.s"),("Meera Al Ketbi","meera.k"),("Noura Al Mansoori","noura.ma"),
    ("Lujain Al Rashidi","lujain.r"),("Shamsa Al Nuaimi","shamsa.n"),("Ohood Al Shamsi","ohood.s"),
    ("Latifa Al Kaabi","latifa.k"),
    # Expat (UAE/GCC)
    ("Sarah Johnson","sarah.j"),("Emma Williams","emma.w"),("Priya Sharma","priya.s"),
    ("Jennifer Lee","jennifer.l"),("Maria Santos","maria.s"),("Ananya Patel","ananya.p"),
    # KSA
    ("Noura Al Rashidi","noura.r"),("Lara Al Otaibi","lara.o"),("Rana Al Qahtani","rana.q"),
    ("Huda Al Ghamdi","huda.g"),("Abeer Al Dossari","abeer.d"),("Dima Al Harbi","dima.h"),
    ("Hana Al Zahrani","hana.z"),("Rawan Al Malki","rawan.m"),("Sama Al Shehri","sama.sh"),
    # Kuwait
    ("Dalal Al Mutairi","dalal.m"),("Noor Al Sabah","noor.s"),("Ghada Al Rashidi","ghada.r"),
    ("Farah Al Enezi","farah.e"),
    # Qatar
    ("Mariam Al Thani","mariam.t"),("Hamda Al Kuwari","hamda.k"),("Shaikha Al Misnad","shaikha.ms"),
    # Bahrain
    ("Fatima Al Khalifa","fatima.k"),("Zainab Al Baharna","zainab.b"),
    # Oman
    ("Asma Al Busaidi","asma.b"),("Samira Al Wahaibi","samira.w"),
]

ADDRESSES = {
    "UAE":    ["Dubai, UAE","Abu Dhabi, UAE","Sharjah, UAE","Ajman, UAE","Ras Al Khaimah, UAE","Al Ain, UAE","Fujairah, UAE"],
    "KSA":    ["Riyadh, KSA","Jeddah, KSA","Dammam, KSA","Mecca, KSA","Khobar, KSA"],
    "Kuwait": ["Kuwait City, Kuwait","Hawalli, Kuwait","Salmiya, Kuwait"],
    "Qatar":  ["Doha, Qatar","Al Wakra, Qatar","Lusail, Qatar"],
    "Bahrain":["Manama, Bahrain","Riffa, Bahrain"],
    "Oman":   ["Muscat, Oman","Salalah, Oman"],
}
COUNTRIES = list(ADDRESSES.keys())
COUNTRY_WEIGHTS = [0.45, 0.25, 0.12, 0.08, 0.05, 0.05]

COURIERS = {
    "UAE":    [("Aramex","ARA"),("DHL Express","DHL"),("Emirates Post","EMP"),("Fetchr","FTR")],
    "KSA":    [("SMSA Express","SMS"),("Naqel Express","NQL"),("Aramex","ARA"),("DHL Express","DHL")],
    "Kuwait": [("Aramex","ARA"),("DHL Express","DHL")],
    "Qatar":  [("Qatar Post","QAT"),("Aramex","ARA")],
    "Bahrain":[("Bahrain Post","BHP"),("Aramex","ARA")],
    "Oman":   [("Oman Post","OMN"),("Aramex","ARA")],
}

PAYMENTS = ["credit_card","credit_card","credit_card","cash_on_delivery","tabby_installments","tamara_installments","apple_pay","google_pay"]
STATUSES_WEIGHTS = [
    ("delivered",       0.52),
    ("in_transit",      0.18),
    ("processing",      0.10),
    ("out_for_delivery",0.08),
    ("cancelled",       0.06),
    ("returned",        0.06),
]

# date helpers
from datetime import date, timedelta

def rand_date(days_ago_max, days_ago_min=0):
    base = date(2026, 4, 28)
    delta = random.randint(days_ago_min, days_ago_max)
    return (base - timedelta(days=delta)).isoformat()

def tracking_num(courier_code, country):
    return f"{courier_code}-{random.randint(100000,999999)}-{country[:3].upper()}"

# product pool keyed by category
product_pool = list(products.keys())

def rand_items(n=None):
    count = n or random.choices([1,2,3,4],[0.40,0.35,0.18,0.07])[0]
    chosen = random.sample(product_pool, min(count, len(product_pool)))
    items = []
    for pid in chosen:
        p = products[pid]
        qty = random.choices([1,2,3],[0.75,0.20,0.05])[0]
        items.append({"product_id": pid, "name": p["name"], "qty": qty, "price_aed": p["price_aed"]})
    return items

def make_order(order_num):
    oid = f"MW-{order_num:05d}"
    name, email_prefix = random.choice(GCC_CUSTOMERS)
    country = random.choices(COUNTRIES, COUNTRY_WEIGHTS)[0]
    address = random.choice(ADDRESSES[country])
    payment = random.choice(PAYMENTS)
    status_str, _ = random.choices(
        [s for s,_ in STATUSES_WEIGHTS],
        [w for _,w in STATUSES_WEIGHTS]
    )[0], None
    status_str = random.choices(
        [s for s,_ in STATUSES_WEIGHTS],
        [w for _,w in STATUSES_WEIGHTS]
    )[0]

    items = rand_items()
    total = round(sum(i["price_aed"] * i["qty"] for i in items), 2)
    courier_name, courier_code = random.choice(COURIERS[country])

    order = {
        "order_id": oid,
        "customer_name": name,
        "email": f"{email_prefix}@example.com",
        "status": status_str,
        "items": items,
        "total_aed": total,
        "payment_method": payment,
        "address": address,
    }

    if status_str == "delivered":
        del_date = rand_date(90, 1)
        order["delivery_date"] = del_date
        # compute returnable_until
        ret_days = min(products[i["product_id"]]["return_window_days"] for i in items)
        if ret_days > 0:
            d = date.fromisoformat(del_date)
            ret_until = (d + timedelta(days=ret_days)).isoformat()
            order["returnable_until"] = ret_until
            if date.fromisoformat(ret_until) < date(2026, 4, 28):
                order["return_window_expired"] = True
        # occasionally flag a note
        if random.random() < 0.05:
            order["notes"] = random.choice([
                "Customer reported item damaged on delivery",
                "Customer says item does not match description",
                "Possible safety concern flagged",
                "Wheel squeak reported — may be warranty issue",
            ])

    elif status_str == "in_transit":
        eta_days = random.randint(1, 5)
        order["estimated_delivery"] = (date(2026, 4, 28) + timedelta(days=eta_days)).isoformat()
        order["tracking_number"] = tracking_num(courier_code, country)
        order["courier"] = courier_name

    elif status_str == "out_for_delivery":
        order["estimated_delivery"] = date(2026, 4, 28).isoformat()
        order["tracking_number"] = tracking_num(courier_code, country)
        order["courier"] = courier_name

    elif status_str == "processing":
        pass  # no extra fields

    elif status_str == "cancelled":
        order["cancelled_date"] = rand_date(30, 0)
        # 60% refund processed, 40% pending
        order["refund_status"] = random.choice(["refund_processed","refund_processed","pending"])
        if order["refund_status"] == "refund_processed":
            order["refund_date"] = (date.fromisoformat(order["cancelled_date"]) + timedelta(days=random.randint(1,5))).isoformat()

    elif status_str == "returned":
        ret_init = rand_date(45, 5)
        order["return_initiated"] = ret_init
        order["refund_status"] = random.choice(["refund_processed","refund_processed","pending"])
        if order["refund_status"] == "refund_processed":
            order["refund_date"] = (date.fromisoformat(ret_init) + timedelta(days=random.randint(3,10))).isoformat()

    return oid, order

# Generate 150 orders spread across a realistic ID range
# Keep the original 20 hand-crafted orders as-is (MW-10021 → MW-10304)
# New orders start at MW-11000
orders = {}

# Add the 20 pre-existing orders first
EXISTING_PATH = Path(__file__).parent.parent / "data" / "orders.json"
existing = json.loads(EXISTING_PATH.read_text(encoding="utf-8"))
orders.update(existing)

# Generate 130 more
used_ids = set(int(k.split("-")[1]) for k in orders)
new_count = 0
candidate = 11000
while new_count < 130:
    if candidate not in used_ids:
        oid, order = make_order(candidate)
        orders[oid] = order
        used_ids.add(candidate)
        new_count += 1
    candidate += random.randint(1, 8)

print(f"Total orders: {len(orders)}")
print(f"Total products: {len(products)}")

# Write
out_dir = Path(__file__).parent.parent / "data"
out_dir.mkdir(exist_ok=True)
(out_dir / "orders.json").write_text(json.dumps(orders, indent=2, ensure_ascii=False), encoding="utf-8")
(out_dir / "products.json").write_text(json.dumps(products, indent=2, ensure_ascii=False), encoding="utf-8")
print("Written: data/orders.json, data/products.json")

# Quick sanity checks
statuses = {}
for o in orders.values():
    s = o["status"]
    statuses[s] = statuses.get(s, 0) + 1
print("Status breakdown:", statuses)
countries = {}
for o in orders.values():
    c = o["address"].split(", ")[-1]
    countries[c] = countries.get(c, 0) + 1
print("Country breakdown:", countries)
