import os


def upload_abstract_document(instance, filename):
    """
    Custom upload path for abstract documents.
    Files are saved in the 'abstract_documents' folder with the abstract's unique ID.
    """
    # Generate a unique path using the abstract's ID
    document_id = instance.abstract_id
    extension = filename.split('.')[-1]  # Preserve file extension
    return os.path.join('abstract_documents', str(document_id) + '.' + extension)


def upload_payment_receipt(instance, filename):
    document_id = instance.payment_id
    extension = filename.split('.')[-1] 
    return os.path.join('payment_slip', str(document_id) + '.' + extension)

def upload_schedule_document(instance, filename):
    document_id = instance.document_id
    extension = filename.split('.')[-1]
    return os.path.join('schedule_document', str(document_id) + '.' + extension)

def upload_certificate_template(instance, filename):
    document_id = instance.conference_id
    extension = filename.split('.')[-1]
    return os.path.join('certificate_template', str(document_id) + '.' + extension)

def upload_certificate_zip(instance, filename):
    return os.path.join('certificates', f"{instance.conference.conference_id}.zip")