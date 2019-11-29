"""
MongoEngine Models for the Zeye Cloud Platform
"""

from datetime import datetime, timedelta
from uuid import uuid4
import mongoengine as mge
from mongoengine import signals
from json import dumps


def handler(event):
    """Signal decorator to allow use of callback functions as
    class decorators."""

    def decorator(fn):
        def apply(cls):
            event.connect(fn, sender=cls)
            return cls

        fn.apply = apply
        return fn

    return decorator


@handler(signals.post_save)
def model_with_zeye_admin_created(sender, document, **kwargs):
    try:
        action = 'Created' if 'created' in kwargs else 'Updated'
        description = '%s %s' % (action, str(document))
        Log(
            description_event=description,
            zeye_admin_ref=document.zeye_admin_ref
        ).save()
    except mge.ValidationError:
        print("[DocumentLogger] Some validation error has occurred.")
    except Exception as e:
        print("[DocumentLogger] Some odd happened:", e)
    print("%s %s." % (str(document), action))


@handler(signals.post_save)
def model_with_deployment_created(sender, document, **kwargs):
    try:
        action = 'Created' if 'created' in kwargs else 'Updated'
        description = '%s %s' % (action, str(document))
        zeye_admin = document.deplo_ref.zeye_admin_ref
        Log(
            description_event=description,
            zeye_admin_ref=zeye_admin
        ).save()
    except mge.ValidationError:
        print("[DocumentLogger] Some validation error has occurred.")
    except Exception as e:
        print("[DocumentLogger] Some odd happened:", e)
    print("%s %s." % (str(document), action))


@handler(signals.post_save)
def model_with_zeye_manager_created(sender, document, **kwargs):
    try:
        action = 'Created' if 'created' in kwargs else 'Updated'
        description = '%s %s' % (action, str(document))
        zeye_admin = document.zeye_manager_ref.zeye_admin_ref
        Log(
            description_event=description,
            zeye_admin_ref=zeye_admin
        ).save()
    except mge.ValidationError:
        print("[DocumentLogger] Some validation error has occurred.")
    except Exception as e:
        print("[DocumentLogger] Some odd happened:", e)
    print("%s %s." % (str(document), action))


class ZeyeAdmin(mge.Document):
    email = mge.StringField(max_length=128, primary_key=True)
    names = mge.ListField(mge.StringField(
        max_length=16), required=True, max_length=4)
    surnames = mge.ListField(mge.StringField(
        max_length=16), required=True, max_length=4)
    password = mge.StringField(required=True)
    server_quantity = mge.IntField(default=5)
    clients_quantity = mge.IntField(default=5)
    registration_date = mge.DateTimeField(default=datetime.now)
    license_key = mge.StringField(
        default=str(uuid4()).replace('-', ''), unique=True)
    status = mge.BooleanField(default=True)
    profile_picture = mge.StringField(max_length=256, default='')

    @staticmethod
    def update_password(email, new_password):
        admin = ZeyeAdmin.get(email)
        if admin:
            admin.password = new_password
            admin.save()
            return True
        return False

    @staticmethod
    def get(email):
        try:
            query = ZeyeAdmin.objects.get(email=email, status=True)
            return query
        except mge.DoesNotExist:
            return None

    @staticmethod
    def delete_zeye_admin(email):
        admin = ZeyeAdmin.get(email)
        if admin:
            admin.status = False
            admin.save()
            return True
        return False

    def __eq__(self, zu):
        return self.email == zu.email

    def __str__(self):
        return 'ZeyeAdmin({email}, {license})'.format(
            email=self.email,
            license=self.license_key
        )


class UserAuth(mge.Document):
    code = mge.SequenceField('user_auth')
    email = mge.StringField(max_length=128, unique=True)
    encodings = mge.ListField()

    @staticmethod
    def get(email):
        try:
            return UserAuth.objects.get(email=email)
        except mge.DoesNotExist:
            return None

    def __eq__(self, user):
        return self.email == user.email

    def __str__(self):
        return 'UserAuth({code}, {email})'.format(
            code=self.code,
            email=self.email
        )


class UserAuthToken(mge.Document):
    code = mge.SequenceField('token')
    email = mge.StringField(max_length=128, unique=True)
    token = mge.StringField(max_length=36, default=str(uuid4()))

    def __str__(self):
        return 'UserAuthToken({email}, {token})'.format(
            email=self.email,
            token=self.token
        )

    @staticmethod
    def get(email):
        try:
            return UserAuthToken.objects.get(email=email)
        except mge.DoesNotExist:
            return None


@model_with_zeye_admin_created.apply
class ZeyeManager(mge.Document):
    email = mge.StringField(max_length=128, primary_key=True)
    names = mge.ListField(mge.StringField(max_length=16), required=True)
    surnames = mge.ListField(mge.StringField(max_length=16), required=True)
    password = mge.StringField(required=True)
    zeye_admin_ref = mge.ReferenceField(
        ZeyeAdmin, reverse_delete_rule=mge.CASCADE)
    # registration_url = mge.StringField(max_length=128)
    status = mge.BooleanField(default=True)
    profile_picture = mge.StringField(max_length=256, default='')

    @staticmethod
    def update_password(email, new_password):
        mana = ZeyeManager.get(email)
        if mana:
            mana.password = new_password
            mana.save()
            return True
        return False

    @staticmethod
    def get(email):
        try:
            query = ZeyeManager.objects.get(email=email, status=True)
            return query
        except mge.DoesNotExist:
            return None

    @staticmethod
    def delete_zeye_manager(email):
        admin = ZeyeAdmin.get(email)
        if admin:
            admin.status = False
            admin.save()
            return True
        return False

    def __eq__(self, zu):
        return self.email == zu.email

    def __str__(self):
        return 'ZeyeManager({email}, {zeye_admin})'.format(
            email=self.email,
            zeye_admin=self.zeye_admin_ref
        )


class UserSettings(mge.Document):
    email = mge.StringField(max_length=128, primary_key=True)
    profile_picture = mge.StringField(max_length=256, default='')
    deployments_quant = mge.IntField(default=10)
    cameras = mge.IntField(default=10)

    @staticmethod
    def get(email):
        try:
            query = UserSettings.objects.get(email=email)
            return query
        except mge.DoesNotExist:
            return None

    def __eq__(self, us):
        return self.email == us.email

    def __str__(self):
        return 'Settings({email}, {Deployments}, {Cameras})'.format(
            email=self.email, Deployments=self.deployments,
            Cameras=self.cameras
        )


@model_with_zeye_admin_created.apply
class DeploymentInstance(mge.Document):
    instance_types = ('Server', 'Client')

    zeye_admin_ref = mge.ReferenceField(
        ZeyeAdmin, reverse_delete_rule=mge.CASCADE)
    mb_serial = mge.StringField(unique=True, required=True)
    instance_type = mge.StringField(required=True, choices=instance_types)
    coordinate = mge.ListField(default=[0, 0])
    status = mge.BooleanField(default=True)

    @staticmethod
    def get(mb_serial):
        try:
            return DeploymentInstance.objects.get(mb_serial=mb_serial)
        except mge.DoesNotExist:
            return None

    def __eq__(self, svi):
        return self.mb_serial == svi.mb_serial

    def __str__(self):
        return "DeploymentInstance({serial}) - {instance_type}".format(
            serial=self.mb_serial, instance_type=self.instance_type)


# Share deployments with others zeye_users
class SharedDeployment(mge.Document):
    code = mge.SequenceField('code', primary_key=True)
    mb_serial = mge.StringField(max_length=128, unique=True)
    shared_users = mge.ListField(mge.StringField(), default=[])
    status = mge.BooleanField(defaul=True)

    @staticmethod
    def subscribe(user, serial):
        try:
            SharedDeployment.objects().filter(mb_serial=serial).update_one(push__shared_users=user)
            return True
        except Exception as e:
            return False

    @staticmethod
    def unsubscribe(user, serial):
        try:
            SharedDeployment.objects().filter(mb_serial=serial).update_one(pull__shared_users=user)
            return True
        except Exception as e:
            return False

    @staticmethod
    def is_subscribed(user, serial):
        try:
            shared = SharedDeployment.objects().filter(mb_serial=serial, shared_users__contains=user)
            return len(shared) > 0
        except:
            return False

    @staticmethod
    def get(serial):
        try:
            query = SharedDeployment.objects.get(mb_serial=serial)
            return query
        except mge.DoesNotExist:
            return None


@model_with_zeye_manager_created.apply
class DeploymentManager(mge.Document):
    zeye_manager_ref = mge.ReferenceField(ZeyeManager, required=True)
    deplo_ref = mge.ReferenceField(DeploymentInstance, required=True)
    id_code = mge.SequenceField('DeploymentManager')

    @staticmethod
    def delete_deployment_manager(zeye_manager, deployment):
        DeploymentManager.delete(
            zeye_manager_ref=zeye_manager,
            deplo_ref=deployment)

    def __eq__(self, deplo_manager):
        return self.id_code == deplo_manager.id_code

    def __str__(self):
        return 'DeploymentManager({code}, {manager})'.format(
            code=self.id_code,
            manager=self.zeye_manager_ref
        )


class KnownPerson(mge.Document):
    dni = mge.StringField(
        max_length=128,
        primary_key=True)
    names = mge.ListField(mge.StringField(
        max_length=256), max_length=4, required=True)
    surnames = mge.ListField(mge.StringField(
        max_length=256), max_length=4, required=True)
    email = mge.StringField(max_length=128, required=True)
    birth_date = mge.StringField(max_length=128)
    encodings = mge.ListField()
    registered_by = mge.StringField(max_length=256)
    image = mge.StringField(max_length=256)
    # deplo_ref = mge.ReferenceField(
    #     DeploymentInstance, reverse_delete_rule=mge.CASCADE)

    @staticmethod
    def getKnownPerson(dni):
        try:
            return KnownPerson.objects.get(dni=dni)
        except mge.DoesNotExist:
            return None

    def __eq__(self, known):
        return self.dni == known.dni

    def __str__(self):
        return 'KnownPerson({dni}, {names} {surnames})'.format(
            dni=self.dni,
            names=' '.join(self.names),
            surnames=' '.join(self.surnames)
        )


class UnknownPerson(mge.Document):
    code = mge.StringField(max_length=16, unique=True, required=True)
    encodings = mge.ListField()
    deplo_ref = mge.ReferenceField(
        DeploymentInstance, reverse_delete_rule=mge.CASCADE)

    @staticmethod
    def get_unknown_person(code):
        try:
            return UnknownPerson.objects.get(code=code)
        except mge.DoesNotExist:
            return None

    def __eq__(self, unknown):
        return self.code == unknown.code

    def __str__(self):
        return 'UnknownPerson({code})'.format(code=self.code)


@model_with_zeye_admin_created.apply
class InvitationZeyeManager(mge.Document):
    email = mge.StringField(max_length=128, unique=True)
    registration_url = mge.StringField(required=True)
    expiration_date = mge.DateTimeField(
        default=datetime.now() + timedelta(days=15))
    zeye_admin_ref = mge.ReferenceField(
        ZeyeAdmin, reverse_delete_rule=mge.CASCADE)

    @staticmethod
    def get_invitation(url):
        try:
            return InvitationZeyeManager.objects.get(registration_url=url)
        except mge.DoesNotExist:
            print("[InvitationZeyeManager] The document you're trying to\
                get does not exists")

    @staticmethod
    def delete_invitation(url):
        try:
            InvitationZeyeManager.objects.get(registration_url=url).delete()
        except mge.DoesNotExist:
            print("[InvitationZeyeManager] The document you're trying to\
                delete does not exists")

    def __eq__(self, invi):
        return self.email == invi.email

    def __str__(self):
        return 'InvitationZeyeManager({email})'.format(
            email=self.email
        )


@model_with_deployment_created.apply
class Camera(mge.Document):
    statuses = ('Online', 'Offline', 'Disabled')

    id_code = mge.SequenceField('Camera')
    url = mge.StringField(required=True)
    coordinate = mge.ListField(default=[0, 0])
    deplo_ref = mge.ReferenceField(DeploymentInstance, required=True)
    status = mge.StringField(default='Offline', choices=statuses)
    @staticmethod
    def get_camera(url):
        try:
            return Camera.objects.get(url=url)
        except mge.DoesNotExist:
            return None
            # print("[Camera] The document you're trying to\
            #     get does not exists")

    def __eq__(self, camera):
        return self.id_code == camera.id_code

    def __str__(self):
        return 'Camera({id_code}, {url})'.format(
            id_code=self.id_code,
            url=self.url
        )


""" class Event(mge.Document):
    id_code = mge.SequenceField('Event')
    time = mge.StringField(default=str(datetime.datetime.now()))
    id_detected = mge.StringField(max_length=16)  # DNI if Known else CODE
    
    # zone = mge.StringField(max_length=64)
    # name_video = mge.StringField(max_length=64)
    pictures = mge.ListField(required=True)
    camera_used = mge.ReferenceField(Camera, required=True)
    deplo_ref = mge.ReferenceField(
        DeploymentInstance, reverse_delete_rule=mge.CASCADE)
    status = mge.BooleanField(default=True)

    @staticmethod
    def times_detected_person(id_code):
        return Event.objects(id_code=id_code).count()

    def __eq__(self, event):
        return self.id_code == event.id_code

    def __str__(self):
        return 'Event({code}, {detected})'.format(
            code=self.id_code,
            detected=self.id_detected
        ) """


class Event(mge.Document):
    id_code = mge.SequenceField('Event')
    zeye_admin = mge.StringField(max_length=256, required=True)
    id_detected = mge.StringField(max_length=16, required=True)
    detection = mge.DictField(required=True)
    time = mge.StringField(default=str(datetime.now()))
    pictures = mge.ListField(required=True)
    camera_url = mge.StringField(required=True)
    camera_coord = mge.ListField(required=True)
    deplo_serial = mge.StringField(required=True)
    deplo_coord = mge.ListField(required=True)
    event_type = mge.StringField(max_length=256)
    detection_type = mge.StringField(max_length=256)

    @staticmethod
    def times_detected_person(id_code):
        return Event.objects(id_code=id_code).count()

    def __eq__(self, event):
        return self.id_code == event.id_code

    def __str__(self):
        return 'Event({code}, {detected})'.format(
            code=self.id_code,
            detected=self.id_detected
        )


@model_with_deployment_created.apply
class Search(mge.Document):

    id_code = mge.SequenceField('Search', primary_key=True)
    id_person = mge.StringField(max_length=16, required=True)
    name = mge.StringField(max_length=64)
    encoding = mge.ListField()
    status = mge.BooleanField(default=True)
    deplo_ref = mge.ReferenceField(
        DeploymentInstance, reverse_delete_rule=mge.CASCADE)

    def __eq__(self, search):
        return self.id_code == search.id_code

    def __str__(self):
        return 'Search({code}, {person}'.format(
            code=self.id_code, person=self.id_person)


class Log(mge.Document):

    id_code = mge.SequenceField('Search', primary_key=True)
    description_event = mge.StringField(max_length=256, required=True)
    zeye_admin_ref = mge.ReferenceField(ZeyeAdmin, required=True)
    date = mge.StringField(required=True, default=str(datetime.now()))

    def __eq__(self, log):
        return self.id_code == log.id_code

    def __str__(self):
        return 'Log({code}, {description}'.format(
            code=self.id_code,
            description=self.description_event
        )


class Subscription(mge.Document):

    id_code = mge.SequenceField('Subscription', primary_key=True)
    email = mge.StringField(max_length=256, required=True, unique=True)
    notifications = mge.ListField(default=[])
    deplo_list = mge.ListField(mge.StringField(), default=[])
    last_read = mge.IntField(default=0)

    def __eq__(self, sub):
        return self.email == sub.email

    def __str__(self):
        return 'Subscription({email}, {len_nots}, {len_deplo}, {last_read})'.format(
            email=self.email,
            len_nots=len(self.notifications),
            len_deplo=len(self.deplo_list),
            last_read=self.last_read
        )


class Setting(mge.Document):
    id_deplo = mge.StringField(unique=True, required=True)
    settings = mge.DictField(default={
        'pacman': {
            'first_run': True,
            'enabled': False,
            'streaming': {
                'status': 1,
                'resolution': {
                    'type': 'percent',
                    'value': .4
                },
                'imencode_quality': 40,
                'compress_rate': 8
            },
            'motion_detection': {
                'status': 1,
                'resolution': {
                    'type': 'percent',
                    'value': 1
                },
                'imencode_quality': 100,
                'compress_rate': 9
            }
        },

        'ai-worker': {
            'first_run': True,
            'enabled': False,
            'model': 'cnn'
        }, 

        'qai-worker': {
            'first_run': True,
            'enabled': False,
            'resolution': {
                'resize': False,
                'width': 'original',
            },
            'object_detection': {
                'enabled': False,
                'max_zoom': 25,
                'allowed_objects': {
                    'people': True,
                    'cars': False,
                    'motorbikes': False,
                    'planes': False,
                    'animals': False
                },
            },
            'face_detection': {
                'enabled': 1,
                "ray": {
                    "enabled": 0,
                    "config": {}
                },
                "type": "mtcnn",
                "config": {}
            },

            'face_recognition': {
                "enabled": 1,
                "ray": {
                    "enabled": 1,
                    "wait": 1,
                    "config": {
                        "boxes_by_task": 2
                    }
                },
                "type": "dlib",
                "register": {
                    "knowns": 1,
                    "unknowns": 1
                },
                "config": {
                    
                }
            },
            'events': {
                'grab': True,
                'images': {
                    'enabled': True,
                    'render': {
                        'face_grid': False,
                        'object_grid': False
                    }
                }
            }
        },
    })

    def __eq__(self, setting):
        return self.id_deplo == setting.id_deplo

    def __str__(self):
        return 'Setting({deplo})'.format(deplo=self.id_deplo)

    @staticmethod
    def get(mb_serial):
        try:
            conf = Setting.objects().get(id_deplo=mb_serial)
            return conf
        except mge.DoesNotExist:
            return None