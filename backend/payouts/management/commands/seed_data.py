"""
Seed script: python manage.py seed_data

Creates 3 merchants with realistic credit history.
Run this once after migrations.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from payouts.models import Merchant, LedgerEntry, Payout


MERCHANTS = [
    {
        'name': 'TechFlow Agency',
        'email': 'billing@techflow.io',
        'credits': [
            (250_000_00, 'Client payment — Accenture project Q1'),
            (180_000_00, 'Client payment — Infosys design contract'),
            (95_000_00,  'Client payment — Startup MVP sprint'),
            (320_000_00, 'Client payment — HDFC Bank dashboard'),
            (140_000_00, 'Client payment — Zepto growth retainer'),
        ],
    },
    {
        'name': 'DesignCraft Studio',
        'email': 'accounts@designcraft.in',
        'credits': [
            (120_000_00, 'Branding project — FinTech client'),
            (85_000_00,  'UI/UX contract — EdTech platform'),
            (200_000_00, 'Product design — SaaS company USA'),
        ],
    },
    {
        'name': 'CodeBridge Solutions',
        'email': 'finance@codebridge.dev',
        'credits': [
            (500_000_00, 'Engineering retainer — US startup'),
            (280_000_00, 'Backend project — logistics company'),
            (175_000_00, 'API integration — payments client'),
            (420_000_00, 'Full-stack contract — e-commerce'),
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed merchants and ledger data for demo purposes'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data…')

        for m_data in MERCHANTS:
            with transaction.atomic():
                merchant, created = Merchant.objects.get_or_create(
                    email=m_data['email'],
                    defaults={'name': m_data['name']},
                )
                if created:
                    self.stdout.write(f'  Created merchant: {merchant.name}')
                else:
                    self.stdout.write(f'  Merchant already exists: {merchant.name}')
                    continue  # skip seeding entries if already exists

                for amount, desc in m_data['credits']:
                    LedgerEntry.objects.create(
                        merchant=merchant,
                        entry_type=LedgerEntry.EntryType.CREDIT,
                        amount_paise=amount,
                        description=desc,
                    )

                self.stdout.write(f'    ✓ {len(m_data["credits"])} credit entries added')

        self.stdout.write(self.style.SUCCESS('\nSeed complete. Run the dev server and open the dashboard.'))
