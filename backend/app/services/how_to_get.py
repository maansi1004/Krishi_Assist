"""Plain guidance on how to get each kind of document, shown when a farmer says
"I don't have it yet". Written in three languages.

These are general steps, because offices and portals differ by state. The screen adds a reminder
to confirm with the official office. Only well-known official websites are linked.
"""
from __future__ import annotations

LINKS = {
    "uidai": {"label": "UIDAI (Aadhaar)", "url": "https://uidai.gov.in/"},
    "digilocker": {"label": "DigiLocker", "url": "https://www.digilocker.gov.in/"},
    "udid": {"label": "UDID / Swavlamban card", "url": "https://www.swavlambancard.gov.in/"},
    "soil": {"label": "Soil Health Card portal", "url": "https://soilhealth.dac.gov.in/"},
}

GUIDE = {
    "aadhaar": {
        "title": {"en": "Aadhaar", "hi": "आधार", "hinglish": "Aadhaar"},
        "steps": {
            "en": ["Visit the nearest Aadhaar enrolment or update centre and carry proof of identity and address. Centres are listed on the UIDAI website.",
                   "If you already have an Aadhaar number, download your e-Aadhaar from the UIDAI website or DigiLocker, or get a printout at a Common Service Centre (CSC).",
                   "Upload a clear copy here and keep the original safe."],
            "hi": ["नज़दीकी आधार नामांकन या अपडेट केंद्र जाएं और पहचान व पते का प्रमाण साथ ले जाएं। केंद्रों की सूची UIDAI की वेबसाइट पर है।",
                   "अगर आधार नंबर पहले से है, तो UIDAI की वेबसाइट या DigiLocker से ई-आधार डाउनलोड करें, या कॉमन सर्विस सेंटर (CSC) से प्रिंट निकलवाएं।",
                   "यहां उसकी साफ़ कॉपी अपलोड करें और असली कागज़ संभालकर रखें।"],
            "hinglish": ["Nazdiki Aadhaar enrolment ya update centre par jayein aur pehchaan va pate ka praman saath le jayein. Centres UIDAI website par listed hain.",
                         "Agar Aadhaar number pehle se hai, to UIDAI website ya DigiLocker se e-Aadhaar download karein, ya Common Service Centre (CSC) se print nikalwayein.",
                         "Yahan uski saaf copy upload karein aur original kagaz sambhal kar rakhein."],
        },
        "links": ["uidai", "digilocker"],
    },
    "identity_proof": {
        "title": {"en": "Photo ID", "hi": "फोटो पहचान पत्र", "hinglish": "Photo ID"},
        "steps": {
            "en": ["Most schemes accept one government photo ID, such as a voter ID, driving licence or passport. Aadhaar also counts.",
                   "If you have none of these, Aadhaar is usually the easiest to get (see the Aadhaar steps).",
                   "Check the scheme's official page for the exact list of IDs it accepts."],
            "hi": ["ज़्यादातर योजनाएं एक सरकारी फोटो पहचान पत्र मान लेती हैं, जैसे वोटर आईडी, ड्राइविंग लाइसेंस या पासपोर्ट। आधार भी चलता है।",
                   "अगर इनमें से कुछ नहीं है, तो आधार बनवाना आमतौर पर सबसे आसान है (आधार के चरण देखें)।",
                   "योजना के आधिकारिक पेज पर देखें कि कौन-कौन से पहचान पत्र मान्य हैं।"],
            "hinglish": ["Zyadatar schemes ek sarkari photo ID maan leti hain, jaise voter ID, driving licence ya passport. Aadhaar bhi chalta hai.",
                         "Agar inmein se kuch nahi hai, to Aadhaar banwana aamtaur par sabse aasaan hai (Aadhaar ke steps dekhein).",
                         "Scheme ke official page par dekhein ki kaun-kaun se ID valid hain."],
        },
        "links": ["digilocker"],
    },
    "land_record": {
        "title": {"en": "Land record or lease", "hi": "ज़मीन का रिकॉर्ड या पट्टा", "hinglish": "Zameen record ya lease"},
        "steps": {
            "en": ["Ask your village revenue officer (patwari, lekhpal, talati or VAO) or the tehsil office for a copy of your land record, for example khasra/khatauni, 7/12 or jamabandi.",
                   "Many states also publish land records on their own land-records website. Search for your state's land records site, or ask at a Common Service Centre (CSC).",
                   "If you farm on leased or shared land, get a written lease or the owner's signed, dated consent and keep a copy."],
            "hi": ["अपने गांव के राजस्व अधिकारी (पटवारी, लेखपाल, तलाठी या वीएओ) या तहसील कार्यालय से अपने ज़मीन के रिकॉर्ड की कॉपी मांगें, जैसे खसरा/खतौनी, 7/12 या जमाबंदी।",
                   "कई राज्य ज़मीन के रिकॉर्ड अपनी वेबसाइट पर भी देते हैं। अपने राज्य की भू-अभिलेख वेबसाइट खोजें, या कॉमन सर्विस सेंटर (CSC) में पूछें।",
                   "अगर आप पट्टे या साझे की ज़मीन पर खेती करते हैं, तो लिखित पट्टा या मालिक की हस्ताक्षर व तारीख वाली सहमति लें और कॉपी रखें।"],
            "hinglish": ["Apne gaon ke revenue officer (patwari, lekhpal, talati ya VAO) ya tehsil office se apne zameen record ki copy maangein, jaise khasra/khatauni, 7/12 ya jamabandi.",
                         "Kai rajya zameen ke records apni website par bhi dete hain. Apne rajya ki land-records website khojein, ya Common Service Centre (CSC) mein poochhein.",
                         "Agar aap lease ya saajhe ki zameen par kheti karte hain, to likhit lease ya malik ki signed aur dated sehmati lein aur copy rakhein."],
        },
        "links": [],
    },
    "bank_passbook": {
        "title": {"en": "Bank passbook or details", "hi": "बैंक पासबुक या विवरण", "hinglish": "Bank passbook ya details"},
        "steps": {
            "en": ["If you have no account, open a savings account in your own name at the nearest bank branch or post office. Most banks offer a zero-balance (Jan Dhan) account.",
                   "Carry your Aadhaar and a photograph. Ask for a passbook or a printed statement that shows the account number and IFSC code.",
                   "If the scheme pays money directly, check that the account is active and linked to your Aadhaar."],
            "hi": ["अगर खाता नहीं है, तो नज़दीकी बैंक शाखा या डाकघर में अपने नाम से बचत खाता खुलवाएं। ज़्यादातर बैंक ज़ीरो-बैलेंस (जन धन) खाता देते हैं।",
                   "आधार और एक फोटो साथ ले जाएं। पासबुक या प्रिंटेड स्टेटमेंट मांगें जिस पर खाता नंबर और IFSC कोड हो।",
                   "अगर योजना का पैसा सीधे खाते में आता है, तो देखें कि खाता चालू है और आधार से जुड़ा है।"],
            "hinglish": ["Agar account nahi hai, to nazdiki bank branch ya post office mein apne naam se savings account khulwayein. Zyadatar banks zero-balance (Jan Dhan) account dete hain.",
                         "Aadhaar aur ek photo saath le jayein. Passbook ya printed statement maangein jis par account number aur IFSC code ho.",
                         "Agar scheme ka paisa seedhe account mein aata hai, to dekhein ki account active hai aur Aadhaar se juda hai."],
        },
        "links": [],
    },
    "photo": {
        "title": {"en": "Passport photograph", "hi": "पासपोर्ट फोटो", "hinglish": "Passport photo"},
        "steps": {
            "en": ["Get a recent passport-size colour photograph from any photo studio.",
                   "Take a clear scan or phone photo of it on a plain background, or ask a Common Service Centre (CSC) to scan it."],
            "hi": ["किसी भी फोटो स्टूडियो से हाल की पासपोर्ट साइज़ रंगीन फोटो बनवाएं।",
                   "उसका साफ़ स्कैन या सादी पृष्ठभूमि पर मोबाइल से फोटो लें, या कॉमन सर्विस सेंटर (CSC) से स्कैन करवाएं।"],
            "hinglish": ["Kisi bhi photo studio se haal ki passport size colour photo banwayein.",
                         "Uska saaf scan ya saadi background par mobile se photo lein, ya Common Service Centre (CSC) se scan karwayein."],
        },
        "links": [],
    },
    "ration_card": {
        "title": {"en": "Ration card", "hi": "राशन कार्ड", "hinglish": "Ration card"},
        "steps": {
            "en": ["Apply through your state's food and civil supplies department or at the nearest Common Service Centre (CSC).",
                   "Carry proof of identity, address and the family details your state asks for.",
                   "If you already have a ration card, upload a clear copy of the page with the family details."],
            "hi": ["अपने राज्य के खाद्य एवं नागरिक आपूर्ति विभाग या नज़दीकी कॉमन सर्विस सेंटर (CSC) के ज़रिए आवेदन करें।",
                   "पहचान, पते का प्रमाण और राज्य द्वारा मांगे गए परिवार के विवरण साथ रखें।",
                   "अगर राशन कार्ड पहले से है, तो परिवार के विवरण वाले पन्ने की साफ़ कॉपी अपलोड करें।"],
            "hinglish": ["Apne rajya ke food and civil supplies vibhag ya nazdiki Common Service Centre (CSC) se apply karein.",
                         "Pehchaan, pate ka praman aur rajya dwara maange gaye parivar ke details saath rakhein.",
                         "Agar ration card pehle se hai, to parivar ke details wale page ki saaf copy upload karein."],
        },
        "links": [],
    },
    "caste_certificate": {
        "title": {"en": "Caste certificate", "hi": "जाति प्रमाण पत्र", "hinglish": "Jati praman patra"},
        "steps": {
            "en": ["Apply at your tehsil or SDM office, on your state's e-District or Seva Kendra portal, or at a Common Service Centre (CSC).",
                   "Carry your Aadhaar, address proof and, if you have one, an older caste certificate of a family member.",
                   "Processing time differs by state, so apply early."],
            "hi": ["अपने तहसील या एसडीएम कार्यालय, राज्य के ई-डिस्ट्रिक्ट या सेवा केंद्र पोर्टल, या कॉमन सर्विस सेंटर (CSC) पर आवेदन करें।",
                   "आधार, पते का प्रमाण और अगर हो तो परिवार के किसी सदस्य का पुराना जाति प्रमाण पत्र साथ रखें।",
                   "समय हर राज्य में अलग लगता है, इसलिए जल्दी आवेदन करें।"],
            "hinglish": ["Apne tehsil ya SDM office, rajya ke e-District ya Seva Kendra portal, ya Common Service Centre (CSC) par apply karein.",
                         "Aadhaar, pate ka praman aur agar ho to parivar ke kisi sadasya ka purana jati praman patra saath rakhein.",
                         "Samay har rajya mein alag lagta hai, isliye jaldi apply karein."],
        },
        "links": [],
    },
    "disability_certificate": {
        "title": {"en": "Disability certificate", "hi": "दिव्यांगता प्रमाण पत्र", "hinglish": "Divyangta praman patra"},
        "steps": {
            "en": ["Apply for the disability certificate and UDID card on the Swavlamban (UDID) website, or at your district hospital or Chief Medical Officer's office.",
                   "A medical examination by a government medical board is usually needed.",
                   "Keep a copy of the certificate and upload it here."],
            "hi": ["दिव्यांगता प्रमाण पत्र और UDID कार्ड के लिए स्वावलंबन (UDID) वेबसाइट पर, या अपने ज़िला अस्पताल या मुख्य चिकित्सा अधिकारी कार्यालय में आवेदन करें।",
                   "आमतौर पर सरकारी मेडिकल बोर्ड से जांच ज़रूरी होती है।",
                   "प्रमाण पत्र की कॉपी रखें और यहां अपलोड करें।"],
            "hinglish": ["Divyangta praman patra aur UDID card ke liye Swavlamban (UDID) website par, ya apne zila aspatal ya Chief Medical Officer office mein apply karein.",
                         "Aamtaur par sarkari medical board se jaanch zaroori hoti hai.",
                         "Certificate ki copy rakhein aur yahan upload karein."],
        },
        "links": ["udid"],
    },
    "soil_health_card": {
        "title": {"en": "Soil Health Card", "hi": "मृदा स्वास्थ्य कार्ड", "hinglish": "Soil Health Card"},
        "steps": {
            "en": ["Ask your block or district agriculture office about the Soil Health Card scheme and when soil samples are collected.",
                   "You can also check the Soil Health Card portal to see whether a card has already been issued for your land.",
                   "A card is usually issued after your soil sample has been tested."],
            "hi": ["अपने ब्लॉक या ज़िला कृषि कार्यालय से मृदा स्वास्थ्य कार्ड योजना और मिट्टी के नमूने कब लिए जाते हैं, यह पूछें।",
                   "मृदा स्वास्थ्य कार्ड पोर्टल पर भी देख सकते हैं कि आपकी ज़मीन का कार्ड बन चुका है या नहीं।",
                   "कार्ड आमतौर पर मिट्टी के नमूने की जांच होने के बाद मिलता है।"],
            "hinglish": ["Apne block ya zila krishi office se Soil Health Card scheme aur mitti ke sample kab liye jaate hain, ye poochhein.",
                         "Soil Health Card portal par bhi dekh sakte hain ki aapki zameen ka card ban chuka hai ya nahi.",
                         "Card aamtaur par mitti ke sample ki jaanch ke baad milta hai."],
        },
        "links": ["soil"],
    },
    "age_proof": {
        "title": {"en": "Age proof", "hi": "आयु प्रमाण", "hinglish": "Aayu praman"},
        "steps": {
            "en": ["Any one of these usually works: birth certificate, school leaving certificate or Aadhaar. Check which one the scheme accepts.",
                   "For a birth certificate, apply to the local registrar of births (municipality or gram panchayat)."],
            "hi": ["इनमें से कोई एक आमतौर पर चलता है: जन्म प्रमाण पत्र, स्कूल छोड़ने का प्रमाण पत्र या आधार। देखें कि योजना कौन सा मानती है।",
                   "जन्म प्रमाण पत्र के लिए स्थानीय जन्म-पंजीयक (नगरपालिका या ग्राम पंचायत) के पास आवेदन करें।"],
            "hinglish": ["Inmein se koi ek aamtaur par chalta hai: janm praman patra, school leaving certificate ya Aadhaar. Dekhein scheme kaun sa maanti hai.",
                         "Janm praman patra ke liye local registrar (nagarpalika ya gram panchayat) ke paas apply karein."],
        },
        "links": [],
    },
    "residence_proof": {
        "title": {"en": "Residence or domicile proof", "hi": "निवास प्रमाण", "hinglish": "Niwas praman"},
        "steps": {
            "en": ["Apply for a residence or domicile certificate at the tehsil office, on your state's e-District portal, or at a Common Service Centre (CSC).",
                   "Some schemes also accept an electricity bill, ration card or Aadhaar as address proof. Check what the scheme accepts."],
            "hi": ["निवास या मूल निवास प्रमाण पत्र के लिए तहसील कार्यालय, राज्य के ई-डिस्ट्रिक्ट पोर्टल या कॉमन सर्विस सेंटर (CSC) पर आवेदन करें।",
                   "कुछ योजनाएं बिजली बिल, राशन कार्ड या आधार को भी पते का प्रमाण मान लेती हैं। देखें कि योजना क्या मानती है।"],
            "hinglish": ["Niwas ya domicile certificate ke liye tehsil office, rajya ke e-District portal ya Common Service Centre (CSC) par apply karein.",
                         "Kuch schemes bijli bill, ration card ya Aadhaar ko bhi pate ka praman maan leti hain. Dekhein scheme kya maanti hai."],
        },
        "links": [],
    },
    "project_documents": {
        "title": {"en": "Project, estimate or invoice", "hi": "परियोजना, अनुमान या बिल", "hinglish": "Project, estimate ya bill"},
        "steps": {
            "en": ["These are usually prepared with the equipment dealer or supplier, or with a technical consultant: for example a quotation, invoice or project report.",
                   "Ask the dealer for an official quotation on their letterhead. For bigger projects, ask the scheme office for the project report format.",
                   "Before you buy anything, check whether the scheme needs approval first."],
            "hi": ["ये आमतौर पर उपकरण के डीलर या सप्लायर, या किसी तकनीकी सलाहकार के साथ तैयार होते हैं: जैसे कोटेशन, बिल या परियोजना रिपोर्ट।",
                   "डीलर से उनके लेटरहेड पर आधिकारिक कोटेशन मांगें। बड़ी परियोजनाओं के लिए योजना कार्यालय से रिपोर्ट का प्रारूप पूछें।",
                   "कुछ भी खरीदने से पहले देखें कि योजना में पहले मंज़ूरी लेनी होती है या नहीं।"],
            "hinglish": ["Ye aamtaur par equipment dealer ya supplier, ya kisi technical consultant ke saath taiyaar hote hain: jaise quotation, bill ya project report.",
                         "Dealer se unke letterhead par official quotation maangein. Bade projects ke liye scheme office se report ka format poochhein.",
                         "Kuch bhi kharidne se pehle dekhein ki scheme mein pehle approval lena hota hai ya nahi."],
        },
        "links": [],
    },
    "other": {
        "title": {"en": "Scheme-specific document", "hi": "योजना से जुड़ा दस्तावेज़", "hinglish": "Scheme se juda document"},
        "steps": {
            "en": ["This document is specific to the scheme. Read the official application guidelines for the exact format.",
                   "Ask the scheme's office or a Common Service Centre (CSC) for the template or help in preparing it."],
            "hi": ["यह दस्तावेज़ इसी योजना के लिए है। सही प्रारूप के लिए आधिकारिक आवेदन दिशानिर्देश पढ़ें।",
                   "योजना कार्यालय या कॉमन सर्विस सेंटर (CSC) से प्रारूप या तैयार करने में मदद मांगें।"],
            "hinglish": ["Ye document isi scheme ke liye hai. Sahi format ke liye official application guidelines padhein.",
                         "Scheme office ya Common Service Centre (CSC) se format ya taiyaar karne mein madad maangein."],
        },
        "links": [],
    },
}


def how_to_get(doc_type: str) -> dict:
    g = GUIDE.get(doc_type) or GUIDE["other"]
    return {"title": g["title"], "steps": g["steps"], "links": [LINKS[k] for k in g["links"]]}
