from django.db import models
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db.models.expressions import F

class UsernameField(models.CharField):
    """
    Provides easy denormalisation of User.username onto a model.

    By default, ``UsernameField`` will assume you wish to denormalise
    ``instance.user.username``::

        class Post(models.Model):
            user = models.ForeignKey(User)
            username = UsernameField()

    If the source is elsewhere, you can specify it with ``populate_from``::

        class Thread(models.Model):
            last_post = models.ForeignKey(User)
            last_post_username = UsernameField(populate_from='last_post')

    The ``max_length`` kwarg behaves a little differently to a regular
    ``CharField`` in that the username is silently truncated to that length.
    This is by design to support denormalisation of the first letter.
    """

    instances = []

    def __init__(self, *args, **kwargs):
        self.populate_from = kwargs.pop('populate_from', 'user')

        kwargs['max_length'] = kwargs.pop('max_length', 30)

        super(UsernameField, self).__init__(*args, **kwargs)

    def pre_save(self, obj, add):
        if getattr(obj, self.name) == '':
            try:
                user = getattr(obj, self.populate_from)

                # Support nullable fields.
                if user is None:
                    setattr(obj, self.name, '')
                else:
                    setattr(obj, self.name, user.username[:self.max_length])
            except ObjectDoesNotExist:
                pass

        return getattr(obj, self.name)

    def contribute_to_class(self, cls, name):
        if not cls._meta.abstract:
            self.instances.append(
                (cls, self.populate_from, name, self.max_length)
            )

        super(UsernameField, self).contribute_to_class(cls, name)

    @classmethod
    def rename_username(cls, user_id, username):
        """
        Renames all denormalised User.username instances (that use
        ``UsernameField``).
        """

        for model, source, target, max_length in cls.instances:
            model.objects.filter(**{source: user_id}).update(**{
                target: username[:max_length],
            })

        User.objects.filter(pk=user_id).update(username=username)

    @classmethod
    def lint(cls):
        for model, source, target, max_length in cls.instances:
            if max_length < 30:
                print "I: Not checking %s.%s as field can truncate data" % \
                    (model, target)
                continue

            qs = model.objects.exclude(**{
                '%s__username' % source: F(target),
            }).values_list('pk', flat=True)

            if not qs.exists():
                continue

            print "W: %d %s.%s instance(s) have invalid usernames: %r" % \
                (len(qs), model, target, qs)
