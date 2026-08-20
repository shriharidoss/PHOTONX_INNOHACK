class Vitals:
    def __init__(
        self,
        patient_id,
        temperature,
        heart_rate,
        spo2,
        systolic_bp,
        diastolic_bp
    ):
        self.patient_id = patient_id
        self.temperature = temperature
        self.heart_rate = heart_rate
        self.spo2 = spo2
        self.systolic_bp = systolic_bp
        self.diastolic_bp = diastolic_bp

    def to_dict(self):
        return {
            "patient_id": self.patient_id,
            "temperature": self.temperature,
            "heart_rate": self.heart_rate,
            "spo2": self.spo2,
            "systolic_bp": self.systolic_bp,
            "diastolic_bp": self.diastolic_bp
        }