document.addEventListener('DOMContentLoaded', function() {
    // ========== АВТО-СКРЫТИЕ АЛЕРТОВ ==========
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // ========== КНОПКА "НАВЕРХ" ==========
    const backToTopBtn = document.getElementById('backToTop');
    if (backToTopBtn) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
            }
        }, { passive: true });
        
        backToTopBtn.addEventListener('click', e => {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ========== МОБИЛЬНОЕ МЕНЮ: АВТО-ЗАКРЫТИЕ ==========
    const mobileMenu = document.getElementById('mobileMenu');
    if (mobileMenu) {
        mobileMenu.querySelectorAll('.nav-item, .btn-logout').forEach(link => {
            link.addEventListener('click', () => {
                const bs = bootstrap.Collapse.getInstance(mobileMenu);
                if (bs) bs.hide();
            });
        });
    }

    // ========== ОБНОВЛЕНИЕ БЕЙДЖА КОРЗИНЫ (ГЛОБАЛЬНО) ==========
    window.updateCartBadge = function(count) {
        const badges = document.querySelectorAll('#cartBadge');
        badges.forEach(badge => {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        });
        // Сохраняем в localStorage для синхронизации между страницами
        localStorage.setItem('cart_count', count);
    };

    // Инициализация бейджа при загрузке страницы
    const savedCount = localStorage.getItem('cart_count');
    if (savedCount && window.updateCartBadge) {
        window.updateCartBadge(parseInt(savedCount));
    }

    // ========== БЛОКИРОВКА ДУБЛИРОВАНИЯ ФОРМ ==========
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const btn = this.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Обработка...';
            }
        });
    });

    // ========== ГОРЯЧИЕ КЛАВИШИ ==========
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.show').forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            });
        }
    });

    // ========== СКРЫТИЕ ПРЕЛОАДЕРА ==========
    window.addEventListener('load', () => {
        const preloader = document.getElementById('preloader');
        if (preloader) {
            setTimeout(() => {
                preloader.classList.add('hidden');
                setTimeout(() => preloader.remove(), 400);
            }, 300);
        }
    });
});

// ========== ГЛОБАЛЬНЫЕ УТИЛИТЫ ==========

// Форматирование цены
window.formatPrice = function(p) {
    return new Intl.NumberFormat('ru-RU', { 
        style: 'currency', 
        currency: 'RUB', 
        minimumFractionDigits: 0 
    }).format(p);
};

// Валидация телефона
window.validatePhone = function(p) {
    return /^(\+7|8)\d{10}$/.test(p.replace(/[\s\-\(\)]/g, ''));
};

// Debounce для оптимизации событий
window.debounce = function(fn, wait) { 
    let t; 
    return (...args) => { 
        clearTimeout(t); 
        t = setTimeout(() => fn(...args), wait); 
    }; 
};

// Получение CSRF токена для AJAX-запросов
window.getCSRFToken = function() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

// Универсальная функция для добавления в корзину (используется на всех страницах)
window.addToCartUniversal = function(productId, productName, maxStock, qtyInputId) {
    const qtyInput = document.getElementById(qtyInputId || `qty-${productId}`);
    let qty = qtyInput ? (parseInt(qtyInput.value) || 1) : 1;
    
    if (qty > maxStock) qty = maxStock;
    if (qty < 1) qty = 1;

    fetch(`/orders/cart/add/${productId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.getCSRFToken()
        },
        body: JSON.stringify({ quantity: qty })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            // 🔹 Обновляем бейдж корзины глобально
            if (window.updateCartBadge) {
                window.updateCartBadge(data.total_items);
            }
            // 🔹 Сбрасываем количество
            if (qtyInput) qtyInput.value = 1;
            // 🔹 Показываем остаток
            const remaining = data.remaining_stock;
            if (remaining !== undefined) {
                alert(`✅ "${productName}" (×${qty}) добавлен!\n📦 Осталось на складе: ${remaining} шт.`);
            } else {
                alert(`✅ "${productName}" (×${qty}) добавлен в корзину!`);
            }
        } else {
            alert('❌ ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при добавлении в корзину');
    });
};