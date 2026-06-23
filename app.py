from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ORDS Configuration
ORDS_CONFIG = {
    'base_url': os.getenv('ORDS_BASE_URL', 'http://localhost:8080/ords/medexpert/'),
    'username': os.getenv('ORDS_USERNAME', 'system'),
    'password': os.getenv('ORDS_PASSWORD', 'magesh')
}

class ORDSDatabase:
    def __init__(self, config):
        self.config = config
        self.auth = (config['username'], config['password'])
        
    def _make_ords_request(self, endpoint, method='GET', data=None):
        """Make HTTP request to ORDS endpoint"""
        url = f"{self.config['base_url']}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, auth=self.auth, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, auth=self.auth, json=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"ORDS API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"ORDS Connection Error: {e}")
            return None
    
    def get_symptoms(self):
        """Get all symptoms from ORDS"""
        result = self._make_ords_request('symptoms/')
        if result and 'items' in result:
            return [item['symptom_name'] for item in result['items']]
        else:
            logger.info("Using fallback symptoms data")
            return self._get_fallback_symptoms()
    
    def get_medicine_recommendations(self, symptoms, patient_info):
        """Get medicine recommendations based on symptoms"""
        # Try ORDS first
        result = self._make_ords_request('medicine-recommendations/', 'POST', {
            'symptoms': symptoms,
            'patient_info': patient_info
        })
        
        if result and 'items' in result:
            recommendations = result['items']
        else:
            logger.info("Using fallback medicine recommendations")
            recommendations = self._get_fallback_recommendations(symptoms, patient_info)
        
        # Apply safety rules
        return self._apply_safety_rules(recommendations, patient_info)
    
    def save_consultation(self, patient_info, symptoms, recommendations):
        """Save consultation to ORDS"""
        consultation_data = {
            "patient_age": patient_info.get('age'),
            "patient_gender": patient_info.get('gender'),
            "symptoms": ', '.join(symptoms),
            "recommendations": str(recommendations),
            "consultation_date": datetime.now().isoformat(),
            "severity": patient_info.get('severity', 'mild')
        }
        
        result = self._make_ords_request('consultations/', 'POST', consultation_data)
        return result is not None
    
    def _get_fallback_symptoms(self):
        """Complete symptoms database"""
        return [
            # 🫁 Respiratory Symptoms
            'Cough', 'Runny nose', 'Sneezing', 'Nasal congestion', 'Sore throat', 'Hoarseness', 'Shortness of breath', 'Wheezing',
            
            # 🤢 Gastrointestinal Symptoms  
            'Nausea', 'Vomiting', 'Diarrhea', 'Constipation', 'Indigestion', 'Bloating / Gas', 'Abdominal pain', 'Persistent vomiting', 'Blood in vomit or stool', 'Severe abdominal pain',
            
            # 🧠 Neurological & Mental Symptoms
            'Headache', 'Dizziness', 'Insomnia', 'Anxiety', 'Seizures / Tremors', 'Memory loss / Confusion', 'Sudden severe headache',
            
            # 🧍‍♂️ Musculoskeletal Symptoms
            'Body aches', 'Joint pain', 'Back pain', 'Cramps', 'Stiff neck',
            
            # 🧴 Skin & External Symptoms
            'Rash / Itching', 'Dry skin', 'Blisters', 'Bruising', 'Hair loss', 'Yellowing of skin/eyes (jaundice)', 'Rapidly spreading rash or infection',
            
            # 💧 Urinary & Reproductive Symptoms
            'Painful urination', 'Frequent urination', 'Menstrual cramps', 'Vaginal discharge', 'Blood in urine', 'Painful urination with fever', 'Erectile dysfunction (persistent)',
            
            # 👁️ EENT Symptoms
            'Eye redness', 'Ear pain', 'Nosebleeds', 'Blurred or double vision', 'Eye pain with vision loss', 'Ringing in ears (persistent)',
            
            # 🌡️ General / Systemic
            'Fever', 'Chills', 'Fatigue', 'Loss of appetite', 'Unexplained weight loss', 'Swollen lymph nodes (persistent)', 'Recurring fever',
            
            # 🧪 Cardiovascular
            'Palpitations / Irregular heartbeat', 'Swelling in legs (persistent)', 'High/Low blood pressure (symptomatic)', 'Fainting episodes'
        ]
    
    def _get_fallback_recommendations(self, symptoms, patient_info):
        """Complete medicine database with all symptoms"""
        medicine_database = {
            # 🫁 Respiratory Symptoms
            'Cough': [
                {'medicine': 'Dextromethorphan syrup', 'type': 'OTC', 'uses': 'Suppresses dry cough', 
                 'dosage': '10-20mg every 4-6 hours', 'confidence_score': 85}
            ],
            'Runny nose': [
                {'medicine': 'Cetirizine', 'type': 'OTC', 'uses': 'Relieves allergy-related nasal drip', 
                 'dosage': '10mg once daily', 'confidence_score': 80},
                {'medicine': 'Loratadine', 'type': 'OTC', 'uses': 'Relieves allergy-related nasal drip', 
                 'dosage': '10mg once daily', 'confidence_score': 80}
            ],
            'Sneezing': [
                {'medicine': 'Loratadine', 'type': 'OTC', 'uses': 'Controls allergy-induced sneezing', 
                 'dosage': '10mg once daily', 'confidence_score': 85}
            ],
            'Nasal congestion': [
                {'medicine': 'Oxymetazoline spray', 'type': 'OTC', 'uses': 'Clears blocked nose', 
                 'dosage': '2-3 sprays per nostril every 12 hours (max 3 days)', 'confidence_score': 90}
            ],
            'Sore throat': [
                {'medicine': 'Throat lozenges', 'type': 'OTC', 'uses': 'Soothes throat irritation', 
                 'dosage': '1 lozenge every 2-4 hours', 'confidence_score': 75}
            ],
            'Hoarseness': [
                {'medicine': 'Honey with warm fluids', 'type': 'Home Remedy', 'uses': 'Eases vocal strain', 
                 'dosage': '1-2 teaspoons as needed', 'confidence_score': 70}
            ],
            
            # 🤢 Gastrointestinal Symptoms
            'Nausea': [
                {'medicine': 'Meclizine', 'type': 'OTC', 'uses': 'Reduces nausea and motion sickness', 
                 'dosage': '25-50mg as needed', 'confidence_score': 80},
                {'medicine': 'Ginger supplements', 'type': 'OTC', 'uses': 'Reduces nausea', 
                 'dosage': '250-500mg every 6 hours', 'confidence_score': 70}
            ],
            'Vomiting': [
                {'medicine': 'Oral Rehydration Solution (ORS)', 'type': 'OTC', 'uses': 'Rehydrates and replaces electrolytes', 
                 'dosage': 'As directed based on weight', 'confidence_score': 85}
            ],
            'Diarrhea': [
                {'medicine': 'Loperamide', 'type': 'OTC', 'uses': 'Slows bowel movement', 
                 'dosage': '4mg initially, then 2mg after each loose stool (max 16mg/day)', 'confidence_score': 80},
                {'medicine': 'Oral Rehydration Solution (ORS)', 'type': 'OTC', 'uses': 'Prevents dehydration', 
                 'dosage': 'As directed based on weight', 'confidence_score': 90}
            ],
            'Constipation': [
                {'medicine': 'Psyllium husk', 'type': 'OTC', 'uses': 'Softens stool and eases bowel movement', 
                 'dosage': '1 teaspoon in water 1-3 times daily', 'confidence_score': 75},
                {'medicine': 'Docusate sodium', 'type': 'OTC', 'uses': 'Stool softener', 
                 'dosage': '100-200mg daily', 'confidence_score': 70}
            ],
            'Indigestion': [
                {'medicine': 'Omeprazole', 'type': 'OTC', 'uses': 'Reduces stomach acid', 
                 'dosage': '20mg once daily before eating', 'confidence_score': 85},
                {'medicine': 'Calcium carbonate (Tums)', 'type': 'OTC', 'uses': 'Neutralizes stomach acid', 
                 'dosage': '2-4 tablets as needed', 'confidence_score': 80}
            ],
            'Bloating / Gas': [
                {'medicine': 'Simethicone', 'type': 'OTC', 'uses': 'Relieves gas and bloating', 
                 'dosage': '40-125mg after meals and at bedtime', 'confidence_score': 75}
            ],
            'Abdominal pain': [
                {'medicine': 'Paracetamol', 'type': 'OTC', 'uses': 'Eases mild abdominal pain', 
                 'dosage': '500-1000mg every 4-6 hours', 'confidence_score': 70}
            ],
            
            # 🧠 Neurological & Mental Symptoms
            'Headache': [
                {'medicine': 'Paracetamol', 'type': 'OTC', 'uses': 'Relieves mild to moderate headache', 
                 'dosage': '500-1000mg every 4-6 hours', 'confidence_score': 85},
                {'medicine': 'Ibuprofen', 'type': 'OTC', 'uses': 'Relieves headache with inflammation', 
                 'dosage': '200-400mg every 6-8 hours', 'confidence_score': 80}
            ],
            'Dizziness': [
                {'medicine': 'Meclizine', 'type': 'OTC', 'uses': 'Reduces vertigo and lightheadedness', 
                 'dosage': '25-50mg as needed', 'confidence_score': 75}
            ],
            'Insomnia': [
                {'medicine': 'Melatonin', 'type': 'OTC', 'uses': 'Promotes sleep onset', 
                 'dosage': '1-5mg 30 minutes before bedtime', 'confidence_score': 70},
                {'medicine': 'Chamomile tea', 'type': 'Home Remedy', 'uses': 'Mild sedative effect', 
                 'dosage': '1 cup before bedtime', 'confidence_score': 65}
            ],
            'Anxiety': [
                {'medicine': 'Valerian root', 'type': 'OTC', 'uses': 'Mild calming effect', 
                 'dosage': '300-600mg as needed', 'confidence_score': 60}
            ],
            
            # 🧍‍♂️ Musculoskeletal Symptoms
            'Body aches': [
                {'medicine': 'Ibuprofen', 'type': 'OTC', 'uses': 'Reduces muscle pain and fever', 
                 'dosage': '200-400mg every 6-8 hours', 'confidence_score': 85},
                {'medicine': 'Paracetamol', 'type': 'OTC', 'uses': 'Relieves muscle pain', 
                 'dosage': '500-1000mg every 4-6 hours', 'confidence_score': 80}
            ],
            'Joint pain': [
                {'medicine': 'Ibuprofen', 'type': 'OTC', 'uses': 'Relieves joint inflammation', 
                 'dosage': '200-400mg every 6-8 hours', 'confidence_score': 80},
                {'medicine': 'NSAID gel (Diclofenac)', 'type': 'OTC', 'uses': 'Topical pain relief', 
                 'dosage': 'Apply to affected area 3-4 times daily', 'confidence_score': 75}
            ],
            'Back pain': [
                {'medicine': 'Ibuprofen', 'type': 'OTC', 'uses': 'Reduces back pain and inflammation', 
                 'dosage': '200-400mg every 6-8 hours', 'confidence_score': 80}
            ],
            'Cramps': [
                {'medicine': 'Magnesium supplements', 'type': 'OTC', 'uses': 'Prevents muscle cramps', 
                 'dosage': '200-400mg daily', 'confidence_score': 70}
            ],
            'Stiff neck': [
                {'medicine': 'Ibuprofen', 'type': 'OTC', 'uses': 'Reduces inflammation and pain', 
                 'dosage': '200-400mg every 6-8 hours', 'confidence_score': 75}
            ],
            
            # 🧴 Skin & External Symptoms
            'Rash / Itching': [
                {'medicine': 'Calamine lotion', 'type': 'OTC', 'uses': 'Soothes skin irritation', 
                 'dosage': 'Apply to affected area 3-4 times daily', 'confidence_score': 80},
                {'medicine': 'Hydrocortisone cream', 'type': 'OTC', 'uses': 'Reduces itching and inflammation', 
                 'dosage': 'Apply thinly 1-2 times daily', 'confidence_score': 85}
            ],
            'Dry skin': [
                {'medicine': 'Moisturizing cream', 'type': 'OTC', 'uses': 'Hydrates and protects skin', 
                 'dosage': 'Apply as needed throughout day', 'confidence_score': 90}
            ],
            'Blisters': [
                {'medicine': 'Antibiotic ointment', 'type': 'OTC', 'uses': 'Prevents infection', 
                 'dosage': 'Apply to cleaned area 2-3 times daily', 'confidence_score': 85}
            ],
            'Bruising': [
                {'medicine': 'Arnica gel', 'type': 'OTC', 'uses': 'Reduces swelling and discoloration', 
                 'dosage': 'Apply to bruise 2-3 times daily', 'confidence_score': 70}
            ],
            'Hair loss': [
                {'medicine': 'Biotin supplements', 'type': 'OTC', 'uses': 'Supports hair health', 
                 'dosage': '2500-5000mcg daily', 'confidence_score': 65}
            ],
            
            # 💧 Urinary & Reproductive Symptoms
            'Painful urination': [
                {'medicine': 'Phenazopyridine', 'type': 'OTC', 'uses': 'Eases urinary discomfort', 
                 'dosage': '200mg 3 times daily after meals (max 2 days)', 'confidence_score': 80}
            ],
            'Menstrual cramps': [
                {'medicine': 'Ibuprofen', 'type': 'OTC', 'uses': 'Relieves period pain', 
                 'dosage': '200-400mg every 6-8 hours', 'confidence_score': 85}
            ],
            'Vaginal discharge': [
                {'medicine': 'Antifungal cream (Clotrimazole)', 'type': 'OTC', 'uses': 'Treats yeast infection', 
                 'dosage': 'Apply as directed for 3-7 days', 'confidence_score': 90}
            ],
            
            # 👁️ EENT Symptoms
            'Eye redness': [
                {'medicine': 'Antihistamine eye drops', 'type': 'OTC', 'uses': 'Reduces allergy-related redness', 
                 'dosage': '1-2 drops in affected eye(s) every 4-6 hours', 'confidence_score': 80}
            ],
            'Ear pain': [
                {'medicine': 'Paracetamol', 'type': 'OTC', 'uses': 'Eases ear discomfort', 
                 'dosage': '500-1000mg every 4-6 hours', 'confidence_score': 75}
            ],
            
            # 🌡️ General / Systemic
            'Fever': [
                {'medicine': 'Paracetamol', 'type': 'OTC', 'uses': 'Lowers body temperature', 
                 'dosage': '500-1000mg every 4-6 hours', 'confidence_score': 90},
                {'medicine': 'Ibuprofen', 'type': 'OTC', 'uses': 'Reduces fever and inflammation', 
                 'dosage': '200-400mg every 6-8 hours', 'confidence_score': 85}
            ],
            'Fatigue': [
                {'medicine': 'Rest and hydration', 'type': 'Lifestyle', 'uses': 'Boosts energy and recovery', 
                 'dosage': 'Adequate sleep and fluid intake', 'confidence_score': 95}
            ],
            'Loss of appetite': [
                {'medicine': 'Small frequent meals', 'type': 'Dietary', 'uses': 'Maintains nutrition', 
                 'dosage': 'Light, easily digestible foods', 'confidence_score': 85}
            ]
        }
        
        # Emergency symptoms that require doctor evaluation
        emergency_symptoms = [
            'Shortness of breath', 'Wheezing', 'Persistent vomiting', 'Blood in vomit or stool', 
            'Severe abdominal pain', 'Seizures / Tremors', 'Memory loss / Confusion', 
            'Sudden severe headache', 'Yellowing of skin/eyes (jaundice)', 
            'Rapidly spreading rash or infection', 'Blood in urine', 'Painful urination with fever',
            'Erectile dysfunction (persistent)', 'Blurred or double vision', 
            'Eye pain with vision loss', 'Ringing in ears (persistent)', 'Unexplained weight loss',
            'Swollen lymph nodes (persistent)', 'Recurring fever', 'Palpitations / Irregular heartbeat',
            'Swelling in legs (persistent)', 'High/Low blood pressure (symptomatic)', 'Fainting episodes'
        ]
        
        # Check if any emergency symptoms are present
        has_emergency = any(symptom in emergency_symptoms for symptom in symptoms)
        
        if has_emergency:
            return [{
                'medicine': 'CONSULT HEALTHCARE PROVIDER',
                'type': 'Medical Advice',
                'uses': 'Symptoms require professional medical evaluation',
                'dosage': 'Seek immediate medical attention',
                'confidence_score': 99,
                'warnings': ['Do not self-treat - these symptoms need doctor evaluation'],
                'advice': 'Contact healthcare provider or visit emergency room'
            }]
        
        # Normal recommendation logic
        recommendations = []
        used_medicines = set()
        
        for symptom in symptoms:
            if symptom in medicine_database:
                for medicine in medicine_database[symptom]:
                    if medicine['medicine'] not in used_medicines:
                        recommendations.append(medicine)
                        used_medicines.add(medicine['medicine'])
        
        return recommendations
    
    def _apply_safety_rules(self, recommendations, patient_info):
    
        safe_recommendations = []
    
        # Extract patient data
        age = patient_info.get('age')
        gender = patient_info.get('gender')
        pregnancy = patient_info.get('pregnancy', False)
        allergies = patient_info.get('allergies', False)
        chronic = patient_info.get('chronic', False)
        severity = patient_info.get('severity', 'mild')
    
        # Convert age to integer if possible
        try:
            age_int = int(age) if age else None
        except (ValueError, TypeError):
            age_int = None
    
        for rec in recommendations:
            # Create a copy to avoid modifying original
            safe_rec = rec.copy()
            warnings = []
            contraindications = []
            special_instructions = []
        
            medicine_name = safe_rec.get('medicine', '').lower()
            medicine_type = safe_rec.get('type', '').lower()
        
            # ==================== AGE-BASED SAFETY RULES ====================
            if age_int:
                # Pediatric restrictions
                if age_int < 2:
                    contraindications.append("NOT RECOMMENDED for children under 2 years")
                elif age_int < 6:
                    if medicine_name in ['dextromethorphan', 'loperamide', 'dimenhydrinate']:
                        warnings.append("Use under doctor supervision for children under 6")
                elif age_int < 12:
                    if medicine_name in ['ibuprofen', 'aspirin']:
                        warnings.append("Pediatric dosage required - consult doctor")

                # Elderly precautions
                if age_int > 65:
                    if medicine_name in ['ibuprofen', 'naproxen']:
                        warnings.append("Increased risk of kidney damage and stomach bleeding in elderly")
                    if medicine_name in ['meclizine', 'dimenhydrinate']:
                        warnings.append("May cause confusion or drowsiness in elderly patients")
        
            # ==================== PREGNANCY SAFETY RULES ====================
            if pregnancy:
                if medicine_name in ['ibuprofen', 'naproxen']:
                    contraindications.append("AVOID during pregnancy - may cause complications")
                elif medicine_name in ['aspirin']:
                    contraindications.append("CONTRAINDICATED in pregnancy")
                elif medicine_name in ['paracetamol']:
                    warnings.append("Use only under doctor supervision during pregnancy")
                elif 'antifungal' in medicine_name:
                    warnings.append("Consult doctor before use during pregnancy")
        
            # ==================== GENDER-SPECIFIC RULES ====================
            if gender == 'female' and not pregnancy:
                if medicine_name in ['ibuprofen', 'naproxen']:
                    warnings.append("May reduce effectiveness of oral contraceptives")
        
            # ==================== ALLERGY & SENSITIVITY RULES ====================
            if allergies:
                if 'sulfa' in medicine_name or 'sulfonamide' in medicine_name:
                    contraindications.append("CONTRAINDICATED in patients with sulfa allergy")
                if 'penicillin' in medicine_name:
                    contraindications.append("CONTRAINDICATED in patients with penicillin allergy")
                warnings.append("Check inactive ingredients for potential allergens")
        
            # ==================== CHRONIC CONDITION RULES ====================
            if chronic:
                # NSAID restrictions for various conditions
                if medicine_name in ['ibuprofen', 'naproxen', 'aspirin']:
                    contraindications.append("Use with caution in patients with:")
                    if 'kidney' in chronic.lower():
                        contraindications.append("  - Kidney disease (increased nephrotoxicity risk)")
                    if 'liver' in chronic.lower():
                        contraindications.append("  - Liver disease (metabolism impaired)")
                    if 'heart' in chronic.lower() or 'hypertension' in chronic.lower():
                        contraindications.append("  - Heart conditions (may increase blood pressure)")
                    if 'ulcer' in chronic.lower() or 'gerd' in chronic.lower():
                        contraindications.append("  - Stomach ulcers or GERD (increased bleeding risk)")
                    if 'asthma' in chronic.lower():
                        contraindications.append("  - Asthma (may trigger bronchospasm)")
            
                # Antihistamine precautions
                if any(word in medicine_name for word in ['cetirizine', 'loratadine', 'diphenhydramine']):
                    if 'glaucoma' in chronic.lower():
                        warnings.append("Use with caution in glaucoma")
                    if 'prostate' in chronic.lower():
                        warnings.append("May cause urinary retention in prostate conditions")
        
            # ==================== MEDICINE-SPECIFIC SAFETY RULES ====================
        
            # NSAIDs Safety
            if medicine_name in ['ibuprofen', 'naproxen']:
                warnings.append("Take with food or milk to minimize stomach upset")
                warnings.append("Avoid alcohol consumption while taking this medication")
                if severity == 'severe':
                    warnings.append("Severe pain may indicate serious condition - consult doctor")
        
            # Acetaminophen Safety
            if 'paracetamol' in medicine_name or 'acetaminophen' in medicine_name:
                warnings.append("Do not exceed 4000mg (4g) per day")
                warnings.append("Avoid concurrent use with other acetaminophen-containing products")
                if chronic and 'liver' in chronic.lower():
                    contraindications.append("CONTRAINDICATED in severe liver disease")
                warnings.append("Chronic alcohol users should not exceed 2000mg per day")
        
            # Antihistamine Safety
            if any(word in medicine_name for word in ['cetirizine', 'loratadine', 'diphenhydramine']):
                warnings.append("May cause drowsiness - avoid driving or operating machinery")
                if age_int and age_int > 65:
                    warnings.append("Increased risk of falls in elderly")
        
            # Decongestant Safety
            if 'pseudoephedrine' in medicine_name or 'phenylephrine' in medicine_name:
                if chronic and any(cond in chronic.lower() for cond in ['heart', 'hypertension', 'thyroid']):
                    contraindications.append("CONTRAINDICATED in heart conditions, hypertension, or thyroid disease")
                warnings.append("May cause insomnia or nervousness")
        
            # Antidiarrheal Safety
            if 'loperamide' in medicine_name:
                warnings.append("Do not use if fever present or if blood in stool")
                warnings.append("Discontinue if abdominal distention occurs")
                if age_int and age_int < 12:
                    contraindications.append("Not recommended for children under 12")
        
            # Cough Suppressant Safety
            if 'dextromethorphan' in medicine_name:
                if chronic and any(cond in chronic.lower() for cond in ['asthma', 'copd']):
                    warnings.append("Use with caution in asthma/COPD - may thicken secretions")
        
            # ==================== DURATION & MONITORING RULES ====================
        
            # Short-term use medications
            if any(word in medicine_name for word in ['oxymetazoline', 'phenazopyridine']):
                warnings.append("Do not use for more than 3 consecutive days")
                special_instructions.append("Rebound congestion may occur with prolonged use")
        
            # Topical medications
            if any(word in medicine_type for word in ['cream', 'ointment', 'topical']):
                special_instructions.append("Discontinue if irritation or rash develops")
                special_instructions.append("Do not apply to broken or infected skin")
        
            # ==================== DRUG INTERACTION WARNINGS ====================
            if chronic:
                if medicine_name in ['ibuprofen', 'naproxen']:
                    warnings.append("May interact with: blood pressure medications, blood thinners, steroids")
                if 'antihistamine' in medicine_type:
                    warnings.append("May enhance sedative effects of alcohol and other CNS depressants")
        
            # ==================== SEVERITY-BASED RECOMMENDATIONS ====================
            if severity == 'severe':
                safe_rec['advice'] = "Severe symptoms require immediate medical evaluation. Do not rely on self-treatment."
            elif len(symptoms) >= 3:
                safe_rec['advice'] = "Multiple symptoms suggest possible underlying condition. Consult healthcare provider for comprehensive evaluation."
            else:
                safe_rec['advice'] = "Consult a doctor if symptoms persist for more than 3 days or worsen"
        
            # ==================== FINAL SAFETY ASSESSMENT ====================
        
            # If contraindications exist, mark as unsafe
            if contraindications:
                safe_rec['safety_status'] = 'unsafe'
                safe_rec['confidence'] = max(safe_rec.get('confidence_score', 80) - 30, 20)
            elif warnings:
                safe_rec['safety_status'] = 'caution'
                safe_rec['confidence'] = max(safe_rec.get('confidence_score', 80) - 10, 50)
            else:
                safe_rec['safety_status'] = 'safe'
                safe_rec['confidence'] = safe_rec.get('confidence_score', 80)
        
            # Combine all warnings and contraindications
            all_warnings = []
            if contraindications:
                all_warnings.extend([f"🚫 {warning}" for warning in contraindications])
            if warnings:
                all_warnings.extend([f"⚠️ {warning}" for warning in warnings])
            if special_instructions:
                all_warnings.extend([f"💡 {instruction}" for instruction in special_instructions])
        
            safe_rec['warnings'] = all_warnings
        
            # Add monitoring recommendations
            monitoring_advice = []
            if medicine_name in ['ibuprofen', 'naproxen']:
                monitoring_advice.append("Monitor for stomach pain, black stools, or unusual bleeding")
            if 'paracetamol' in medicine_name:
                monitoring_advice.append("Watch for signs of liver problems: yellow skin, dark urine, abdominal pain")
        
            if monitoring_advice:
                safe_rec['monitoring'] = monitoring_advice
        
            safe_recommendations.append(safe_rec)
    
        return safe_recommendations
class MedicineExpertSystem:
    def __init__(self, database):
        self.db = database
        self.emergency_symptoms = [
            'Chest pain', 'Shortness of breath', 'Severe abdominal pain',
            'Sudden weakness', 'Difficulty speaking', 'Loss of consciousness'
        ]
    
    def analyze_symptoms(self, symptoms, patient_info):
        """Analyze symptoms and return recommendations"""
        
        # Check for emergency conditions
        emergency_warning = self._check_emergency_conditions(symptoms, patient_info)
        
        # Get medicine recommendations
        recommendations = self.db.get_medicine_recommendations(symptoms, patient_info)
        
        # Apply expert rules
        recommendations = self._apply_expert_rules(recommendations, symptoms, patient_info)
        
        # Save consultation
        self.db.save_consultation(patient_info, symptoms, recommendations)
        
        return {
            'emergency_warning': emergency_warning,
            'recommendations': recommendations
        }
    
    def _check_emergency_conditions(self, symptoms, patient_info):
        """Check for emergency symptoms"""
        emergency_symptoms = [
            'Shortness of breath', 'Wheezing', 'Persistent vomiting', 'Blood in vomit or stool', 
            'Severe abdominal pain', 'Seizures / Tremors', 'Memory loss / Confusion', 
            'Sudden severe headache', 'Yellowing of skin/eyes (jaundice)', 
            'Rapidly spreading rash or infection', 'Blood in urine', 'Painful urination with fever',
            'Erectile dysfunction (persistent)', 'Blurred or double vision', 
            'Eye pain with vision loss', 'Ringing in ears (persistent)', 'Unexplained weight loss',
            'Swollen lymph nodes (persistent)', 'Recurring fever', 'Palpitations / Irregular heartbeat',
            'Swelling in legs (persistent)', 'High/Low blood pressure (symptomatic)', 'Fainting episodes'
        ]
        
        severe_symptoms = [symptom for symptom in symptoms if symptom in emergency_symptoms]
        
        if severe_symptoms and patient_info.get('severity') == 'severe':
            return f"EMERGENCY: {', '.join(severe_symptoms)} detected. These require immediate medical evaluation."
        
        return None
    
    def _apply_expert_rules(self, recommendations, symptoms, patient_info):
        """Apply expert medical rules"""
        # Rule 1: Boost confidence for combination symptoms
        if 'Fever' in symptoms and 'Body aches' in symptoms:
            for rec in recommendations:
                if rec['medicine'] == 'Ibuprofen':
                    rec['confidence'] = min(rec.get('confidence', 80) + 5, 95)
        
        # Rule 2: Adjust for multiple symptoms
        if len(symptoms) >= 3:
            for rec in recommendations:
                rec['advice'] = "Multiple symptoms detected. Consider consulting a doctor for comprehensive evaluation."
        
        return recommendations
    
    def validate_patient_input(self, patient_info, symptoms):
        """Validate patient input"""
        errors = []
        
        # Age validation
        age = patient_info.get('age')
        if not age:
            errors.append("Age is required")
        else:
            try:
                age_int = int(age)
                if not (1 <= age_int <= 120):
                    errors.append("Age must be between 1 and 100")
            except ValueError:
                errors.append("Age must be a valid number")
        
        # Gender validation
        gender = patient_info.get('gender')
        if not gender or gender not in ['male', 'female', 'other']:
            errors.append("Valid gender selection is required")
        
        # Symptoms validation
        if not symptoms or len(symptoms) == 0:
            errors.append("At least one symptom must be selected")
        
        return errors

# Initialize services
ords_db = ORDSDatabase(ORDS_CONFIG)
expert_system = MedicineExpertSystem(ords_db)

@app.route('/')
def index():
    """Serve the main application"""
    return render_template('index.html')

@app.route('/api/symptoms', methods=['GET'])
def get_symptoms():
    """Get available symptoms"""
    try:
        symptoms = ords_db.get_symptoms()
        return jsonify({'symptoms': symptoms})
    except Exception as e:
        logger.error(f"Error in get_symptoms: {e}")
        return jsonify({'error': 'Failed to fetch symptoms'}), 500

@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    """Diagnose symptoms and return recommendations"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract patient information
        patient_info = {
            'age': data.get('age'),
            'gender': data.get('gender'),
            'pregnancy': data.get('pregnancy', False),
            'allergies': data.get('allergies', False),
            'chronic': data.get('chronic', False),
            'severity': data.get('severity', 'mild')
        }
        
        symptoms = data.get('symptoms', [])
        
        # Validate input
        validation_errors = expert_system.validate_patient_input(patient_info, symptoms)
        if validation_errors:
            return jsonify({'error': validation_errors[0]}), 400
        
        # Get diagnosis
        result = expert_system.analyze_symptoms(symptoms, patient_info)
        
        logger.info(f"Diagnosis completed for patient age {patient_info['age']} with {len(symptoms)} symptoms")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Diagnosis error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test ORDS connection
        symptoms = ords_db.get_symptoms()
        ords_status = len(symptoms) > 0
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'ords_connected': ords_status,
            'symptoms_available': len(symptoms)
        })
    except Exception as e:
        return jsonify({
            'status': 'degraded',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 Starting Medicine Expert System...")
    print("📊 Available endpoints:")
    print("   GET  /              - Main application")
    print("   GET  /api/symptoms  - Get available symptoms") 
    print("   POST /api/diagnose  - Get medicine recommendations")
    print("   GET  /api/health    - Health check")
    print("")
    print("🔧 Configuration:")
    print(f"   ORDS Base URL: {ORDS_CONFIG['base_url']}")
    print("   Server: http://localhost:5000")
    print("")
    print("⚠️  Remember: This is for educational purposes only!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)