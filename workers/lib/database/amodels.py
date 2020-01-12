from datetime import datetime
import mongoengine as mge

class KnownPerson(mge.Document):
    
    dni = mge.StringField(max_length=16, primary_key=True)
    names = mge.ListField(mge.StringField(max_length=16), max_length=4, required=True)
    surnames = mge.ListField(mge.StringField(max_length=16), max_length=4, required=True)
    email = mge.StringField(max_length=128, required=True)
    lastUpdate = mge.DateTimeField(default=datetime.today().date())
    encodings = mge.ListField()
    birth_date = mge.StringField()
    registered_by = mge.StringField()
    image = mge.StringField()

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
    lastUpdate = mge.DateTimeField(default=datetime.today().date())

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
