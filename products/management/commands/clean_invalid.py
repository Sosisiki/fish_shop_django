from django.core.management.base import BaseCommand
from products.models import Product

# ✅ Допустимые категории (только эти товары останутся)
VALID_CATEGORIES = {'fish', 'aquarium', 'accessory', 'food'}


class Command(BaseCommand):
    help = "Удаление товаров с невалидной категорией (прочерк '-' или пустое значение)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, что будет удалено, без фактического удаления'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Подтвердить удаление без дополнительного запроса'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        # Находим все товары с невалидной категорией
        invalid_products = Product.objects.exclude(
            category__in=VALID_CATEGORIES
        )
        
        if not invalid_products.exists():
            self.stdout.write(
                self.style.SUCCESS('✅ Все товары имеют валидные категории. Нечего удалять.')
            )
            return
        
        self.stdout.write(self.style.WARNING(f'\n⚠️  НАЙДЕНО ТОВАРОВ ДЛЯ УДАЛЕНИЯ: {invalid_products.count()}\n'))
        
        # Выводим список товаров
        for product in invalid_products:
            category_display = product.get_category_display() if product.category else '—'
            self.stdout.write(
                f'   ❌ "{product.name}" — категория: {category_display} (цена: {product.price}₽)'
            )
        
        # Если dry-run — останавливаемся
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n🔍 РЕЖИМ ПРОСМОТРА: ничего не удалено.\n'
                                 'Запустите без --dry-run для фактического удаления.')
            )
            return
        
        # Запрос подтверждения (если не --force)
        if not force:
            confirm = input(
                self.style.WARNING(
                    f'\n❗ Вы уверены, что хотите удалить {invalid_products.count()} товаров? (yes/no): '
                )
            )
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.SUCCESS('✅ Отменено. Товары не удалены.'))
                return
        
        # Удаляем
        deleted_count, _ = invalid_products.delete()
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('🗑️  УДАЛЕНИЕ ЗАВЕРШЕНО'))
        self.stdout.write(f'   📦 Удалено товаров: {deleted_count}')
        self.stdout.write(f'   ✅ Осталось товаров: {Product.objects.count()}')
        self.stdout.write('='*70)
        
        # Показываем, что осталось
        self.stdout.write(self.style.SUCCESS('\n📋 ОСТАВШИЕСЯ ТОВАРЫ ПО КАТЕГОРИЯМ:'))
        for category_key, category_name in Product.CATEGORY_CHOICES:
            count = Product.objects.filter(category=category_key).count()
            emoji = {'fish': '🐠', 'aquarium': '🐟', 'accessory': '🔧', 'food': '🍽'}.get(category_key, '📦')
            self.stdout.write(f'   {emoji} {category_name}: {count} шт.')