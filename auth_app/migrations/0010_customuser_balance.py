# Generated by Django 4.2.5 on 2023-10-11 11:31

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth_app", "0009_orderitem_seller"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="balance",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0.00"), max_digits=10
            ),
        ),
    ]
