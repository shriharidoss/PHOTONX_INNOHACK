import mysql.connector


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():

    connection = mysql.connector.connect(

        host="localhost",

        user="root",

        password="hari2008",

        database="innohack_kiosk"

    )

    return connection


# ============================================================
# PATIENT FUNCTIONS
# ============================================================

def save_patient(
    name,
    age,
    gender,
    phone
):

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO patients
        (
            name,
            age,
            gender,
            phone
        )
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            name,
            age,
            gender,
            phone
        )
    )

    connection.commit()

    patient_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return patient_id


def get_patient(
    patient_id
):

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    query = """
        SELECT *
        FROM patients
        WHERE patient_id = %s
    """

    cursor.execute(
        query,
        (patient_id,)
    )

    patient = cursor.fetchone()

    cursor.close()
    connection.close()

    return patient


def get_all_patients():

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    query = """
        SELECT
            patient_id,
            name,
            age,
            gender,
            phone,
            created_at
        FROM patients
        ORDER BY patient_id ASC
    """

    cursor.execute(query)

    patients = cursor.fetchall()

    cursor.close()
    connection.close()

    return patients


def get_patient_by_phone(
    phone
):

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    query = """
        SELECT *
        FROM patients
        WHERE phone = %s
        LIMIT 1
    """

    cursor.execute(
        query,
        (phone,)
    )

    patient = cursor.fetchone()

    cursor.close()
    connection.close()

    return patient


# ============================================================
# HEALTH READING FUNCTIONS
# ============================================================

def save_health_reading(
    patient_id,
    temperature,
    spo2,
    heart_rate,
    systolic_bp,
    diastolic_bp
):

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO health_readings
        (
            patient_id,
            temperature,
            spo2,
            heart_rate,
            systolic_bp,
            diastolic_bp
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            patient_id,
            temperature,
            spo2,
            heart_rate,
            systolic_bp,
            diastolic_bp
        )
    )

    connection.commit()

    reading_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return reading_id


def get_health_readings(
    patient_id
):

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    query = """
        SELECT *
        FROM health_readings
        WHERE patient_id = %s
        ORDER BY reading_time DESC
    """

    cursor.execute(
        query,
        (patient_id,)
    )

    readings = cursor.fetchall()

    cursor.close()
    connection.close()

    return readings


# ============================================================
# DOCTOR FUNCTIONS
# ============================================================

def save_doctor(
    name,
    specialization,
    phone,
    email
):

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO doctors
        (
            name,
            specialization,
            phone,
            email
        )
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            name,
            specialization,
            phone,
            email
        )
    )

    connection.commit()

    doctor_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return doctor_id


# ============================================================
# CONSULTATION FUNCTIONS
# ============================================================

def save_consultation(
    patient_id,
    doctor_id,
    consultation_type,
    diagnosis
):

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO consultations
        (
            patient_id,
            doctor_id,
            consultation_type,
            diagnosis
        )
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            patient_id,
            doctor_id,
            consultation_type,
            diagnosis
        )
    )

    connection.commit()

    consultation_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return consultation_id


# ============================================================
# PRESCRIPTION FUNCTIONS
# ============================================================

def save_prescription(
    patient_id,
    doctor_id,
    medicine,
    dosage,
    frequency,
    duration,
    instructions
):

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO prescriptions
        (
            patient_id,
            doctor_id,
            medicine,
            dosage,
            frequency,
            duration,
            instructions
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            patient_id,
            doctor_id,
            medicine,
            dosage,
            frequency,
            duration,
            instructions
        )
    )

    connection.commit()

    prescription_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return prescription_id


def get_prescriptions(
    patient_id
):

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    query = """
        SELECT
            p.prescription_id,
            p.patient_id,
            p.doctor_id,
            p.medicine,
            p.dosage,
            p.frequency,
            p.duration,
            p.instructions,
            p.prescribed_at,
            d.name AS doctor_name
        FROM prescriptions p
        LEFT JOIN doctors d
            ON p.doctor_id = d.doctor_id
        WHERE p.patient_id = %s
        ORDER BY p.prescribed_at DESC
    """

    cursor.execute(
        query,
        (patient_id,)
    )

    prescriptions = cursor.fetchall()

    cursor.close()
    connection.close()

    return prescriptions


# ============================================================
# VIDEO CONSULTATION FUNCTIONS
# ============================================================

def create_video_request(
    patient_id,
    reason="General consultation"
):

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO video_consultation_requests
        (
            patient_id,
            reason,
            status
        )
        VALUES (%s, %s, 'pending')
    """

    cursor.execute(
        query,
        (
            patient_id,
            reason
        )
    )

    connection.commit()

    request_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return request_id


def accept_video_request(
    request_id,
    doctor_id,
    room_id
):

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        UPDATE video_consultation_requests
        SET
            doctor_id = %s,
            status = 'accepted',
            room_id = %s,
            accepted_at = CURRENT_TIMESTAMP
        WHERE request_id = %s
          AND status = 'pending'
    """

    cursor.execute(
        query,
        (
            doctor_id,
            room_id,
            request_id
        )
    )

    connection.commit()

    updated = cursor.rowcount

    cursor.close()
    connection.close()

    return updated


def reject_video_request(
    request_id
):

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        UPDATE video_consultation_requests
        SET status = 'rejected'
        WHERE request_id = %s
          AND status = 'pending'
    """

    cursor.execute(
        query,
        (request_id,)
    )

    connection.commit()

    updated = cursor.rowcount

    cursor.close()
    connection.close()

    return updated


def get_patient_video_requests(
    patient_id
):

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    query = """
        SELECT *
        FROM video_consultation_requests
        WHERE patient_id = %s
        ORDER BY created_at DESC
    """

    cursor.execute(
        query,
        (patient_id,)
    )

    requests = cursor.fetchall()

    cursor.close()
    connection.close()

    return requests