# Generated migration for adding status field to Product model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='status',
            field=models.CharField(
                choices=[('draft', 'Draft'), ('published', 'Published')],
                default='draft',
                max_length=20
            ),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['status'], name='products_status_idx'),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name='products',
                to='products.category'
            ),
        ),
    ]
