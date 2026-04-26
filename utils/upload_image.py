import os


def upload_image_to(instance, filename):
    image_id = instance.image_id 
    extension = filename.split('.')[-1]
    
    return os.path.join('name', str(image_id) + '.' + extension)


def upload_speakers_to(instance, filename):
    speaker_id = instance.speaker_id 
    extension = filename.split('.')[-1]
    
    return os.path.join('speakers', str(speaker_id) + '.' + extension)

def upload_sponsor_logo_to(instance, filename):
    sponsor_id = instance.sponsor_id
    extension = filename.split('.')[-1]
    
    return os.path.join('sponsor_logo', str(sponsor_id) + '.' + extension)

def upload_slider_to(instance, filename):
    id = instance.id
    extension = filename.split('.')[-1]
    
    return os.path.join('sliders', str(id) + '.' + extension)