import uuid
from django.db import migrations, models


def set_unique_tokens(apps, schema_editor):
    User = apps.get_model('users', 'User')
    for user in User.objects.all():
        user.verification_token = uuid.uuid4()
        user.save(update_fields=['verification_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_managers'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='verification_token',
            field=models.UUIDField(default=uuid.uuid4, unique=False),
        ),
        migrations.RunPython(set_unique_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='verification_token',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]
