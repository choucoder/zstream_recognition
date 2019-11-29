import unittest

import models
from connection import custom_connect


class TestZeyeAdmin(unittest.TestCase):

    def test_create_and_get(self):
        zadmin = models.ZeyeAdmin(
            email='test@test.com',
            names=['Test', 'Ting'],
            surnames=['Test', 'Ting'],
            password='sometestpassword',
            license_key='123456qwerty'
        )
        zadmin.save()

        query = models.ZeyeAdmin.objects.get(email='test@test.com')

        self.assertEqual(str(query), '(test@test.com, 123456qwerty)')

        query.delete()

    def test_delete(self):
        zadmin = models.ZeyeAdmin(
            email='test@test.com',
            names=['Test', 'Ting'],
            surnames=['Test', 'Ting'],
            password='sometestpassword',
            license_key='123456qwerty'
        )
        zadmin.save()

        models.ZeyeAdmin.objects.get(email='test@test.com').delete()
        self.assertEqual(
            models.ZeyeAdmin.objects(email='test@test.com').count(), 0)


class TestZeyeManager(unittest.TestCase):

    def test_create_and_get(self):
        zadmin = models.ZeyeAdmin(
            email='test@test.com',
            names=['Test', 'Ting'],
            surnames=['Test', 'Ting'],
            password='sometestpassword',
            license_key='123456qwerty'
        )
        zadmin.save()

        zmanager = models.ZeyeManager(
            email='test@man.com',
            names=['Jose', 'Test'],
            surnames=['Test', 'Test'],
            password='some silly password',
            zeye_admin_ref=zadmin
        )
        zmanager.save()

        query = models.ZeyeManager.objects.get(email='test@man.com')
        self.assertEqual(query.email, 'test@man.com')

    def test_delete(self):
        zadmin = models.ZeyeAdmin(
            email='test@test.com',
            names=['Test', 'Ting'],
            surnames=['Test', 'Ting'],
            password='sometestpassword',
            license_key='123456qwerty'
        )
        zadmin.save()

        zmanager = models.ZeyeManager(
            email='test@man.com',
            names=['Jose', 'Test'],
            surnames=['Test', 'Test'],
            password='some silly password',
            zeye_admin_ref=zadmin
        )
        zmanager.save()

        query = models.ZeyeManager.objects.get(email='test@man.com')
        query.delete()
        self.assertEqual(
            models.ZeyeManager.objects(email='test@man.com').count(), 0)


class TestDeploymentInstance(unittest.TestCase):

    def test_create_and_get(self):
        zadmin = models.ZeyeAdmin(
            email='test@test.com',
            names=['Test', 'Ting'],
            surnames=['Test', 'Ting'],
            password='sometestpassword',
            license_key='123456qwerty'
        )
        zadmin.save()

        deplo = models.DeploymentInstance(
            zeye_admin_ref=zadmin,
            mb_serial='123456qwerty',
            instance_type='Server'
        )
        deplo.save()

        self.assertEqual(
            models.DeploymentInstance.objects(
                mb_serial='123456qwerty').count(), 1)

        deplo.delete()

    def test_delete(self):
        zadmin = models.ZeyeAdmin(
            email='test@test.com',
            names=['Test', 'Ting'],
            surnames=['Test', 'Ting'],
            password='sometestpassword',
            license_key='123456qwerty'
        )
        zadmin.save()

        deplo = models.DeploymentInstance(
            zeye_admin_ref=zadmin,
            mb_serial='123456qwerty',
            instance_type='Server'
        )
        deplo.save()

        query = models.DeploymentInstance.objects.get(mb_serial='123456qwerty')
        query.delete()

        self.assertEqual(
            models.DeploymentInstance.objects(
                mb_serial='123456qwerty').count(), 0)


class TestKnownPerson(unittest.TestCase):

    def test_create_and_get(self):
        known = models.KnownPerson(
            dni='12345678',
            names=['Test', 'Ting'],
            surnames=['Testing'],
            email='test@test.com',
        )
        known.save()

        self.assertEqual(
            models.KnownPerson.objects(dni='12345678').count(), 1
        )

        known.delete()

    def test_delete(self):
        known = models.KnownPerson(
            dni='12345678',
            names=['Test', 'Ting'],
            surnames=['Testing'],
            email='test@test.com',
        )
        known.save()

        query = models.KnownPerson.objects.get(dni='12345678')
        query.delete()

        self.assertEqual(
            models.KnownPerson.objects(dni='12345678').count(), 0
        )


class TestUnknownPerson(unittest.TestCase):

    def test_create_and_get(self):
        unknown = models.UnknownPerson(
            code='12qw34er56ty'
        )
        unknown.save()

        self.assertEqual(
            models.UnknownPerson.objects(code='12qw34er56ty').count(), 1
        )

        unknown.delete()

    def test_delete(self):
        unknown = models.UnknownPerson(
            code='12qw34er56ty'
        )
        unknown.save()

        query = models.UnknownPerson.objects.get(code='12qw34er56ty')
        query.delete()

        self.assertEqual(
            models.UnknownPerson.objects(code='12qw34er56ty').count(), 0
        )


class TestInvitationZeyeManager(unittest.TestCase):

    def test_create_and_get(self):
        zadmin = models.ZeyeAdmin(
            email='test@test.com',
            names=['Test', 'Ting'],
            surnames=['Test', 'Ting'],
            password='sometestpassword',
            license_key='123456qwerty'
        )
        zadmin.save()

        invitation = models.InvitationZeyeManager(
            email='test2@test.com',
            registration_url='lalala.com/signup',
            zeye_admin_ref=zadmin
        )
        invitation.save()

        self.assertEqual(
            models.InvitationZeyeManager.objects(
                email='test2@test.com').count(), 1
        )

        zadmin.delete()
        invitation.delete()

        self.assertEqual(
            models.InvitationZeyeManager.objects(
                email='test2@test.com').count(), 0
        )


if __name__ == '__main__':
    custom_connect()
    unittest.main()
