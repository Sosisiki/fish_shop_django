import os
import requests
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files import File
from products.models import Product

# 🔹 НАДЁЖНЫЕ ССЫЛКИ (Unsplash - работают всегда)
# Используем прямые ссылки на качественные фото

PRODUCT_IMAGES = {
    # 🐠 РЫБКИ
    "Гуппи Эндлера": "https://images.unsplash.com/photo-1535591273668-578e619f2cfb?w=400&h=400&fit=crop",
    "Неон Голубой": "https://images.unsplash.com/photo-1522069169874-c58ec4b76be5?w=400&h=400&fit=crop",
    "Скалярия Императорская": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop",
    "Петушок Сиамский": "https://images.unsplash.com/photo-1534043464124-85095614f5b4?w=400&h=400&fit=crop",
    "Данио Рерио": "https://images.unsplash.com/photo-1524704654690-b56c05c76be5?w=400&h=400&fit=crop",
    "Меченосец Зелёный": "https://images.unsplash.com/photo-1535591273668-578e619f2cfb?w=400&h=400&fit=crop",
    "Барбус Суматранский": "https://images.unsplash.com/photo-1524704654690-b56c05c76be5?w=400&h=400&fit=crop",
    "Тернеция Чёрная": "https://images.unsplash.com/photo-1522069169874-c58ec4b76be5?w=400&h=400&fit=crop",
    "Лабео Двухцветный": "https://images.unsplash.com/photo-1535591273668-46a013bb70d5?w=400&h=400&fit=crop",
    "Акара Голубая": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop",
    "Апистограмма Рамирези": "https://images.unsplash.com/photo-1534043464124-85095614f5b4?w=400&h=400&fit=crop",
    "Коридорас Крапчатый": "https://images.unsplash.com/photo-1524704654690-b56c05c76be5?w=400&h=400&fit=crop",
    "Анциструс Обыкновенный": "https://images.unsplash.com/photo-1522069169874-c58ec4b76be5?w=400&h=400&fit=crop",
    "Моллинезия Чёрная": "https://images.unsplash.com/photo-1535591273668-46a013bb70d5?w=400&h=400&fit=crop",
    "Дискус Красный": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop",
    
    # 🐟 АКВАРИУМЫ
    "Nano Cube 20л": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Panorama 50л": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "Tetra AquaArt 60л": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Juwel Rio 125л": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "Dennerle Scapers 30л": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "AquaEl Glossy 40л": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "Ferplast Club 70л": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "BiOrb Life 30л": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "Tetra Clear 80л": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Juwel Vision 180л": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "AquaOptima 25л": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Dennerle Nano 10л": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "Ferplast Dubai 100л": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Juwel Lido 120л": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "Tetra AquaArt 30л": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    
    # 🔧 АКСЕССУАРЫ
    "Фильтр Tetra TetraTec 300": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop",
    "Компрессор Hailea ACO-009": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Терморегулятор Xilong 50Вт": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "LED-светильник Nicrew Classic": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Грунт Tetra ActiveSubstrate 5кг": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop",
    "Декорация Коряга Натуральная": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "Сифон для грунта Aquael": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Сачок нейлоновый 15см": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop",
    "Тест воды Tetra 6-в-1": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "Фон самоклеящийся 3D": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Распылитель воздуха керамический": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop",
    "Крышка с LED подсветкой 60см": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "Грот керамический 'Пещера'": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Автоматическая кормушка": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop",
    "УФ-стерилизатор AquaPro 9Вт": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    
    # 🍽 КОРМА
    "TetraMin Хлопья 100мл": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop",
    "Sera Goldy Gran 100мл": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "TetraPro Colour 100мл": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "Sera Vipagran 250мл": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop",
    "JBL NovoGranoColor 100мл": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Tetra Phyll 250мл": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "Sera Flora 100мл": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop",
    "JBL NovoTab 30шт": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Tetra WaferMix 100мл": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "Sera Crabs Natural 100мл": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop",
    "JBL ProScan Тест + Корм": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Tetra Rubin 100мл": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
    "Sera Pond Staple 1л": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop",
    "JBL NovoBel 250мл": "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400&h=400&fit=crop",
    "Tetra FreshDelica Мотыль": "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400&h=400&fit=crop",
}


class Command(BaseCommand):
    help = "Загрузка изображений для ВСЕХ товаров (перезаписывает существующие)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Перезаписать существующие изображения'
        )

    def handle(self, *args, **options):
        force = options['force']
        success_count = 0
        error_count = 0
        skip_count = 0
        
        self.stdout.write(self.style.SUCCESS('\n🐟 ЗАГРУЗКА ИЗОБРАЖЕНИЙ ДЛЯ ВСЕХ ТОВАРОВ\n'))
        
        # Получаем ВСЕ товары из базы
        all_products = Product.objects.all()
        self.stdout.write(f'📦 Найдено товаров в базе: {all_products.count()}\n')
        
        for product in all_products:
            try:
                # Ищем подходящее изображение по названию
                image_url = None
                
                # Точное совпадение
                if product.name in PRODUCT_IMAGES:
                    image_url = PRODUCT_IMAGES[product.name]
                else:
                    # Ищем по ключевым словам
                    for key, url in PRODUCT_IMAGES.items():
                        if key.lower() in product.name.lower() or product.name.lower() in key.lower():
                            image_url = url
                            break
                
                if not image_url:
                    # Если не нашли - используем случайное изображение аквариума
                    fallback_images = [
                        "https://images.unsplash.com/photo-1527011046414-4781f1f94f8c?w=400",
                        "https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=400",
                        "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
                    ]
                    image_url = fallback_images[product.id % 3]
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  "{product.name}" - используем универсальное фото')
                    )
                
                # Проверяем, есть ли уже изображение
                if product.image and not force:
                    self.stdout.write(
                        self.style.WARNING(f'⏭️  "{product.name}" - уже есть изображение (используйте --force для замены)')
                    )
                    skip_count += 1
                    continue
                
                # Скачиваем изображение
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(image_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                # Создаём файл
                image_file = File(BytesIO(response.content))
                filename = f"product_{product.id}.jpg"
                
                # Удаляем старое изображение если есть
                if product.image:
                    product.image.delete(save=False)
                
                # Сохраняем новое
                product.image.save(filename, image_file, save=True)
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ "{product.name}"')
                )
                success_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ "{product.name}": {str(e)[:60]}')
                )
                error_count += 1
        
        # Итоговый отчёт
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('📊 ИТОГИ ЗАГРУЗКИ:'))
        self.stdout.write(f'   ✅ Загружено: {success_count}')
        self.stdout.write(f'   ❌ Ошибки: {error_count}')
        self.stdout.write(f'   ⏭️  Пропущено: {skip_count}')
        self.stdout.write('='*70)
        
        if success_count > 0:
            self.stdout.write(self.style.SUCCESS('\n🎉 Готово! Все товары получили изображения!'))